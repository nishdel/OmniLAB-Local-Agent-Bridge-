import asyncio
from dataclasses import replace
import json
import time
import uuid
import httpx
import pytest
from localagentbridge.adaptive import AdaptiveRouter
from localagentbridge.bridge import Bridge
from localagentbridge.config import Config
from localagentbridge.models import AdaptiveConfig, ModelProfile, eligibility
from localagentbridge.schemas import compact
from localagentbridge.service import Service
from localagentbridge.telemetry import Store
from test_bridge import SUMMARY, wire


def profile(name='small:4b', architecture='dense', total=4, active=None, weight=2.3, strength=1, enabled=True):
    return ModelProfile(name,architecture,total,['general','coding','reasoning'],active,weight_gb=weight,strength=strength,enabled=enabled)


def config(tmp_path, **policy):
    return Config(data_dir=tmp_path,roles=dict(general='small:4b',coding='coder:7b',reasoning='small:4b'),
        model_registry=[profile(),profile('coder:7b',total=7.6,weight=4.4,strength=2),
                        profile('dense:14b',total=14.8,weight=8.7,strength=3)],
        adaptive=AdaptiveConfig(enabled=True,**policy))


def fake(cfg, chats, answers=None, on_chat=None, missing=()):
    def handler(request):
        if request.url.path=='/api/tags':
            return httpx.Response(200,json={'models':[{'name':p.name} for p in cfg.model_registry if p.name not in missing]})
        body = json.loads(request.content)
        chats.append(body)
        if on_chat:
            on_chat(len(chats))
        answer = answers[min(len(chats)-1,len(answers)-1)] if answers else SUMMARY
        return httpx.Response(200,content=wire(answer))
    return httpx.MockTransport(handler)


def test_moe_compute_is_active_but_memory_is_full_weight():
    moe = profile('moe:30b','moe',30,3,19)
    policy = AdaptiveConfig(memory_budget_gb=24)
    assert eligibility(moe,policy,'Light') == (False,'memory_budget')
    assert eligibility(moe,policy,'Medium') == (False,'memory_budget')
    assert eligibility(moe,policy,'Large')[0]
    assert eligibility(replace(moe,active_parameters_b=None),policy,'Large') == (False,'compute_cap')
    assert eligibility(profile('moe:16b','moe',16,2.4,8.3),policy,'Medium')[0]
    assert eligibility(profile('dense:14b',total=14.8,weight=8.7),policy,'Medium') == (False,'compute_cap')


def test_measured_memory_latency_and_global_memory_are_independent_gates():
    p = profile()
    cfg = AdaptiveConfig()
    assert eligibility(p,cfg,'Light',{'model_memory_gb':7}) == (False,'memory_budget')
    assert eligibility(p,cfg,'Light',{'average_latency':46}) == (False,'measured_latency')
    assert eligibility(p,cfg,'Maximum',{'model_memory_gb':13}) == (False,'memory_budget')


@pytest.mark.parametrize('cap',['Light','Medium','Large','Maximum'])
def test_ceiling_never_forces_larger_model(tmp_path,cap):
    cfg,chats = config(tmp_path),[]
    app = Bridge(cfg,fake(cfg,chats))
    app.store.compute_cap(value=cap)
    result = asyncio.run(app.analyze('summarize_context','evidence '*300))
    assert [b['model'] for b in chats] == ['small:4b']
    assert result['_routing']['cap']==cap and not result['_routing']['handoff_to_codex']
    assert len(compact(result).encode())<=cfg.max_output_bytes
    with app.store.connect() as db:
        row = db.execute('SELECT * FROM route_results').fetchone()
        assert row['returned_bytes']==len(compact(result).encode())
        assert row['source_bytes']==len(('evidence '*300).encode())


def test_cap_persists_and_reload_affects_next_request(tmp_path):
    cfg,chats=config(tmp_path),[]
    app=Bridge(cfg,fake(cfg,chats))
    Store(tmp_path).compute_cap(value='Light')
    result=asyncio.run(app.analyze('analyze_code','code',routing={'complexity':'moderate'}))
    assert not chats and result['_routing']['reason']=='compute_cap'
    Store(tmp_path).compute_cap(value='Medium')
    result=asyncio.run(app.analyze('summarize_context','code',routing={'complexity':'moderate'}))
    assert chats[-1]['model']=='coder:7b' and result['_routing']['cap']=='Medium'


def test_low_confidence_escalates_once_and_logs_reason(tmp_path):
    cfg,chats=config(tmp_path),[]
    low=dict(behavior='Unclear',findings=[],uncertainties=[],recommended_tests=[],confidence='low')
    app=Bridge(cfg,fake(cfg,chats,[low,low|{'confidence':'high'}]))
    result=asyncio.run(app.analyze('analyze_code','code',role='general'))
    assert [b['model'] for b in chats]==['small:4b','coder:7b']
    assert chats[0]['messages']==chats[1]['messages']
    assert result['_routing']['attempts'][1]['reason']=='low_confidence'
    with app.store.connect() as db:
        row=db.execute("SELECT * FROM usage WHERE model='coder:7b'").fetchone()
        assert row['escalated_from']=='small:4b' and row['escalation_reason']=='low_confidence'
        assert row['generation_seconds']==2 and row['tokens_per_second']==10


def test_invalid_answer_escalates_but_transport_and_missing_never_substitute(tmp_path):
    cfg,chats=config(tmp_path),[]
    app=Bridge(cfg,fake(cfg,chats,[{'invalid':'answer'},SUMMARY]))
    result=asyncio.run(app.analyze('summarize_context','evidence'))
    assert len(chats)==2 and result['_routing']['attempts'][1]['reason']=='invalid_result'
    chats.clear()
    app=Bridge(cfg,fake(cfg,chats,missing=['small:4b']))
    result=asyncio.run(app.analyze('summarize_context','evidence'))
    assert not chats and 'ollama pull small:4b' in result['_routing']['reason']
    assert result['_routing']['handoff_to_codex']


def test_lowering_cap_blocks_next_escalation(tmp_path):
    cfg,chats=config(tmp_path),[]
    cfg.adaptive.default_cap='Large'
    app=Bridge(cfg,fake(cfg,chats,[{'invalid':True}],on_chat=lambda n: Store(tmp_path).compute_cap(value='Light')))
    result=asyncio.run(app.analyze('summarize_context','evidence'))
    assert len(chats)==1 and result['_routing']['cap']=='Light'
    assert result['_routing']['reason']=='compute_cap'


def test_verified_failure_followup_honors_chain_attempt_limit(tmp_path):
    cfg,chats=config(tmp_path),[]
    app=Bridge(cfg,fake(cfg,chats))
    app.store.compute_cap(value='Large')
    first=asyncio.run(app.analyze('summarize_context','evidence'))
    second=asyncio.run(app.analyze('summarize_context','evidence',routing={'previous_request_id':first['_meta']['request_id'],'reason':'contradictory_evidence'}))
    third=asyncio.run(app.analyze('summarize_context','evidence',routing={'previous_request_id':second['_meta']['request_id'],'reason':'previous_attempt_failed'}))
    assert [b['model'] for b in chats]==['small:4b','coder:7b']
    assert third['_routing']['handoff_to_codex'] and third['_routing']['reason'].startswith('attempt_limit')
    assert first['_routing']['logical_id']==second['_routing']['logical_id']==third['_routing']['logical_id']


def test_three_attempt_limit_and_explicit_stronger(tmp_path):
    cfg,chats=config(tmp_path,max_attempts=3),[]
    app=Bridge(cfg,fake(cfg,chats,[{'bad':True}]))
    app.store.compute_cap(value='Large')
    result=asyncio.run(app.analyze('summarize_context','evidence'))
    assert [b['model'] for b in chats]==['small:4b','coder:7b','dense:14b']
    assert result['_routing']['handoff_to_codex']


def test_complex_tasks_and_opt_out_stop_without_unbounded_retry(tmp_path):
    cfg,chats=config(tmp_path),[]
    app=Bridge(cfg,fake(cfg,chats,[{'bad':True}]))
    result=asyncio.run(app.analyze('summarize_context','evidence',routing={'complexity':'complex'}))
    assert not chats and result['_routing']['handoff_to_codex']
    result=asyncio.run(app.analyze('summarize_context','evidence',routing={'auto_escalate':False}))
    assert len(chats)==1 and result['_routing']['reason']=='invalid_result'


def test_disabled_and_reviewed_unreliable_models_are_excluded(tmp_path):
    cfg=config(tmp_path)
    store=Store(tmp_path)
    cfg.model_registry[2].enabled=False
    with store.connect() as db:
        for _ in range(3):
            db.execute('INSERT INTO benchmark_reviews VALUES (?,?,?,?,?,?,?,?,?,?)',
                (str(uuid.uuid4()),'run','case','summarize_context','small:4b','rejected',1,0,0,0))
    candidates,blocked=AdaptiveRouter(cfg,store).candidates('general','summarize_context','Large')
    assert [p.name for p in candidates]==['coder:7b'] and 'benchmark_reliability' in blocked
    assert AdaptiveRouter(cfg,store).candidates('general','analyze_code','Large')[0][0].name=='small:4b'


def test_consensus_rechecks_cap_between_participants(tmp_path):
    cfg,chats=config(tmp_path),[]
    cfg.consensus_roles=['general','coding']
    opinion=dict(verdict='support',reasons=[],checks=[],confidence='high')
    service=Service(cfg,fake(cfg,chats,[opinion],on_chat=lambda n: Store(tmp_path).compute_cap(value='Light')))
    result=asyncio.run(service.second_opinion('Question','evidence',consensus=True))
    assert len(chats)==1 and result['stopped']=='consensus_cap_changed' and result['codex_decides']


def test_registry_rejects_ambiguous_names_and_dense_compute_understatement(tmp_path):
    with pytest.raises(ValueError,match='Dense'):
        profile(total=14,active=3)
    with pytest.raises(ValueError,match='Duplicate'):
        Config(data_dir=tmp_path,model_registry=[profile('model'),profile('model:latest')])
    with pytest.raises(ValueError,match='registered'):
        replace(config(tmp_path),roles=dict(general='unknown',coding='coder:7b',reasoning='small:4b'))


def test_verify_models_checks_exact_requested_model_instead_of_adaptive_candidate(tmp_path,monkeypatch):
    from localagentbridge import verify
    cfg,chats=config(tmp_path),[]
    cfg.roles['general']='coder:7b'
    async def statuses(config):
        return [dict(role='general',model='coder:7b',installed=True)]
    monkeypatch.setattr(verify,'model_status',statuses)
    monkeypatch.setattr(verify,'Bridge',lambda config:Bridge(config,fake(config,chats)))
    assert asyncio.run(verify.verify_models(cfg))
    assert [c['model'] for c in chats]==['coder:7b']


def test_throughput_does_not_divide_legacy_tokens_by_only_new_generation_time(tmp_path):
    store=Store(tmp_path)
    store.usage(id='old',source='local',session_id='old',model='small:4b',started=time.time(),output_tokens=1000,duration=50)
    store.usage(id='new',source='local',session_id='new',model='small:4b',started=time.time(),output_tokens=20,duration=4,generation_seconds=2)
    assert store.model_metrics('small:4b')['tokens_per_second']==10


def test_quality_gate_distinguishes_correctable_from_majority_wrong(tmp_path):
    cfg=config(tmp_path,min_accepted_rate=.25,max_rejected_rate=.5)
    store=Store(tmp_path)
    with store.connect() as db:
        for model,outcomes in [('small:4b',['accepted','rejected','rejected']),('coder:7b',['accepted','corrected','corrected'])]:
            for outcome in outcomes:
                db.execute('INSERT INTO benchmark_reviews VALUES (?,?,?,?,?,?,?,?,?,?)',
                    (str(uuid.uuid4()),'run','case','analyze_code',model,outcome,0,0,0,0))
    candidates,blocked=AdaptiveRouter(cfg,store).candidates('coding','analyze_code','Medium')
    assert [p.name for p in candidates]==['coder:7b'] and 'benchmark_reliability' in blocked


def test_registry_status_joins_metadata_without_enabling_or_substituting(tmp_path):
    from localagentbridge.models import registry_status
    cfg=config(tmp_path)
    cfg.model_registry[-1].enabled=False
    rows=asyncio.run(registry_status(cfg,fake(cfg,[],missing=['dense:14b'])))
    assert len(rows)==3
    dense=rows[-1]
    assert not dense['enabled'] and not dense['installed'] and not dense['resource_eligible']
    assert dense['install_command']=='ollama pull dense:14b'
    assert dense['active_parameters_b']==dense['total_parameters_b']==14.8
    assert dense['measurements']['calls']==0 and dense['measurements']['tokens_per_second'] is None
