import os
import time
import pytest


@pytest.mark.skipif(os.name!='nt',reason='Windows native Tk test')
def test_v3_cap_details_and_escalation(tmp_path):
    import tkinter as tk
    from localagentbridge.config import Config
    from localagentbridge.models import ModelProfile
    from localagentbridge.telemetry import Store
    from localagentbridge.widget import Dashboard
    cfg=Config(data_dir=tmp_path,model_registry=[ModelProfile('qwen-test','dense',4,['general'],weight_gb=2.3)])
    root=tk.Tk()
    store=Store(tmp_path)
    now=time.time()
    store.usage(id='test',source='local',session_id='test',model='qwen-test',started=now,
                total_tokens=120,output_tokens=20,duration=3,generation_seconds=2,source_bytes=1000,output_bytes=200)
    store.activity('test','local','test','qwen-test',now,status='generating',output_tokens=20,
                   role='general',escalated_from='previous:3b',escalation_reason='contradictory_evidence')
    dashboard=Dashboard(root,cfg,store)
    dashboard.visibility.had_activity=True
    try:
        dashboard.refresh()
        assert tuple(dashboard.table['columns'])==('model','time','tokens')
        assert 'Role: general' in dashboard.status.get()
        assert 'contradictory_evidence' in dashboard.status.get()
        dashboard.cap.set('Large')
        dashboard.set_cap()
        assert Store(tmp_path).compute_cap()=='Large'
        Store(tmp_path).compute_cap(value='Light')
        dashboard.refresh()
        assert dashboard.cap.get()=='Light'
        dashboard.toggle_details()
        dashboard.refresh()
        root.update_idletasks()
        card=dashboard.card.get('1.0','end')
        assert 'Architecture: dense' in card and 'total: 4B' in card and 'Quantization: unknown' in card
        assert 'Calls: 1' in card and '10.0 tok/s' in card and '80.0%' in card
        dashboard.commands.put('cap:Maximum')
        dashboard.refresh()
        assert Store(tmp_path).compute_cap()=='Maximum'
        dashboard.toggle_details()
        assert not dashboard.details_open
    finally:
        dashboard.closed=True
        root.destroy()
