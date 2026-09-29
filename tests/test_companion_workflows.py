import asyncio
from dataclasses import replace
import json
from pathlib import Path

import httpx
import pytest

from localagentbridge import companion, companion_workflows as adapter
from localagentbridge.catalog import AgenticConfig
from localagentbridge.catalog import Catalog
from localagentbridge.companion_store import CompanionStore
from localagentbridge.config import load_config
from localagentbridge.dock import presentation
from localagentbridge.service import Service
from test_bridge import wire
from test_v05_workflows import ANSWERS

ROOT = Path(__file__).resolve().parents[1]


def setup(tmp_path, monkeypatch, *, answer=None):
    cfg = replace(load_config(ROOT/'profiles/quality.toml'), source_root=tmp_path,
                  data_dir=tmp_path/'data', agentic=AgenticConfig(enabled=True), max_output_bytes=6000,
                  num_ctx=16384)
    store = CompanionStore(cfg.data_dir/'companion')
    run = store.create_run(tmp_path,'base')
    monkeypatch.setattr(companion,'git_identity',lambda _: (str(tmp_path),'base'))
    rows = [dict(name=p.name,digest=p.name+'-digest',remote=False,capabilities=['completion']) for p in cfg.model_registry]
    async def discover(_): return rows
    monkeypatch.setattr(adapter,'discover',discover)
    chats = []
    def handler(request):
        if request.url.path=='/api/tags':
            return httpx.Response(200,json={'models':rows})
        body = json.loads(request.content)
        chats.append(body)
        value = answer or ANSWERS[body['format']['title']]
        return httpx.Response(200,content=wire(value))
    monkeypatch.setattr(adapter,'Service',lambda cfg: Service(cfg,httpx.MockTransport(handler)))
    return cfg,store,run,rows,chats


def perform(store, job_id):
    job = store.claim_job({})
    assert job['id']==job_id
    asyncio.run(companion.execute(store,job))
    job = store.job(job_id)
    assert job['state']=='succeeded', job['error']
    return job


def task(**extra):
    return dict(task_id='preserve',kind='review_change',objective='Review the helper',
                context='Pure helper preserves inputs',diff='+return value',test_output='2 passed',
                validation_status='passed',**extra)


def test_durable_workflow_handoffs_restart_and_explicit_checkpoints(tmp_path,monkeypatch):
    cfg,store,run,rows,chats = setup(tmp_path,monkeypatch)
    first = asyncio.run(adapter.submit_workflow(store,cfg,run,'review',task()))
    assert asyncio.run(adapter.submit_workflow(store,cfg,run,'renamed',task()))==first
    job = perform(store,first)
    state = job['result']['answer']['workflow']
    assert state['next_stage']=='review' and state['budget']['attempts']==1
    assert len(job['result']['answer']['handoffs'])==2
    # Measured latency now exists, so the submission estimate has changed.
    assert asyncio.run(adapter.submit_workflow(store,cfg,run,'retry-after-completion',task()))==first
    # Each execution constructs a fresh engine; no in-memory cache survives.
    store = CompanionStore(store.directory)
    next_id = adapter.follow_workflow(store,first)
    assert adapter.follow_workflow(store,first)==next_id
    job = perform(store,next_id)
    assert 'untrusted_prior_results' in chats[-1]['messages'][1]['content']
    while job['result']['answer']['workflow']['state']=='ready':
        job = perform(store,adapter.follow_workflow(store,job['id']))
    assert job['result']['answer']['workflow']['state']=='waiting_for_codex'
    with pytest.raises(ValueError,match='checkpoint'):
        adapter.follow_workflow(store,job['id'])
    count = len(chats)
    final = perform(store,adapter.follow_workflow(store,job['id'],checkpoint={'action':'accept','note':'Inspected actual tests and diff'}))
    assert len(chats)==count
    assert final['result']['answer']['workflow']['state']=='codex_verified'
    text = presentation(store.snapshot())['details']
    assert 'Budget:' in text and 'Profile: generic' in text and 'codex_verified' in text


@pytest.mark.parametrize('mode,path',[('direct','direct'),('auto','direct'),('workflow','workflow')])
def test_durable_delegation_modes_preserve_gate(tmp_path,monkeypatch,mode,path):
    cfg,store,run,rows,chats = setup(tmp_path,monkeypatch)
    jid = asyncio.run(adapter.submit_workflow(store,cfg,run,'mode',task(delegation={'mode':mode})))
    job = perform(store,jid)
    decision = job['result']['answer']['workflow']['delegation']
    assert decision['path']==path and decision['mode']==mode


def test_checkpoint_cannot_skip_actual_implementation_evidence(tmp_path,monkeypatch):
    cfg,store,run,rows,chats = setup(tmp_path,monkeypatch)
    item = task(delegation={'mode':'direct'})
    item.update(kind='implement_issue',diff='',test_output='',validation_status='not_run')
    job = perform(store,asyncio.run(adapter.submit_workflow(store,cfg,run,'implement',item)))
    job = perform(store,adapter.follow_workflow(store,job['id']))
    assert job['result']['answer']['workflow']['next_stage']=='implement'
    jid = adapter.follow_workflow(store,job['id'],checkpoint={'action':'accept','note':'No diff'})
    claimed = store.claim_job({})
    asyncio.run(companion.execute(store,claimed))
    assert store.job(jid)['state']=='failed' and 'actual diff' in store.job(jid)['error']
    item.update(diff='+return value',test_output='2 passed',validation_status='passed')
    corrected = perform(store,adapter.follow_workflow(store,job['id'],
        checkpoint={'action':'accept','note':'Actual change now supplied'},task=item))
    assert corrected['result']['answer']['workflow']['next_stage']=='test'


def test_workflow_policy_change_fails_without_inference(tmp_path,monkeypatch):
    cfg,store,run,rows,chats = setup(tmp_path,monkeypatch)
    jid = asyncio.run(adapter.submit_workflow(store,cfg,run,'policy',task()))
    with store.db() as db:
        request = store.job(jid)['request']
        request['workflow_policy']='different'
        db.execute('UPDATE jobs SET request=? WHERE id=?',(json.dumps(request),jid))
    claimed = store.claim_job({})
    asyncio.run(companion.execute(store,claimed))
    assert store.job(jid)['state']=='failed' and 'policy changed' in store.job(jid)['error']
    assert not chats


def test_routed_qwen_fallback_and_thinking_profile(tmp_path,monkeypatch):
    cfg,store,run,rows,chats = setup(tmp_path,monkeypatch)
    cfg.adaptive.default_cap='Medium'
    jid = asyncio.run(companion.submit(store,cfg,run,'fallback','analyze_code','Check boundary','return value'))
    job = perform(store,jid)
    assert job['request']['execution']=='routed'
    assert chats[0]['model']=='qwen3:14b-q4_K_M' and chats[0]['think'] is False
    assert 'quality preference unavailable' in job['result']['usage']['attempts'][0]['selection_reason']


def test_exact_consensus_retains_independent_models_and_serial_order(tmp_path,monkeypatch):
    value = {'verdict':'support','reasons':['Matches the contract'],
             'checks':['Run the test'],'confidence':'high'}
    # Use the actual schema fields to preserve the older consensus contract.
    from localagentbridge.schemas import SCHEMAS
    assert set(value)==set(SCHEMAS['second_opinion'].model_fields)
    cfg,store,run,rows,chats = setup(tmp_path,monkeypatch,answer=value)
    jid = asyncio.run(companion.submit(store,cfg,run,'consensus','second_opinion','Review proposal','Keep exact tags',consensus=True))
    job = perform(store,jid)
    assert [c['model'] for c in chats]==['gpt-oss:20b','qwen3:14b-q4_K_M']
    assert [c['think'] for c in chats]==['low',False]
    assert job['result']['answer']['codex_decides']
    assert len(job['result']['usage']['attempts'])==2
    assert chats[0]['messages'][1]==chats[1]['messages'][1]


def test_missing_qwen_consensus_never_substitutes(tmp_path,monkeypatch):
    cfg,store,run,rows,chats = setup(tmp_path,monkeypatch)
    rows[:] = [r for r in rows if r['name']!='qwen3:14b-q4_K_M']
    with pytest.raises(ValueError,match='Exact consensus model'):
        asyncio.run(companion.submit(store,cfg,run,'consensus','second_opinion','Review','Evidence',consensus=True))
    assert not chats and not store.snapshot()['jobs']


def test_durable_routing_digest_change_prevents_generation(tmp_path,monkeypatch):
    cfg,store,run,rows,chats = setup(tmp_path,monkeypatch)
    jid = asyncio.run(companion.submit(store,cfg,run,'digest','analyze_code','Review','Evidence'))
    next(r for r in rows if r['name']=='gpt-oss:20b')['digest']='replaced'
    job = perform(store,jid)
    assert job['result']['answer']['_routing']['handoff_to_codex']
    assert not chats


def test_workflow_finalization_requires_checkpoint_even_after_result_reviews(tmp_path,monkeypatch):
    cfg,store,run,rows,chats = setup(tmp_path,monkeypatch)
    perform(store,asyncio.run(adapter.submit_workflow(store,cfg,run,'pending',task())))
    event = store.snapshot()['events'][0]
    store.decide(event['id'],'accepted','Inspected first stage only',local=True)
    assert store.claim_event() is None
    with pytest.raises(ValueError,match='workflow checkpoints'):
        store.finalize(run,'Only the first stage finished',True)
    assert store.finalize(run,'Explicit partial report',False)=='blocked'


@pytest.mark.parametrize('role,skill',[(r.id,s) for r in Catalog(AgenticConfig()).roles.values() for s in r.skills])
def test_every_declared_role_skill_is_executable_through_project_catalog(tmp_path,monkeypatch,role,skill):
    cfg,store,run,rows,chats = setup(tmp_path,monkeypatch)
    catalog = tmp_path/'catalog'
    (catalog/'workflows').mkdir(parents=True)
    (catalog/'project-profiles').mkdir()
    (catalog/'workflows/probe.toml').write_text(
        'id="probe"\ndescription="Exercise one declared role/skill"\ntask_kinds=["review_change"]\n'
        '[[stages]]\nid="probe"\nrole='+json.dumps(role)+'\nskills=['+json.dumps(skill)+']\n'
        '[[stages]]\nid="decide"\nexecutor="codex"\ncheckpoint="decision"\n')
    (catalog/'project-profiles/probe.toml').write_text('id="probe"\ndescription="Explicit supported profile"\nworkflows=["probe"]\n')
    cfg = replace(cfg,agentic=AgenticConfig(enabled=True,catalog_root=str(catalog),project_profile='probe'))
    job = perform(store,asyncio.run(adapter.submit_workflow(store,cfg,run,'probe',task())))
    answer = job['result']['answer']
    assert answer['workflow']['state']=='ready',answer
    assert answer['workflow']['next_stage']=='decide'
    assert answer['handoffs'][0]['skill_id']==skill
    assert bool(chats)==(skill!='repository-discovery')


def test_durable_budget_handoff_is_not_discarded_or_reset(tmp_path,monkeypatch):
    cfg,store,run,rows,chats = setup(tmp_path,monkeypatch)
    from localagentbridge.catalog import Limits
    cfg = replace(cfg,agentic=AgenticConfig(enabled=True,limits=Limits(max_attempts=1)))
    first = perform(store,asyncio.run(adapter.submit_workflow(store,cfg,run,'limited',task())))
    job = perform(store,adapter.follow_workflow(store,first['id']))
    state = job['result']['answer']['workflow']
    assert state['state']=='handed_off' and state['budget']['attempts']==1
    assert job['result']['answer']['handoffs'][-1]['payload']['_routing']['reason']=='workflow_attempt_budget'
    assert len(chats)==1


def test_durable_tampered_handoff_rejected_before_next_model_call(tmp_path,monkeypatch):
    cfg,store,run,rows,chats = setup(tmp_path,monkeypatch)
    first = perform(store,asyncio.run(adapter.submit_workflow(store,cfg,run,'tamper',task())))
    jid = adapter.follow_workflow(store,first['id'])
    request = store.job(jid)['request']
    request['handoffs'][0]['payload']['changed']='untrusted modification'
    with store.db() as db:
        db.execute('UPDATE jobs SET request=? WHERE id=?',(json.dumps(request),jid))
    claimed = store.claim_job({})
    asyncio.run(companion.execute(store,claimed))
    assert store.job(jid)['state']=='failed' and 'Handoff does not match' in store.job(jid)['error']
    assert len(chats)==1


def test_exact_qwen_second_opinion_overrides_preference_without_substitution(tmp_path,monkeypatch):
    from localagentbridge.bridge import Bridge
    value = {'verdict':'support','reasons':['Exact opinion'],'checks':[],'confidence':'high'}
    cfg,store,run,rows,chats = setup(tmp_path,monkeypatch,answer=value)
    monkeypatch.setattr(companion,'discover',adapter.discover)
    transport = adapter.Service(cfg).bridge.transport
    monkeypatch.setattr(companion,'Bridge',lambda c:Bridge(c,transport))
    jid = asyncio.run(companion.submit(store,cfg,run,'exact-qwen','second_opinion',
        'Review proposal','Supplied evidence',model='qwen3:14b-q4_K_M'))
    perform(store,jid)
    assert len(chats)==1 and chats[0]['model']=='qwen3:14b-q4_K_M'
    assert chats[0]['think'] is False


def test_local_review_cannot_bypass_uncertain_delivery(tmp_path,monkeypatch):
    cfg,store,run,rows,chats = setup(tmp_path,monkeypatch)
    perform(store,asyncio.run(companion.submit(store,cfg,run,'review','analyze_code','Review','Evidence')))
    event = store.snapshot()['events'][0]
    with store.db() as db:
        db.execute("UPDATE events SET state='uncertain' WHERE id=?",(event['id'],))
    with pytest.raises(ValueError,match='Reconcile'):
        store.decide(event['id'],'accepted','Cannot skip reconciliation',local=True)
