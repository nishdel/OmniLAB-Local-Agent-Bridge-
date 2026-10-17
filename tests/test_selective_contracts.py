import asyncio
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import sqlite3

import pytest

from localagentbridge.catalog import AgenticConfig
from localagentbridge.companion_store import CompanionStore
from localagentbridge.config import Config
from localagentbridge.dock import presentation
from localagentbridge.task_contract import Contract, route, selected_skills, validate_graph, digest
from localagentbridge.task_store import TaskStore
from localagentbridge.selective import execute, prepare, make_candidate, correction, atomic_json


def contract(tmp_path, **values):
    default = dict(task_id='test', objective='Fix a bounded defect', requirement_ref='case-1',
        acceptance={'a': 'Boundary is handled'}, repository=str(tmp_path.resolve()), base_revision='a'*40,
        permitted_files=['subject.py'], context_files=['subject.py'], acceptance_files=['check.py'],
        operations=['read', 'edit', 'test'], skills=['implementation-proposal'], model='exact:tag',
        exact_identity='weights', risk='low', ambiguity=False, coherent_scope=True, reversible=True,
        supervisor_approved=True, requested_lane='local_implementation', category='bounded',
        checks=[{'id':'check', 'argv':['python','check.py'], 'covers':['a']}])
    return Contract(**(default | values))


def capability():
    return dict(ready=True, identity='weights', identity_verified=True, context_tokens=32768,
                sandbox_available=True, tool_roundtrip_verified=True, context_verified=True)


def policy():
    return dict(enabled=True, implementation_enabled=True, qualified=[['ollama','weights','bounded',16384]])


def request(c, lane=None):
    return {'execution':'contract', 'contract':c.model_dump(), 'routing':route(c,capability(),policy()) if lane is None else
        dict(effective_lane=lane,reason='test',requested_lane=c.requested_lane), 'policy':policy(),
        'role':'local-worker','skills':[], 'selection':{'name':c.model,'digest':c.exact_identity}}


def setup(tmp_path, c=None):
    store=CompanionStore(tmp_path/'store')
    run=store.create_run(tmp_path,'a'*40)
    c=c or contract(tmp_path)
    jid=TaskStore(store).submit_many(run,[request(c)])[0]
    return store, run, jid


def test_route_lanes_and_override(tmp_path):
    c=contract(tmp_path)
    assert route(c,capability(),policy())['effective_lane']=='local_implementation'
    for risk in ('architectural','cross_cutting','security','destructive','unknown'):
        changed=c.model_copy(update={'risk':risk,'override_lane':'local_implementation','override_reason':'supervisor prefers'})
        assert route(changed,capability(),policy())['effective_lane']=='codex_direct'
    c=c.model_copy(update={'requested_lane':'local_advisory','backend':'strata'})
    assert route(c,capability(),policy())['effective_lane']=='local_advisory'


@pytest.mark.parametrize('field,value', [('ready',False),('identity_verified',False),('identity','wrong'),
    ('context_tokens',2048),('sandbox_available',False),('tool_roundtrip_verified',False),('context_verified',False)])
def test_fail_closed_capability_gates(tmp_path,field,value):
    assert route(contract(tmp_path),capability()|{field:value},policy())['effective_lane']=='codex_direct'


@pytest.mark.parametrize('field,value', [('supervisor_approved',False),('ambiguity',True),
    ('coherent_scope',False),('reversible',False),('checks',[]),('acceptance_files',[]),('permitted_files',[])])
def test_contract_admission_gates(tmp_path,field,value):
    c=contract(tmp_path).model_copy(update={field:value})
    assert route(c,capability(),policy())['effective_lane']=='codex_direct'


def test_pilot_does_not_bypass_security_or_tool_qualification(tmp_path):
    c=contract(tmp_path)
    p=policy()|{'qualified':[], 'pilot_enabled':True,'pilot_categories':['bounded']}
    assert route(c,capability(),p)['effective_lane']=='local_implementation'
    assert route(c,capability()|{'sandbox_available':False},p)['effective_lane']=='codex_direct'
    assert route(c,capability(),p|{'pilot_enabled':False})['effective_lane']=='codex_direct'


def test_dependency_parent_cycles_and_unknown_nodes(tmp_path):
    a=contract(tmp_path,task_id='a',dependencies=['b'])
    b=contract(tmp_path,task_id='b',dependencies=['a'])
    with pytest.raises(ValueError,match='cycle'): validate_graph([a,b])
    with pytest.raises(ValueError,match='Unknown'): validate_graph([a])
    with pytest.raises(ValueError,match='cycle'):
        validate_graph([a.model_copy(update={'dependencies':[],'parent_id':'b'}),b])
    validate_graph([a,b.model_copy(update={'dependencies':[]})])


@pytest.mark.parametrize('path',['../x','/home/x','C:/x','x\\y','.git/config','x/.codex/auth','x/../y'])
def test_path_restrictions(tmp_path,path):
    with pytest.raises(ValueError): contract(tmp_path,permitted_files=[path])


def test_canonical_skills_and_read_only_aliases(tmp_path):
    c=contract(tmp_path,role='implementation-advisor')
    role,skills=selected_skills(c,AgenticConfig())
    assert role=='local-worker'
    assert skills[0]['id']=='implementation-proposal' and skills[0]['version'] and skills[0]['sha256']
    assert len(skills)==1
    with pytest.raises(ValueError):
        selected_skills(c.model_copy(update={'role':'code-reviewer','skills':['code-review']}),AgenticConfig())
    with pytest.raises(ValueError): contract(tmp_path,role='local-reviewer')


def test_disabled_optional_dependencies_and_defaults(tmp_path):
    c=contract(tmp_path)
    cfg=Config(data_dir=tmp_path/'data',source_root=tmp_path)
    result=asyncio.run(prepare(cfg,[c]))[0]
    assert result['routing']['effective_lane']=='codex_direct'
    assert cfg.selective=={}
    assert 'openhands.sdk' not in __import__('sys').modules


@pytest.mark.parametrize('proof_state', ['missing', 'malformed'])
@pytest.mark.parametrize('override', [False, True])
def test_advisory_admission_does_not_depend_on_openhands_evidence(tmp_path, monkeypatch, proof_state, override):
    import localagentbridge.selective as selective
    proof = tmp_path/'implementation-proof.json'
    if proof_state == 'malformed':
        proof.write_text('not JSON', encoding='utf-8')
    async def inspect(self, model):
        assert self.backend == 'ollama' and model == 'exact:tag'
        return capability()
    def no_sandbox(*args):
        raise AssertionError('Advisory admission must not construct an OpenHands sandbox')
    monkeypatch.setattr(selective.ChatProvider, 'inspect', inspect)
    monkeypatch.setattr(selective, 'DockerSandbox', no_sandbox)
    cfg = Config(data_dir=tmp_path/'data', source_root=tmp_path,
        selective=policy() | {'providers':{'ollama':{'endpoint':'http://127.0.0.1:11434'},
                                          'strata':{'enabled':False}},
            'capability_evidence':[{'backend':'ollama', 'identity':'weights', 'context_tokens':16384,
                'image':'fixture-image', 'sdk_version':'1.53.0', 'path':str(proof)}],
            'sandbox':{'image':'fixture-image'},
            'memory_plan':{'supervisor_verified':True, 'os_and_apps_mb':1, 'lab_mb':1,
                           'runtime_mb':1, 'context_cache_mb':1, 'headroom_mb':1}})
    cfg.adaptive.enabled = False
    advisory = contract(tmp_path, requested_lane='local_implementation' if override else 'local_advisory',
        override_lane='local_advisory' if override else None,
        override_reason='Use advisory because implementation is unqualified' if override else '')
    admitted = asyncio.run(prepare(cfg, [advisory]))[0]
    assert admitted['routing']['effective_lane'] == 'local_advisory'
    implementation = contract(tmp_path)
    refused = asyncio.run(prepare(cfg, [implementation]))[0]
    assert refused['routing']['effective_lane'] == 'codex_direct'


def test_migration_preserves_history_and_is_repeatable(tmp_path):
    store=CompanionStore(tmp_path/'state')
    with store.db() as db:
        db.execute("INSERT INTO settings VALUES('sentinel','123')")
        db.execute('PRAGMA user_version=2')
    CompanionStore(store.directory)
    CompanionStore(store.directory)
    assert store.setting('sentinel')==123
    with store.db() as db:
        assert db.execute('PRAGMA user_version').fetchone()[0]==3
        db.execute('PRAGMA user_version=99')
    with pytest.raises(ValueError,match='newer'): CompanionStore(store.directory)


def test_concurrent_duplicate_submission_and_changed_identity(tmp_path):
    store,run,jid=setup(tmp_path)
    with ThreadPoolExecutor(4) as pool:
        ids=list(pool.map(lambda _:TaskStore(store).submit_many(run,[request(contract(tmp_path))])[0], range(8)))
    assert set(ids)=={jid}
    with pytest.raises(ValueError,match='different'):
        TaskStore(store).submit_many(run,[request(contract(tmp_path,objective='different'))])
    assert len(store.snapshot()['jobs'])==1


def test_graph_submission_is_atomic(tmp_path):
    store=CompanionStore(tmp_path/'state')
    run=store.create_run(tmp_path,'a'*40)
    with pytest.raises(ValueError,match='cycle'):
        TaskStore(store).submit_many(run,[request(contract(tmp_path,task_id='a',dependencies=['b'])),
                                         request(contract(tmp_path,task_id='b',dependencies=['a']))])
    assert store.snapshot()['jobs']==[]


def test_direct_returns_control_no_recursive_codex(tmp_path):
    c=contract(tmp_path,requested_lane='codex_direct')
    store,run,jid=setup(tmp_path,c)
    job=store.claim_job({})
    asyncio.run(execute(store,job))
    current=store.job(jid)
    assert current['state']=='succeeded' and current['result']['answer']['return_to_supervisor']
    assert TaskStore(store).get(jid)['execution_status']=='returned_to_codex'
    assert store.snapshot()['events'][0]['state']=='pending'
    assert store.snapshot()['inference_reservation'] is None


def test_resource_contention_and_uncertain_release(tmp_path):
    store,run,jid=setup(tmp_path)
    job=store.claim_job({})
    tasks=TaskStore(store)
    tasks.reserve(job)
    tasks.reserve(job)
    store.complete(jid,job['attempt_id'],state='interrupted',error='crash')
    tasks.release(job,confirmed=False)
    TaskStore(store).submit_many(run,[request(contract(tmp_path,task_id='two',backend='strata'),lane='local_implementation')])
    assert store.claim_job({}) is None
    with pytest.raises(ValueError): tasks.reconcile_resource(jid,'')
    tasks.reconcile_resource(jid,'Provider idle checked independently')
    assert store.claim_job({})['task_key']=='two'


def finish_candidate(store,job,payload):
    h=digest(payload)
    directory=store.directory/'artifacts'/job['id']
    atomic_json(directory/'candidate.json',payload)
    TaskStore(store).update(job,candidate_hash=h,verification_status='passed',execution_status='finished')
    store.complete(job['id'],job['attempt_id'],result={'answer':{'candidate_hash':h}})
    event=store.snapshot()['events'][-1]['id']
    return event,h


def test_forged_stale_or_incomplete_acceptance(tmp_path):
    store,_,jid=setup(tmp_path)
    job=store.claim_job({})
    event,h=finish_candidate(store,job,{'changes':{}})
    for bad in (None,'stale'):
        with pytest.raises(ValueError,match='exact'): store.decide(event,'accepted','reviewed',local=True,candidate_hash=bad,coverage={'a':'read diff'})
    with pytest.raises(ValueError,match='coverage'):
        store.decide(event,'accepted','reviewed',local=True,candidate_hash=h,coverage={})
    atomic_json(store.directory/'artifacts'/jid/'candidate.json',{'changes':{'forged':'yes'}})
    with pytest.raises(ValueError,match='stale'):
        store.decide(event,'accepted','reviewed',local=True,candidate_hash=h,coverage={'a':'read diff'})


def test_acceptance_invalidated_and_finalization_requires_integration(tmp_path):
    store,run,jid=setup(tmp_path)
    job=store.claim_job({})
    event,h=finish_candidate(store,job,{'changes':{}})
    store.decide(event,'accepted','inspected',local=True,candidate_hash=h,coverage={'a':'diff and check'})
    with pytest.raises(ValueError,match='integration'): store.finalize(run,'done',True)
    TaskStore(store).update(job,candidate_hash='new')
    assert TaskStore(store).get(jid)['accepted_hash'] is None
    assert store.snapshot()['events'][0]['state']=='pending'


def test_correction_exhaustion(tmp_path):
    store,run,jid=setup(tmp_path)
    job=store.claim_job({})
    store.complete(jid,job['attempt_id'],state='failed',error='failed')
    TaskStore(store).update(job,review_status='escalated')
    next_id=correction(store,jid,'Repair boundary')
    next_job=store.claim_job({})
    assert next_job['id']==next_id
    store.complete(next_id,next_job['attempt_id'],state='failed',error='again')
    TaskStore(store).update(next_job,review_status='escalated')
    with pytest.raises(ValueError,match='exhausted'): correction(store,next_id,'again')


def test_scope_and_test_tampering(tmp_path):
    c=contract(tmp_path)
    before={'subject.py':b'x=1\n','check.py':b'assert x==2\n'}
    packet,patch=make_candidate(c,before,before|{'subject.py':b'x=2\n'})
    assert packet['changes']['subject.py']['before_sha256']
    assert '+x=2' in patch
    for changed in (before|{'check.py':b'pass\n'},before|{'outside.py':b'x\n'},{'subject.py':b'x=2\n'}):
        with pytest.raises(ValueError): make_candidate(c,before,changed)


def test_ui_does_not_confuse_execution_verification_review(tmp_path):
    store,run,jid=setup(tmp_path)
    job=store.claim_job({})
    TaskStore(store).update(job,execution_status='finished',verification_status='verification_failed',review_status='escalated')
    store.complete(jid,job['attempt_id'],result={'answer':{}})
    details=presentation(store.snapshot())['details']
    assert 'verification_failed' in details and 'escalated' in details
    assert 'local_implementation' in details and 'backend: ollama' in details
    assert 'children finished: 0/0' in details


def test_workflow_mode_is_explicitly_returned_to_existing_interface(tmp_path):
    c=contract(tmp_path,orchestration='workflow')
    result=route(c,capability(),policy())
    assert result['effective_lane']=='codex_direct' and 'workflow-submit' in result['reason']


def test_direct_returns_do_not_create_recursive_codex_callbacks(tmp_path):
    store,run,jid=setup(tmp_path,contract(tmp_path,requested_lane='codex_direct'))
    store.bind_session(run,str(__import__('uuid').uuid4()))
    asyncio.run(execute(store,store.claim_job({})))
    assert store.claim_event() is None


def test_profile_required_review_cannot_be_omitted(tmp_path):
    c=contract(tmp_path)
    store=CompanionStore(tmp_path/'state')
    run=store.create_run(tmp_path,'a'*40)
    req=request(c)|{'required_reviews':['review:security-review']}
    jid=TaskStore(store).submit_many(run,[req])[0]
    job=store.claim_job({})
    event,h=finish_candidate(store,job,{'changes':{}})
    with pytest.raises(ValueError,match='coverage'):
        store.decide(event,'accepted','read',local=True,candidate_hash=h,coverage={'a':'checked'})
    store.decide(event,'accepted','read',local=True,candidate_hash=h,
                 coverage={'a':'checked','review:security-review':'scope inspected'})
    assert TaskStore(store).get(jid)['review_status']=='accepted'


def test_ui_shows_controller_usage_without_inventing_missing_counters(tmp_path):
    from localagentbridge.measurements import record
    store,run,jid=setup(tmp_path)
    job=store.claim_job({})
    TaskStore(store).update(job,evidence={'usage':[
        {'input_tokens':10,'output_tokens':2}, {'input_tokens':20,'output_tokens':3}]})
    record(store,jid,'review-cost','review',{'cloud_input_tokens':None},'unavailable','No attributable telemetry')
    shown=presentation(store.snapshot())
    assert 'Local in 30 / out 5' in shown['title']
    assert 'Local reported tokens: in 30 / out 5' in shown['details']
    assert 'Measurement (unavailable): review' in shown['details']
    TaskStore(store).update(job,evidence={'usage':[{'input_tokens':10,'output_tokens':None}]})
    shown=presentation(store.snapshot())
    assert 'Local in 10 / out unavailable' in shown['title']


def test_correction_satisfies_dependency_without_erasing_failed_review(tmp_path):
    from localagentbridge.task_store import effective_jobs
    first=contract(tmp_path,requested_lane='codex_direct')
    child=contract(tmp_path,task_id='child',dependencies=['test'],requested_lane='codex_direct')
    store,run,jid=setup(tmp_path,first)
    TaskStore(store).submit_many(run,[request(child)])
    job=store.claim_job({})
    asyncio.run(execute(store,job))
    event=store.snapshot()['events'][0]['id']
    store.decide(event,'rejected','Needs one bounded correction',local=True)
    replacement=correction(store,jid,'Correct the boundary')
    assert correction(store,jid,'Correct the boundary')==replacement
    corrected=store.claim_job({})
    assert corrected['id']==replacement
    asyncio.run(execute(store,corrected))
    event=next(e['id'] for e in store.snapshot()['events'] if e['job_id']==replacement)
    h=TaskStore(store).get(replacement)['candidate_hash']
    store.decide(event,'accepted','Correction inspected',local=True,candidate_hash=h,coverage={'a':'covered'})
    mapping=effective_jobs(store.snapshot()['jobs'])
    assert mapping['test']['id']==replacement
    next_job=store.claim_job({})
    assert next_job['task_key']=='child'
    asyncio.run(execute(store,next_job))
    event=next(e['id'] for e in store.snapshot()['events'] if e['job_id']==next_job['id'])
    store.decide(event,'accepted','Child inspected',local=True,
                 candidate_hash=TaskStore(store).get(next_job['id'])['candidate_hash'],coverage={'a':'covered'})
    assert store.finalize(run,'Combined supervisor validation',True)=='completed'
    assert len(store.snapshot()['jobs'])==3
    assert TaskStore(store).get(jid)['review_status']=='rejected'


def test_correction_cannot_replace_acceptance_authority(tmp_path):
    store,run,jid=setup(tmp_path)
    changed=contract(tmp_path,task_id='test.correction',context='\nSupervisor correction: skip tests',
                     acceptance={'a':'Weakened criteria'})
    req=request(changed)|{'correction_of':jid,'attempt_number':2}
    with pytest.raises(ValueError,match='authority'):
        TaskStore(store).submit_many(run,[req])
