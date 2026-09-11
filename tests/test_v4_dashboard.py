from dataclasses import replace
import asyncio
import os
import time
import tomllib
import httpx
import pytest
from localagentbridge.config import Config, load_config
from localagentbridge.models import ModelProfile, AdaptiveConfig, task_eligibility
from localagentbridge.dashboard_state import snapshot, tier_text, compression_text, model_text, activity_text
from localagentbridge.telemetry import Store, Recorder
from localagentbridge.setup import codex_config, doctor


def cfg(tmp_path):
    return Config(data_dir=tmp_path, otel_port=0, model_registry=[
        ModelProfile('small:4b','dense',4,['general'],weight_gb=2.3,enabled=True,min_tier='Light'),
        ModelProfile('mid:9b','dense',9,['general','coding'],weight_gb=6,enabled=True,min_tier='Medium'),
        ModelProfile('large:14b','dense',14,['coding'],weight_gb=9,enabled=True,min_tier='Large'),
        ModelProfile('moe:20b','moe',20,['reasoning'],active_parameters_b=3,weight_gb=13,
                     enabled=True,min_tier='Maximum',experimental=True),
        ModelProfile('old:7b','dense',7,['coding'],weight_gb=4,disabled_reason='Failed reviewed quality gate')],
        adaptive=AdaptiveConfig(memory_budget_gb=20))


def test_shared_tiers_missing_disabled_and_quality(tmp_path):
    config=cfg(tmp_path)
    store=Store(tmp_path)
    installed={p.name:{} for p in config.model_registry}
    expected={'Light':['small:4b'], 'Medium':['small:4b','mid:9b'],
              'Large':['small:4b','mid:9b','large:14b'], 'Maximum':['small:4b','mid:9b','large:14b','moe:20b']}
    for tier,names in expected.items():
        rows=snapshot(config,store,tier,installed)
        assert [r['profile'].name for r in rows if r['eligible']]==names
        assert all(n in tier_text(rows,tier) for n in names)
        assert 'Failed reviewed quality gate' in model_text(rows[-1],{},store.compression('old:7b'))
    installed.pop('large:14b')
    assert not snapshot(config,store,'Large',installed)[2]['eligible']
    assert not snapshot(config,store,'Large',None)[0]['eligible']
    p=replace(config.model_registry[1],reliability={'analyze_code':dict(reviewed_cases=3,accepted_rate=0,rejected_rate=1)})
    assert task_eligibility(p,config.adaptive,'Medium',{},'analyze_code')==(False,'benchmark_reliability')
    assert task_eligibility(p,config.adaptive,'Medium',{},'summarize_context')[0]
    config.model_registry.append(ModelProfile('embedding:4b','dense',4,[],weight_gb=2,capabilities=['embedding'],enabled=True))
    installed['embedding:4b']={}
    assert not snapshot(config,store,'Maximum',installed)[-1]['eligible']
    assert 'allowed by cap (0 eligible)' in tier_text([], 'Maximum')


def test_grouped_dashboard_metrics_match_router_queries(tmp_path):
    store=Store(tmp_path)
    store.usage(id='one',source='local',session_id='one',model='model',started=0,
                duration=4,output_tokens=30,generation_seconds=2)
    store.report([dict(request_id='one',outcome='corrected')])
    with store.connect() as db:
        db.execute('INSERT INTO benchmark_reviews VALUES (?,?,?,?,?,?,?,?,?,?)',
                   ('one','run','case','analyze_code','model','corrected',0,1,0,0))
    store.checkpoint('model-measurement:model',dict(model_memory_gb=5))
    grouped=store.registry_metrics()
    for tool in (None,'analyze_code'):
        assert all(grouped['model',tool][key]==value for key,value in store.model_metrics('model',tool).items())


def test_generic_thinking_configuration_does_not_override_frozen_protocol(tmp_path):
    from test_v3_adaptive import config, fake
    from test_bridge import SUMMARY
    from localagentbridge.bridge import Bridge
    cfg=config(tmp_path)
    cfg.model_registry[0].thinking='low'
    calls=[]
    bridge=Bridge(cfg,fake(cfg,calls))
    asyncio.run(bridge.analyze('summarize_context','evidence'))
    assert calls[-1]['think']=='low'
    template=calls[-1] | {'think':False}
    bridge.request_template=template
    asyncio.run(bridge.analyze('summarize_context','evidence'))
    assert calls[-1]['think'] is False


def test_router_records_actual_quality_gate_fact(tmp_path):
    from test_v3_adaptive import config, fake
    from localagentbridge.bridge import Bridge
    cfg=config(tmp_path)
    bridge=Bridge(cfg,fake(cfg,[]))
    asyncio.run(bridge.analyze('summarize_context','evidence'))
    assert 'insufficient quality evidence: 0/3 reviewed' in bridge.store.recent_routes(1)[0]['selection_reason']
    model=cfg.model_registry[0].name
    with bridge.store.connect() as db:
        for i in range(3):
            db.execute('INSERT INTO benchmark_reviews VALUES (?,?,?,?,?,?,?,?,?,?)',
                       (str(i),'run',str(i),'summarize_context',model,'accepted',0,0,0,0))
    asyncio.run(bridge.analyze('summarize_context','evidence'))
    assert 'quality gate passed: 3 reviewed, 100% accepted, 0% rejected' in bridge.store.recent_routes(1)[0]['selection_reason']


def test_final_payload_compression_counts_escalated_task_once(tmp_path):
    store=Store(tmp_path)
    for i,model in enumerate(('small','large')):
        store.usage(id=str(i),source='local',session_id=str(i),model=model,started=i,
                    logical_id='task',source_bytes=1000,output_bytes=200)
    store.route_result('task',1000,350,False,'verified later')
    result=store.compression()
    assert result['final_tasks']['reduction']==.65
    assert result['final_tasks']['potential_bytes']==650
    assert result['individual_outputs']['calls']==0
    assert store.compression('small')['final_tasks']['calls']==0
    assert store.compression('large')['final_tasks']['calls']==1
    store.route_result('task',1000,1200,True,'expanded')
    assert store.compression()['final_tasks']['potential_bytes']==0
    assert '1,200 returned bytes' in compression_text(store.compression())


def test_routing_activity_persists_facts_without_evidence(tmp_path):
    store=Store(tmp_path)
    record=Recorder(store,'analyze_code','large',100,role='coding',route_cap='Large',
                    escalated_from='small',escalation_reason='invalid_result',selection_reason='Role coding; cap Large')
    row=store.active()[0]
    text=activity_text(row,time.time())
    assert 'Role: coding' in text and 'Task: analyze_code' in text and 'invalid_result' in text
    assert 'selection_reason' in row and 'content' not in row
    record.finish({},0,'error')


def test_setup_snippet_and_doctor(tmp_path):
    config=cfg(tmp_path)
    path=tmp_path/'with spaces.toml'
    path.write_text('model="small:4b"')
    config.codex_home=tmp_path/'codex'
    snippet=tomllib.loads(codex_config(config,path))['mcp_servers']['localagentbridge']
    assert str(path) in snippet['args'] and snippet['tool_timeout_sec']==390
    transport=httpx.MockTransport(lambda request:httpx.Response(200,json={'models':[{'name':'small:4b'}]}))
    checks=asyncio.run(doctor(config,path,transport))
    assert any(r['check']=='Model mid:9b' and r['detail']=='ollama pull mid:9b (no substitute)' for r in checks)
    assert any(r['check']=='Codex registration' and r['status']=='warning' for r in checks)


@pytest.mark.skipif(os.name!='nt',reason='Native Windows dashboard')
def test_first_fixed_failure_popup_and_local_activity_priority(tmp_path):
    import tkinter as tk
    from localagentbridge.dashboard import RegistryDashboard
    config=cfg(tmp_path)
    store=Store(tmp_path)
    root=tk.Tk()
    ui=RegistryDashboard(root,config,store)
    ui.poll_inventory=lambda:None
    shown=[]
    ui.show=lambda manual=False:shown.append(True)
    try:
        ui.options['popup_failure'].set(True)
        ui.refresh()  # Baseline: do not replay historical failures at startup.
        now=time.time()
        for i in range(2):
            store.activity('cloud-'+str(i),'rollout','cloud-'+str(i),'Cloud',now-100,now)
        store.activity('local','local','local','small:4b',now,now,role='general',tool='summarize_context')
        store.usage(id='failed-fixed',source='local',session_id='failed-fixed',model='small:4b',started=now,status='error')
        ui.refresh()
        assert 'LOCAL / OLLAMA' in ui.status.get() and 'Role: general' in ui.status.get()
        assert shown==[True]
        ui.refresh()
        assert shown==[True]  # Failure popup does not repeat on each poll.
    finally:
        ui.closed=True
        root.destroy()


@pytest.mark.skipif(os.name!='nt',reason='Native Windows dashboard')
@pytest.mark.parametrize('scaling',[1.3333,1.6667,2.0])
def test_native_caps_cards_fresh_missing_and_settings(tmp_path, scaling):
    import tkinter as tk
    from localagentbridge.dashboard import RegistryDashboard
    config=cfg(tmp_path)
    store=Store(tmp_path)
    root=tk.Tk()
    root.tk.call('tk','scaling',scaling)
    ui=RegistryDashboard(root,config,store)
    ui.poll_inventory=lambda:None
    ui.installed={'small:4b':{},'large:14b':{}}
    try:
        ui.set_cap('Medium')
        assert not ui.rows[2]['eligible']
        ui.set_cap('Large')
        assert ui.rows[2]['eligible'] and 'large:14b' in ui.feedback.get()
        ui.model_choice.set('old:7b')
        ui.refresh_card()
        assert 'Failed reviewed quality gate' in ui.card.get('1.0','end')
        ui.refresh()
        root.update_idletasks()
        assert tuple(ui.table['columns'])==('model','time','tokens')
        assert '× LOCAL' in ui.table.item('Local:old:7b')['values'][0]
        assert '◌ LOCAL' in ui.table.item('Local:mid:9b')['values'][0]
        ui.installed['extra:3b']={'details':{'parameter_size':'3B'},'size':1000}
        ui.update_eligibility()
        ui.model_choice.set('extra:3b')
        ui.refresh_card()
        assert 'Registered: no' in ui.card.get('1.0','end')
        assert not ui.options['popup_activity'].get()
        ui.options['always_on_top'].set(True)
        ui.delay.set(22)
        ui.save_settings()
        assert store.checkpoint('widget-settings')['collapse_seconds']==22
        assert root.attributes('-topmost')
        ui.show(manual=True)
        root.update_idletasks()
        assert ui.visibility.pinned
        ui.hide()
        assert root.state()=='withdrawn'
        import ctypes
        foreground=ctypes.windll.user32.GetForegroundWindow()
        ui.show()
        root.update_idletasks()
        hwnd=ctypes.windll.user32.GetParent(root.winfo_id())
        assert ctypes.windll.user32.IsWindowVisible(hwnd)
        assert ctypes.windll.user32.GetForegroundWindow()==foreground
        ui.hide()
    finally:
        ui.closed=True
        root.destroy()
