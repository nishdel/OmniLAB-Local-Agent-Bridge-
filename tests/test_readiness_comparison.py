"""Model-free energy/accounting, fixture acceptance and harness boundaries."""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys

import pytest

from localagentbridge.comparison import PHASES, empty_attempt, energy, report, validate_attempt, next_step
from localagentbridge.comparison_telemetry import laptop_power, sample, summarize

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from comparison_fixtures import FIXTURES
from benchmark_readiness import prepare, mock, verify, sha
from localagentbridge.task_contract import digest


def power(t, watts=100, **kw):
    return dict(timestamp=t, monotonic_seconds=t, units='W', source='synthetic',
                domain='gpu_board', device='test-gpu', watts=watts, generation=1) | kw


def test_energy_integrates_wh_and_clips_boundaries_without_extrapolation():
    value = energy([power(0,0), power(10,200)], 2, 8, max_gap_seconds=10, idle_watts=120)
    assert value['gross_observed_wh'] == pytest.approx(100*6/3600)
    assert value['coverage_ratio'] == 1
    assert value['idle_subtracted_estimate_wh'] < 0  # Never clamp a negative estimate.
    partial = energy([power(2), power(4)], 0, 10)
    assert partial['coverage_ratio'] == .2 and partial['uncovered_seconds'] == 8
    assert not partial['complete']


@pytest.mark.parametrize('rows,reason', [
    ([power(0),power(10)], 'sampling_gap'),
    ([power(0),power(2,None)], 'unavailable_power'),
    ([power(0),power(2,generation=2)], 'sensor_restart'),
    ([power(0),power(2,monotonic_seconds=0)], 'clock_discontinuity_or_suspend')])
def test_unknown_power_and_gaps_remain_unknown(rows, reason):
    value = energy(rows, 0, 10)
    assert value['gross_observed_wh'] is None and value['covered_seconds'] == 0
    assert value['gaps'][0]['reason'] == reason
    assert energy([],0,10)['gross_observed_wh'] is None


def test_power_zero_duplicates_conflicts_and_mixed_boundaries():
    assert energy([power(0,0),power(2,0),power(2,0)],0,2)['gross_observed_wh'] == 0
    for rows in ([power(0),power(0,1)], [power(0),power(2,domain='whole_system')],
                 [power(0,units='mW')], [power(0,float('nan'))], [power(0,True)]):
        with pytest.raises(ValueError):
            energy(rows,0,10)


def attempt(arm='A', outcome='accepted_first_pass', n=1):
    row = empty_attempt(arm=arm, fixture='fix', trial=1, attempt=n,
                        candidate='a'*40, settings_sha256=arm*64, fixture_sha256='f'*64)
    row.update(mode='live', outcome=outcome, accounting_run_id=arm, lane='local_implementation',
               admission={'status':'admitted','reason':'synthetic test declaration'},
               independent_checks=[{'passed':True,'evidence':'synthetic check'}], regressions=[],
               review={'independent':True,'evidence':'synthetic independent review','candidate_sha256':'c'*64},
               cloud_coverage={p:'observed' for p in PHASES}, usage_report_sha256='u'*64)
    if outcome in ('failed','rejected','blocked'):
        row['failure_class']='synthetic_failure'
    return row


def receipt(arm, total, **extra):
    return dict(id=arm, source='rollout', attribution={'run_id':arm}, category='evaluation',
                input_tokens=total-20 if total is not None else None, cached_input_tokens=10,
                output_tokens=20, reasoning_output_tokens=5, total_tokens=total) | extra


def test_cloud_savings_complete_equivalent_accepted_only_preserves_negative():
    rows=[attempt('A'),attempt('B')]
    usage={'records':[receipt('A',100),receipt('B',120)]}
    result=report(rows,usage,equivalence_evidence='Same frozen task and supervisor settings, all work included')
    assert result['comparisons'][0]['net_cloud_tokens_avoided']==-20
    assert result['tasks'][0]['cloud']['tokens']['total_tokens']['total']==100
    assert report(rows,{'investment':usage},equivalence_evidence='same')['comparisons'][0]['net_cloud_tokens_avoided']==-20
    for change in ('mock','unknown_phase','no_acceptance','missing_counter'):
        modified=deepcopy(rows); u=deepcopy(usage)
        if change=='mock': modified[1]['mode']='mock'
        if change=='unknown_phase': modified[1]['cloud_coverage']['planning']='unknown'
        if change=='no_acceptance': modified[1].update(outcome='rejected',failure_class='quality')
        if change=='missing_counter': u['records'][1]['total_tokens']=None
        assert report(modified,u,equivalence_evidence='test')['comparisons'][0]['net_cloud_tokens_avoided'] is None
    assert report(rows,usage)['comparisons'][0]['net_cloud_tokens_avoided'] is None


def test_failure_energy_included_per_accepted_task_and_unknown_attempt_poison():
    failed=attempt('B','failed'); accepted=attempt('B','accepted_after_local_retry',2)
    failed['energy']=[energy([power(0),power(2)],0,2)]
    accepted['energy']=[energy([power(3),power(5)],3,5)]
    data=report([failed,accepted],{'records':[]})
    assert data['energy_per_accepted_task'][0]['wh_per_accepted_task']==pytest.approx(400/3600)
    another=attempt('B','failed'); another.update(fixture='another',accounting_run_id='another')
    another['energy']=[energy([power(6),power(8)],6,8)]
    data=report([failed,accepted,another],{'records':[]})
    assert data['energy_per_accepted_task'][0]['wh_per_accepted_task']==pytest.approx(600/3600)
    failed['energy']=[]
    assert report([failed,accepted],{'records':[]})['energy_per_accepted_task'][0]['wh_per_accepted_task'] is None


def test_accounting_rejects_missing_attempts_duplicates_and_false_acceptance():
    row=attempt()
    for rows in ([row,row], [attempt(n=2)]):
        with pytest.raises(ValueError): report(rows,{'records':[]})
    with pytest.raises(ValueError,match='Duplicate selected'):
        report([row],{'records':[receipt('A',100),receipt('A',100)]})
    bad=deepcopy(row);bad['independent_checks']=[]
    with pytest.raises(ValueError,match='independent'): validate_attempt(bad)
    blocked = report([attempt('D','blocked')],{'records':[]})['tasks'][0]
    assert blocked['accepted'] is False and blocked['first_pass_accepted'] is None
    assert not blocked['quality_evaluated']


def test_existing_power_export_never_uses_estimates_or_assumes_cpu(tmp_path):
    path=tmp_path/'status.json'
    path.write_text(json.dumps(dict(timestamp=100,estimated_total=999,subtotal=42,components={
        'cpu':{'kind':'cpu','provider':'test','error':'unavailable'},
        'gpu':{'kind':'egpu','provider':'nvml','watts':100,'generation':9}})))
    values=laptop_power(path,now=102)
    assert values[0]['watts'] is None and values[1]['watts']==100
    assert values[1]['generation'] is None
    with pytest.raises(ValueError,match='stale'): laptop_power(path,now=126)


def test_readonly_gpu_query_and_unsupported_power():
    calls=[]
    def run(argv,**kwargs):
        calls.append(argv)
        return subprocess.CompletedProcess(argv,0,'mock-gpu, 300, [N/A]\n','')
    value=sample(run=run)
    assert calls==[['nvidia-smi','--query-gpu=uuid,memory.used,power.draw','--format=csv,noheader,nounits']]
    assert value['power'][0]['watts'] is None and value['resources']['gpu_used_mib']==300
    assert not value['cpu_probe_started'] and value['whole_system_wall_watts'] is None


def test_resource_aggregation_and_counter_reset():
    def row(t,read):
        return dict(resources=dict(timestamp=t,host_used_bytes=100+t,available_ram_bytes=200-t,
                    gpu_used_mib=30,disk_read_bytes=read,disk_write_bytes=t),power=[power(t)],error=None)
    value=summarize([row(0,100),row(2,120)],0,2)
    assert value['resources']['minimum_available_ram_bytes']==198
    assert value['resources']['disk_read_bytes']==20
    assert value['energy'][0]['complete']
    assert summarize([row(0,100),row(2,20)],0,2)['resources']['disk_read_bytes'] is None


def test_next_step_budget_and_missing_accounting_halt():
    plan=json.loads((Path(__file__).resolve().parents[1]/'examples/comparison-plan.json').read_text())
    manifest={'plan':plan,'candidate_commit':'a'*40,'cases':[
        dict(key='one',arm='A',fixture='source_explanation',trial=1,
             settings_sha256='A'*64,fixture_sha256='f'*64)]}
    assert next_step(manifest,[],{'records':[]},elapsed_seconds=0,evidence_bytes=0)['status']=='proposed'
    assert next_step(manifest,[],{'records':[]},elapsed_seconds=64800,evidence_bytes=0)['status']=='halt'
    row=attempt();row['fixture']='source_explanation'
    assert next_step(manifest,[row],{'records':[]},elapsed_seconds=100,evidence_bytes=1)['status']=='halt'
    row['candidate']='changed'
    with pytest.raises(ValueError,match='frozen'):next_step(manifest,[row],{'records':[]},elapsed_seconds=1,evidence_bytes=1)
    row['candidate']='a'*40
    row['arm']='D'
    with pytest.raises(ValueError):next_step(manifest,[row],{'records':[]},elapsed_seconds=1,evidence_bytes=1)


def test_unknown_cpu_does_not_block_declared_board_energy_queue():
    plan=json.loads((Path(__file__).resolve().parents[1]/'examples/comparison-plan.json').read_text())
    row=attempt();row.update(fixture='source_explanation',end_to_end_seconds=2)
    row['energy']=[energy([power(0),power(2)],0,2),
                   energy([power(0,None,domain='cpu_package',device='cpu'),
                           power(2,None,domain='cpu_package',device='cpu')],0,2)]
    manifest={'plan':plan,'candidate_commit':'a'*40,'cases':[
        dict(key='one',arm='A',fixture='source_explanation',trial=1,
             settings_sha256='A'*64,fixture_sha256='f'*64)]}
    assert next_step(manifest,[row],{'records':[receipt('A',100)]},elapsed_seconds=2,evidence_bytes=1)['status']=='complete'


# Controls for evaluator testing only. Never supplied to generation in a trial.
CONTROLS = {
 'source_explanation': {'answer.json': json.dumps(dict(summary='The function returns None for missing or expired entries and preserves a cached zero value.',
    expiry_comparison='>=', expired_result=None,missing_result=None,zero_is_cached=True,source_lines=[2,5,7]))},
 'defect_review': {'answer.json':json.dumps({'findings':[
    {'line':4,'explanation':'Truth testing incorrectly drops valid zero readings','input':[[1,0]],'expected':[[1,0]]},
    {'line':5,'explanation':'Timestamp dictionary assignment overwrites earlier equal timestamp readings',
     'input':[[1,2],[1,3]],'expected':[[1,2],[1,3]]}]})},
 'regression_tests': {'test_subject.py':'''import unittest
from subject import lease_active
class Tests(unittest.TestCase):
    def test_start(self): self.assertTrue(lease_active(5,5,3))
    def test_middle(self): self.assertTrue(lease_active(6,5,3))
    def test_expiry(self): self.assertFalse(lease_active(8,5,3))
    def test_before(self): self.assertFalse(lease_active(4,5,3))
    def test_zero(self): self.assertFalse(lease_active(5,5,0))
    def test_negative(self):
        with self.assertRaises(ValueError): lease_active(5,5,-1)
'''},
 'bounded_fix': {'subject.py':'''def bucket_counts(times, edges):
    if len(edges)<2 or any(a>=b for a,b in zip(edges,edges[1:])):
        raise ValueError('edges')
    return [sum(a<=t<b for t in times) for a,b in zip(edges,edges[1:])]
'''},
 'multifile_refactor': {'labels.py':"def normalize(value):\n    return (value or '').strip().lower() or 'unknown'\n",
    'exporter.py':'import labels\ndef row_label(value):\n    return labels.normalize(value)\n',
    'summary.py':'import labels\ndef group_label(value):\n    return labels.normalize(value)\n'},
 'structured_logs': {'answer.json':json.dumps(dict(attempts_by_state={'failed':1,'accepted':1,'blocked':1,'rejected':1},
    accepted_tasks=1,known_generation_ms=120,total_generation_ms=None,missing_duration_attempts=1,evidence_event_ids=['e1','e2','e3','e4']))}
}


@pytest.mark.parametrize('fixture',FIXTURES,ids=lambda f:f['id'])
def test_authorities_reject_baseline_and_accept_independent_controls(tmp_path,fixture):
    for name,content in fixture['files'].items(): (tmp_path/name).write_text(content,encoding='utf-8')
    (tmp_path/'acceptance.py').write_text(fixture['authority'],encoding='utf-8')
    def check():
        return subprocess.run([sys.executable,'-B','acceptance.py'],cwd=tmp_path,capture_output=True,text=True,timeout=15)
    assert check().returncode != 0
    for name,content in CONTROLS[fixture['id']].items(): (tmp_path/name).write_text(content,encoding='utf-8')
    result=check()
    assert result.returncode==0, result.stderr
    if fixture['id']=='regression_tests':
        assert 'all four behavior mutants killed' in result.stdout
        (tmp_path/'test_subject.py').write_text('import unittest\nclass T(unittest.TestCase):\n    def test_ok(self): pass\n')
        assert check().returncode != 0


def test_preparation_and_real_harness_with_mock_only_transports(tmp_path):
    manifest=prepare(tmp_path/'prepared')
    assert len(manifest['cases'])==48 and not manifest['live_authorized']
    assert sum(c['status']=='blocked' for c in manifest['cases'])==12
    for case in manifest['cases']:
        if case['arm']!='A':
            c=json.loads((Path(case['directory'])/'contract.json').read_text())[0]
            assert not c['supervisor_approved']
    result=mock(tmp_path/'prepared/manifest.json',tmp_path/'mock')
    assert result['mock_safety']['model_inference'] is False
    assert result['mock_safety']['rows']==48
    assert all(c['status']=='not established' for c in result['comparisons'])
    assert len(verify(tmp_path/'prepared/manifest.json')['cases'])==48
    # Bind a synthetic installed tree and prove package bytes are checked too.
    wheel=tmp_path/'synthetic.whl';wheel.write_bytes(b'synthetic package for hash test')
    runtime=tmp_path/'runtime';runtime.mkdir();(runtime/'module.py').write_text('synthetic')
    hashes={'module.py':sha(runtime/'module.py')}
    package=tmp_path/'package.json'
    package.write_text(json.dumps(dict(source_sha256=manifest['source_sha256'],wheel=str(wheel),
        wheel_sha256=sha(wheel),runtime_root=str(runtime),runtime_sha256=hashes)))
    manifest['package_identity']=dict(path=str(package),sha256=sha(package),
        wheel_sha256=sha(wheel),runtime_tree_sha256=digest(hashes))
    bound=tmp_path/'bound.json';bound.write_text(json.dumps(manifest))
    assert verify(bound)['package_identity']
    (runtime/'module.py').write_text('changed')
    with pytest.raises(ValueError,match='runtime changed'):verify(bound)
    (runtime/'module.py').write_text('synthetic')
    wheel.write_bytes(b'changed')
    with pytest.raises(ValueError,match='source/wheel/runtime'):verify(bound)
    target=Path(manifest['cases'][0]['repository'])/'acceptance.py'
    target.write_text('print("forged")')
    with pytest.raises(ValueError,match='Frozen fixture'): verify(tmp_path/'prepared/manifest.json')
