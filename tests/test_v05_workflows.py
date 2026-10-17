import asyncio
from dataclasses import replace
import json
import time

import httpx
import pytest

from localagentbridge.bridge import BridgeError
from localagentbridge.catalog import AgenticConfig, Limits, Requirements
from localagentbridge.service import Service
from localagentbridge.workflow import WorkflowTask
from test_bridge import SUMMARY, wire
from test_v3_adaptive import config as legacy_config


ANSWERS = {
    'Summary': SUMMARY,
    'CodeAnalysis': {'behavior':'Bounded advisory analysis','findings':[],'uncertainties':[],
                     'recommended_tests':['Check the observable contract'],'confidence':'high'},
    'DiffReview': {'possible_bugs':['Check negative inputs'],'regressions':[],
                   'suspicious_logic':[],'missing_tests':['Negative input regression'],'confidence':'high'},
    'TestAnalysis': {'failing_tests_errors':[],'likely_cause':'No failure in the supplied log',
                    'likely_affected_components':[],'confidence':'high','recommended_investigation':[]},
    'ImplementationPlan': {'contract':'Preserve the supported inputs','steps':['Inspect the owning helper'],
                           'validation':['Test the public behavior'],'uncertainties':[],'confidence':'high'},
}


def setup(tmp_path, *, agentic=None, missing=(), callback=None, invalid=False, low=False, source=None):
    cfg=replace(legacy_config(tmp_path/'usage'),source_root=source,
                agentic=AgenticConfig(enabled=True,**(agentic or {})))
    chats=[]
    def handler(request):
        if request.url.path=='/api/tags':
            return httpx.Response(200,json={'models':[{'name':p.name} for p in cfg.model_registry if p.name not in missing]})
        body=json.loads(request.content)
        chats.append(body)
        if callback:
            callback(body)
        answer={'invalid':True} if invalid else ANSWERS[body['format']['title']].copy()
        if low and 'confidence' in answer:
            answer['confidence']='low'
        return httpx.Response(200,content=wire(answer))
    service=Service(cfg,httpx.MockTransport(handler))
    task=WorkflowTask(task_id='review-1',kind='review_change',objective='Review helper boundary behavior',
                      context='The helper must preserve supported negative inputs.',
                      diff='-return value\n+return abs(value)',test_output='1 passed',validation_status='passed')
    return service,task,chats


def step(engine,state,task,**kwargs):
    return asyncio.run(engine.step(state['run_id'],state['version'],task,**kwargs))


def reach(engine,state,task,stage):
    for _ in range(12):
        if state['next_stage']==stage or state['state']!='ready':
            return state
        state=step(engine,state,task)
    raise AssertionError('Workflow did not terminate within stage budget')


def test_review_workflow_composition_order_and_final_checkpoint(tmp_path):
    service,task,chats=setup(tmp_path)
    engine=service.workflows
    state=engine.start(task)
    with pytest.raises(BridgeError,match='Checkpoint requires'):
        engine.checkpoint(state['run_id'],state['version'],task,{'action':'accept','note':'Too early'})
    first=step(engine,state,task)
    assert [p['skill_id'] for p in first['handoffs']]==['repository-discovery','context-summary']
    assert first['next_stage']=='review' and len(chats)==1
    assert first['budget']['attempts']==1
    with pytest.raises(BridgeError,match='Stale'):
        step(engine,state,task)
    assert len(chats)==1
    reviewed=step(engine,first,task)
    assert reviewed['state']=='ready' and len(chats)==2
    assert 'untrusted_prior_results' in chats[-1]['messages'][1]['content']
    state=reach(engine,reviewed,task,'decide')
    assert [s['state'] for s in state['stages']][2:4]==['skipped','skipped']
    state=step(engine,state,task)
    assert state['state']=='waiting_for_codex'
    assert state['state']!='codex_verified'
    state=engine.checkpoint(state['run_id'],state['version'],task,{'action':'accept','note':'Inspected actual diff and log.'})
    assert state['state']=='codex_verified' and state['next_stage'] is None
    assert engine.start(task)['state']=='codex_verified' and len(chats)==2


def test_implementation_checkpoint_requires_actual_diff_and_new_evidence(tmp_path):
    service,task,chats=setup(tmp_path)
    engine=service.workflows
    task=task.model_copy(update={'kind':'implement_issue','task_id':'issue-1','diff':'','test_output':'','validation_status':'not_run'})
    state=reach(engine,engine.start(task),task,'implement')
    assert state['next_stage']=='implement' and len(chats)==2
    state=step(engine,state,task)
    assert state['state']=='waiting_for_codex'
    with pytest.raises(BridgeError,match='actual diff'):
        engine.checkpoint(state['run_id'],state['version'],task,{'action':'accept','note':'No actual change yet'})
    task=task.model_copy(update={'diff':'+bounded fix','test_output':'2 passed','validation_status':'passed','revision':'changed-source'})
    state=engine.checkpoint(state['run_id'],state['version'],task,{'action':'accept','note':'Codex applied the fix and ran focused tests.'})
    state=reach(engine,state,task,'verify')
    assert state['state']=='ready' and state['next_stage']=='verify' and len(chats)==4
    state=step(engine,state,task)
    state=engine.checkpoint(state['run_id'],state['version'],task,{'action':'accept','note':'Verified diff, tests and review.'})
    assert state['state']=='codex_verified'


@pytest.mark.parametrize('cap',['Light','Medium','Large','Maximum'])
def test_role_requirements_and_compute_caps_remain_authoritative(tmp_path,cap):
    service,task,chats=setup(tmp_path)
    engine=service.workflows
    engine.catalog.roles['code-reviewer'].requirements=Requirements(min_strength=2)
    service.bridge.store.compute_cap(value=cap)
    state=reach(engine,engine.start(task),task,'review')
    state=step(engine,state,task)
    if cap=='Light':
        assert state['state']=='handed_off' and len(chats)==1
        assert state['handoffs'][0]['payload']['_routing']['handoff_to_codex']
    else:
        assert state['state']=='ready' and chats[-1]['model']=='coder:7b'


def test_qwen_only_starter_and_insufficient_capability_handoff(tmp_path):
    from pathlib import Path
    from localagentbridge.config import load_config
    cfg=load_config(Path(__file__).resolve().parents[1]/'config.example.toml')
    cfg=replace(cfg,data_dir=tmp_path,source_root=None,agentic=AgenticConfig(enabled=True))
    chats=[]
    def handler(request):
        if request.url.path=='/api/tags':
            return httpx.Response(200,json={'models':[{'name':'qwen3:4b'}]})
        body=json.loads(request.content); chats.append(body)
        return httpx.Response(200,content=wire(ANSWERS[body['format']['title']]))
    engine=Service(cfg,httpx.MockTransport(handler)).workflows
    task=WorkflowTask(task_id='starter',kind='review_change',objective='Review helper',context='Helper evidence',diff='+small change')
    state=reach(engine,engine.start(task),task,'review')
    state=step(engine,state,task)
    assert state['state']=='ready' and {c['model'] for c in chats}=={'qwen3:4b'}
    engine.catalog.roles['code-reviewer'].requirements=Requirements(min_strength=2)
    task=task.model_copy(update={'task_id':'starter-complex'})
    state=reach(engine,engine.start(task),task,'review')
    count=len(chats)
    state=step(engine,state,task)
    assert state['state']=='handed_off' and len(chats)==count


@pytest.mark.parametrize('requirement',[
    Requirements(capabilities=['vision']),Requirements(min_context=16384)])
def test_capability_and_context_requirements_are_hard_gates(tmp_path,requirement):
    service,task,chats=setup(tmp_path)
    engine=service.workflows
    engine.catalog.roles['code-reviewer'].requirements=requirement
    state=reach(engine,engine.start(task),task,'review')
    count=len(chats)
    state=step(engine,state,task)
    assert state['state']=='handed_off' and len(chats)==count


@pytest.mark.parametrize('limit,value,expected_calls',[
    ('max_attempts',1,1),('max_reserved_tokens',8792,1),('max_output_tokens',600,1),
    ('max_input_chars',1,0)])
def test_shared_budgets_apply_across_stages(tmp_path,limit,value,expected_calls):
    service,task,chats=setup(tmp_path,agentic={'limits':Limits(**{limit:value})})
    engine=service.workflows
    state=reach(engine,engine.start(task),task,'decide')
    assert state['state']=='handed_off' and len(chats)==expected_calls
    same=engine.start(task)
    assert same['run_id']==state['run_id'] and same['budget']==state['budget']
    with pytest.raises(BridgeError):
        step(engine,state,task)


def test_stronger_retry_counts_against_shared_correction_limit(tmp_path):
    service,task,chats=setup(tmp_path,agentic={'limits':Limits(max_corrections=0)})
    engine=service.workflows
    state=reach(engine,engine.start(task),task,'review')
    # Force low-confidence output only for review, allowing exploration to complete.
    old=ANSWERS['DiffReview']['confidence']
    try:
        ANSWERS['DiffReview']['confidence']='low'
        state=step(engine,state,task)
    finally:
        ANSWERS['DiffReview']['confidence']=old
    assert state['state']=='handed_off' and len(chats)==2
    assert state['budget']['corrections']==0
    assert state['budget']['attempts']==2


def test_retry_is_stronger_fresh_evidence_and_bounded(tmp_path):
    service,task,chats=setup(tmp_path,low=True)
    engine=service.workflows
    state=reach(engine,engine.start(task),task,'review')
    state=step(engine,state,task)
    assert state['state']=='handed_off'
    assert [c['model'] for c in chats]==['small:4b','small:4b','coder:7b']
    assert chats[-1]['messages']==chats[-2]['messages']
    assert state['budget']['corrections']==1 and state['stages'][1]['attempts']==2


def test_profile_auto_escalation_opt_out_and_missing_models_do_not_substitute(tmp_path):
    service,task,chats=setup(tmp_path,missing=['small:4b'])
    state=step(service.workflows,service.workflows.start(task),task)
    assert state['state']=='handed_off' and not chats
    service,task,chats=setup(tmp_path/'other',invalid=True)
    service.workflows.catalog.roles['repository-explorer'].requirements=Requirements(auto_escalate=False)
    state=step(service.workflows,service.workflows.start(task),task)
    assert state['state']=='handed_off' and len(chats)==1


def test_lowered_cap_blocks_next_retry(tmp_path):
    service=None
    def callback(body):
        if body['format']['title']=='DiffReview':
            service.bridge.store.compute_cap(value='Light')
    service,task,chats=setup(tmp_path,low=True,callback=callback)
    service.bridge.store.compute_cap(value='Large')
    state=reach(service.workflows,service.workflows.start(task),task,'review')
    state=step(service.workflows,state,task)
    assert state['state']=='handed_off' and len(chats)==2
    assert state['handoffs'][0]['payload']['_routing']['cap']=='Light'


def test_required_security_resource_stages_and_no_model_pins(tmp_path):
    service,task,chats=setup(tmp_path)
    task=task.model_copy(update={'security_review':True,'resource_review':True})
    state=reach(service.workflows,service.workflows.start(task),task,'decide')
    assert len(chats)==4 and state['state']=='ready'
    assert [s['state'] for s in state['stages']][:4]==['advisory_complete']*4
    task=task.model_copy(update={'kind':'implement_issue'})
    with pytest.raises(BridgeError,match='absent'):
        service.workflows.plan(task)


def test_evidence_changes_require_codex_and_rejected_review_is_terminal(tmp_path):
    service,task,chats=setup(tmp_path)
    engine=service.workflows
    state=engine.start(task)
    with pytest.raises(BridgeError,match='changed outside'):
        step(engine,state,task.model_copy(update={'diff':'+different change'}))
    state=reach(engine,state,task,'decide')
    state=step(engine,state,task)
    with pytest.raises(BridgeError,match='Changed evidence'):
        engine.checkpoint(state['run_id'],state['version'],task.model_copy(update={'context':'changed'}),
                          {'action':'accept','note':'Stale review'})
    state=engine.checkpoint(state['run_id'],state['version'],task,{'action':'reject','note':'Contract not preserved'})
    assert state['state']=='rejected' and state['next_stage'] is None


def test_unrun_checks_are_not_silently_certified(tmp_path):
    service,task,_=setup(tmp_path)
    task=task.model_copy(update={'validation_status':'not_run','test_output':''})
    engine=service.workflows
    state=step(engine,reach(engine,engine.start(task),task,'decide'),task)
    with pytest.raises(BridgeError,match='acknowledge'):
        engine.checkpoint(state['run_id'],state['version'],task,{'action':'accept','note':'Inspected review'})
    state=engine.checkpoint(state['run_id'],state['version'],task,
        {'action':'accept','note':'Review complete; tests explicitly not run.','acknowledge_unverified_checks':True})
    assert state['validation_status']=='not_run'


def test_restart_requires_exact_handoffs_and_never_reexecutes(tmp_path):
    service,task,chats=setup(tmp_path)
    engine=service.workflows
    first=step(engine,engine.start(task),task)
    restarted=Service(service.config,service.bridge.transport).workflows
    with pytest.raises(BridgeError,match='Re-supply'):
        step(restarted,first,task)
    assert len(chats)==1
    forged=json.loads(json.dumps(first['handoffs']))
    forged[-1]['payload']['important_findings']=['Forged approval']
    with pytest.raises(BridgeError,match='does not match'):
        step(restarted,first,task,handoffs=forged)
    reviewed=step(restarted,first,task,handoffs=first['handoffs'])
    assert reviewed['state']=='ready' and len(chats)==2


def test_stale_discovered_source_cannot_be_consumed(tmp_path):
    repo=tmp_path/'repo'; repo.mkdir()
    path=repo/'helper.py'; path.write_text('def helper_boundary(value):\n    return value\n')
    service,task,chats=setup(tmp_path,source=repo)
    engine=service.workflows
    first=step(engine,engine.start(task),task)
    path.write_text('def helper_boundary(value):\n    return -value\n')
    with pytest.raises(BridgeError,match='stale'):
        step(engine,first,task)
    assert len(chats)==1


def test_shared_lease_blocks_other_instance_and_interruption_keeps_reservations(tmp_path):
    service,task,_=setup(tmp_path)
    engine=service.workflows
    first=engine.start(task)
    second=engine.start(task.model_copy(update={'task_id':'second'}))
    stage=engine.plan(task)['stages'][0]
    owner,_=engine.ledger.claim(first['run_id'],first['version'],stage,20)
    restarted=Service(service.config,service.bridge.transport).workflows
    with pytest.raises(BridgeError,match='busy'):
        step(restarted,second,task.model_copy(update={'task_id':'second'}))
    with engine.ledger.store.connect() as db:
        db.execute('UPDATE workflow_lease SET expires=?',(time.time()-1,))
    recovered=restarted.status(first['run_id'])
    assert recovered['state']=='handed_off' and recovered['reason']=='interrupted'
    assert recovered['budget']['seconds']==20
    with pytest.raises(BridgeError,match='expired'):
        engine.ledger.finish(owner,1,'ready')


def test_cancellation_and_elapsed_budget_stop_without_late_progress(tmp_path):
    service,task,_=setup(tmp_path,agentic={'limits':Limits(max_seconds=1)})
    async def slow(request):
        if request.url.path=='/api/tags':
            return httpx.Response(200,json={'models':[{'name':p.name} for p in service.config.model_registry]})
        await asyncio.sleep(5)
        return httpx.Response(200,content=wire(SUMMARY))
    service.bridge.transport=httpx.MockTransport(slow)
    engine=service.workflows
    state=step(engine,engine.start(task),task)
    assert state['state']=='handed_off' and state['budget']['attempts']==1
    assert state['budget']['seconds']>=1
    with engine.ledger.store.connect() as db:
        assert db.execute('SELECT COUNT(*) FROM workflow_lease').fetchone()[0]==0


def test_large_prompt_cannot_silently_truncate_or_spend_a_generation(tmp_path):
    service,task,chats=setup(tmp_path)
    task=task.model_copy(update={'context':'evidence '*950})
    state=step(service.workflows,service.workflows.start(task),task)
    assert state['state']=='handed_off' and not chats
    assert state['budget']['attempts']==0 and 'context_fit' in state['handoffs'][-1]['payload']['_routing']['reason']


def test_telemetry_records_metadata_not_context_or_prompts(tmp_path):
    service,task,chats=setup(tmp_path)
    marker='PRIVATE_PAYLOAD_DO_NOT_RETAIN'
    task=task.model_copy(update={'context':marker})
    state=reach(service.workflows,service.workflows.start(task),task,'decide')
    assert any(marker in json.dumps(c) for c in chats)
    with service.bridge.store.connect() as db:
        dump='\n'.join(db.iterdump())
        assert marker not in dump
        assert 'Independently challenge a change' not in dump
        assert db.execute('SELECT COUNT(*) FROM workflow_attempts').fetchone()[0]==2
    assert all(a['selection_reason'] and a['model'] for a in state['attempts'])
    assert sum(a['input_tokens'] for a in state['attempts'])>0


def test_correction_rewinds_without_refunding_stage_or_workflow_attempts(tmp_path):
    service,task,chats=setup(tmp_path,agentic={'limits':Limits(max_corrections=1)})
    engine=service.workflows
    state=step(engine,reach(engine,engine.start(task),task,'decide'),task)
    before=state['budget']['attempts']
    changed=task.model_copy(update={'diff':'+corrected implementation','revision':'fixed'})
    state=engine.checkpoint(state['run_id'],state['version'],changed,{'action':'revise','note':'Codex corrected the defect; review the new diff.'})
    assert state['next_stage']=='explore' and state['budget']['attempts']==before
    assert state['budget']['corrections']==1 and state['stages'][-1]['state']=='pending'
    state=step(engine,reach(engine,state,changed,'decide'),changed)
    assert state['state']=='waiting_for_codex' and len(chats)==4
    with pytest.raises(BridgeError,match='No remaining correction'):
        engine.checkpoint(state['run_id'],state['version'],changed,{'action':'revise','note':'Again'})


def test_role_allowlist_memory_quality_and_disabled_gates(tmp_path):
    from localagentbridge.catalog import RoleOverride
    service,task,chats=setup(tmp_path)
    engine=service.workflows
    profile=engine.catalog.profiles['generic']
    profile.role_overrides=[RoleOverride(role='code-reviewer',allowed_models=['dense:14b'])]
    state=reach(engine,engine.start(task),task,'review')
    state=step(engine,state,task)
    assert state['state']=='handed_off' and len(chats)==1  # default Medium excludes the un-tiered dense model
    profile.role_overrides=[]
    for p in service.config.model_registry:
        p.reliability['review_diff']={'reviewed_cases':10,'accepted_rate':0,'rejected_rate':1}
    task=task.model_copy(update={'task_id':'quality-blocked'})
    state=reach(engine,engine.start(task),task,'review')
    before=len(chats)
    state=step(engine,state,task)
    assert state['state']=='handed_off' and len(chats)==before
    assert 'benchmark_reliability' in state['handoffs'][0]['payload']['_routing']['reason']


def test_abort_does_not_require_missing_source_rehydration(tmp_path):
    repo=tmp_path/'repo'; repo.mkdir()
    path=repo/'helper.py'; path.write_text('def helper(value):\n    return value\n')
    service,task,_=setup(tmp_path,source=repo)
    from localagentbridge.workflow import FileExcerpt
    task=task.model_copy(update={'files':[FileExcerpt(path='helper.py',first_line=1,last_line=2)]})
    engine=service.workflows
    state=step(engine,reach(engine,engine.start(task),task,'decide'),task)
    path.unlink()
    state=engine.checkpoint(state['run_id'],state['version'],task,{'action':'abort','note':'Task cancelled'})
    assert state['state']=='aborted'


def test_doc_review_receives_actual_diff_without_prior_routing_noise(tmp_path):
    from pathlib import Path
    from localagentbridge.config import load_config
    from localagentbridge.workflow import FileExcerpt
    repo=Path(__file__).resolve().parents[1]
    _,task,chats=setup(tmp_path,source=repo)
    # Regression for the first real dogfood: source + two handoffs did not fit 8192.
    cfg=load_config(repo/'examples/v0.5/minimal.toml')
    cfg.data_dir=tmp_path/'starter'
    cfg.search.max_candidates=cfg.search.max_results=1
    def handler(request):
        if request.url.path=='/api/tags':
            return httpx.Response(200,json={'models':[{'name':'qwen3:4b'}]})
        body=json.loads(request.content)
        chats.append(body)
        return httpx.Response(200,content=wire(ANSWERS[body['format']['title']]))
    service=Service(cfg,httpx.MockTransport(handler))
    task=task.model_copy(update={'scope':'localagentbridge','objective':'Review model_tier runtime eligibility',
        'diff':'+    """Return a tier guaranteeing all current runtime memory, latency and quality gates pass."""',
        'files':[FileExcerpt(path='localagentbridge/models.py',first_line=99,last_line=136)]})
    engine=service.workflows
    state=step(engine,engine.start(task),task)
    assert len(chats)==1
    assert 'guaranteeing all current runtime' in chats[0]['messages'][1]['content']
    state=step(engine,state,task)
    assert state['state']=='ready' and len(chats)==2
    assert '_routing' not in chats[-1]['messages'][1]['content']
    assert '_meta' not in chats[-1]['messages'][1]['content']


def test_revised_failed_stage_does_not_reuse_previous_cycle_results(tmp_path):
    service,task,chats=setup(tmp_path)
    engine=service.workflows
    engine.catalog.roles['repository-explorer'].requirements=Requirements(max_attempts=1)
    state=step(engine,reach(engine,engine.start(task),task,'decide'),task)
    changed=task.model_copy(update={'diff':'+new corrected diff','revision':'corrected'})
    state=engine.checkpoint(state['run_id'],state['version'],changed,{'action':'revise','note':'Review corrected evidence.'})
    state=step(engine,state,changed)
    assert state['state']=='handed_off'  # stage's generation budget was already spent
    state=engine.checkpoint(state['run_id'],state['version'],changed,{'action':'accept','note':'Codex inspected current source and resolved exploration.'})
    state=step(engine,state,changed)
    assert state['state']=='ready' and state['next_stage']=='security'
    assert len(chats)==3  # only the revised reviewer generated again
