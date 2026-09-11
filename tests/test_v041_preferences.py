import asyncio
import json
from dataclasses import replace
from pathlib import Path

import httpx
import pytest

from localagentbridge.bridge import Bridge
from localagentbridge.config import Config, load_config
from localagentbridge.dashboard_state import snapshot, tier_text
from localagentbridge.models import AdaptiveConfig, ModelProfile
from test_bridge import SUMMARY, wire
from test_v3_adaptive import fake


def config(tmp_path, cap='Large'):
    return Config(data_dir=tmp_path, roles=dict(general='tiny', coding='quality', reasoning='fallback'),
        adaptive=AdaptiveConfig(enabled=True, default_cap=cap, memory_budget_gb=16,
                                preferred_model='quality', lightweight_model='tiny'),
        model_registry=[
            ModelProfile('tiny','dense',4,['general'],weight_gb=2.3,enabled=True,min_tier='Light'),
            ModelProfile('fallback','dense',14,['general','coding','reasoning'],weight_gb=8.7,
                         strength=4,enabled=True,min_tier='Medium'),
            ModelProfile('quality','moe',21,['general','coding','reasoning'],active_parameters_b=3.6,
                         weight_gb=12.85,strength=5,enabled=True,min_tier='Large',thinking='low')])


@pytest.mark.parametrize('cap,size,expected', [
    ('Light',2000,'tiny'),('Medium',100,'tiny'),('Medium',2000,'fallback'),
    ('Large',100,'tiny'),('Large',600,'tiny'),('Large',2000,'quality'),
    ('Maximum',100,'tiny'),('Maximum',600,'quality')])
def test_preferences_change_order_without_changing_cap(tmp_path,cap,size,expected):
    cfg,chats=config(tmp_path,cap),[]
    result=asyncio.run(Bridge(cfg,fake(cfg,chats)).analyze('summarize_context','x'*size))
    assert [c['model'] for c in chats]==[expected]
    assert not result['_routing']['handoff_to_codex']
    assert chats[0]['think']==('low' if expected=='quality' else False)


@pytest.mark.parametrize('cap,expected',[('Light',None),('Medium','fallback'),('Large','quality'),('Maximum','quality')])
def test_short_code_analysis_is_substantive(tmp_path,cap,expected):
    cfg,chats=config(tmp_path,cap),[]
    answer=dict(behavior='Division',findings=['Empty input divides by zero.'],uncertainties=[],recommended_tests=[],confidence='high')
    result=asyncio.run(Bridge(cfg,fake(cfg,chats,[answer])).analyze('analyze_code','def avg(xs): return sum(xs)/len(xs)'))
    assert [c['model'] for c in chats]==([expected] if expected else [])
    assert result['_routing']['handoff_to_codex']==(expected is None)


def test_preference_cannot_bypass_resources_quality_or_attempt_limit(tmp_path):
    cfg,chats=config(tmp_path),[]
    cfg.adaptive.memory_budget_gb=12
    bridge=Bridge(cfg,fake(cfg,chats))
    asyncio.run(bridge.analyze('summarize_context','x'*2000))
    assert chats[-1]['model']=='fallback'
    with bridge.store.connect() as db:
        assert 'memory_budget' in db.execute('SELECT selection_reason FROM usage').fetchone()[0]
    cfg.adaptive.memory_budget_gb=16
    cfg.model_registry[-1].reliability={'summarize_context':dict(reviewed_cases=3,accepted_rate=0,rejected_rate=1)}
    asyncio.run(bridge.analyze('summarize_context','x'*2000))
    assert chats[-1]['model']=='fallback'
    cfg.model_registry[-1].reliability={}
    bridge=Bridge(cfg,fake(cfg,chats,[{'bad':'schema'}]))
    result=asyncio.run(bridge.analyze('summarize_context','x'*2000))
    assert chats[-1]['model']=='quality' and result['_routing']['handoff_to_codex']
    assert len(result['_routing']['attempts'])==1  # Never downgrade after a failed quality result.


def test_stronger_and_moderate_select_quality_but_complex_hands_off(tmp_path):
    cfg,chats=config(tmp_path),[]
    bridge=Bridge(cfg,fake(cfg,chats))
    for hints in [dict(stronger=True),dict(complexity='moderate')]:
        asyncio.run(bridge.analyze('summarize_context','short',routing=hints))
        assert chats[-1]['model']=='quality'
    result=asyncio.run(bridge.analyze('summarize_context','short',routing={'complexity':'complex'}))
    assert len(chats)==2 and result['_routing']['handoff_to_codex']


def test_profile_controls_thinking_and_only_final_content_is_validated(tmp_path):
    cfg=config(tmp_path)
    bodies=[]
    def handler(request):
        if request.url.path=='/api/tags':
            return httpx.Response(200,json={'models':[{'name':p.name} for p in cfg.model_registry]})
        bodies.append(json.loads(request.content))
        prefix=json.dumps({'message':{'thinking':'private trace, not JSON','content':''},'done':False})+'\n'
        return httpx.Response(200,content=prefix.encode()+wire(SUMMARY))
    bridge=Bridge(cfg,httpx.MockTransport(handler))
    result=asyncio.run(bridge.analyze('summarize_context','x'*2000))
    assert bodies[0]['think']=='low' and isinstance(bodies[0]['format'],dict)
    assert 'private trace' not in json.dumps(result)
    assert b'private trace' not in (tmp_path/'usage.sqlite3').read_bytes()


def test_missing_quality_is_reported_without_substitution(tmp_path):
    cfg,chats=config(tmp_path),[]
    result=asyncio.run(Bridge(cfg,fake(cfg,chats,missing=['quality'])).analyze('summarize_context','x'*2000))
    assert not chats and 'ollama pull quality' in result['_routing']['reason']


def test_triage_preserves_caller_complexity_in_routing_facts(tmp_path,monkeypatch):
    from localagentbridge.service import Service
    service=Service(config(tmp_path))
    captured=[]
    async def analyze(*args,**kwargs):
        captured.append(kwargs['routing'])
        return {'delegation':'delegate_analysis'}
    monkeypatch.setattr(service.bridge,'analyze',analyze)
    asyncio.run(service.triage('Inspect bounded behavior',2000,3,complexity='moderate'))
    assert captured==[{'complexity':'moderate'}]


def test_portable_profiles_and_dashboard_describe_actual_selection(tmp_path):
    root=Path(__file__).resolve().parents[1]
    starter=load_config(root/'config.example.toml')
    assert len(starter.model_registry)==1 and len(set(starter.roles.values()))==1
    for filename in ('balanced.toml','quality.toml'):
        assert load_config(root/'profiles'/filename).adaptive.enabled
    cfg=config(tmp_path)
    from localagentbridge.telemetry import Store
    rows=snapshot(cfg,Store(tmp_path),'Large',{p.name+':latest':{} for p in cfg.model_registry})
    text=tier_text(rows,'Large',cfg.adaptive)
    assert 'prefer quality when eligible' in text and '1200' in text and 'tiny' in text
    with pytest.raises(ValueError,match='two distinct enabled'):
        replace(cfg,adaptive=replace(cfg.adaptive,preferred_model='unregistered'))
