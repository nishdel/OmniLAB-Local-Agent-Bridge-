from localagentbridge.usage_report import aggregate, operating_savings, investment
from localagentbridge.telemetry import Store
from localagentbridge.companion_store import CompanionStore

def test_missing_subset_and_negative_savings():
    result=aggregate([{'input_tokens':10,'cached_input_tokens':6,'output_tokens':None}])
    assert result['tokens']['input_tokens']['total']==10
    assert result['tokens']['output_tokens']['total'] is None
    assert operating_savings(100,150,equivalent=True,complete=True,evidence='paired')['net_cloud_tokens_avoided']==-50
    assert operating_savings(100,150,equivalent=True,complete=True,evidence='paired')['reduction_percent']==-50
    assert operating_savings(0,2,equivalent=True,complete=True,evidence='paired')['reduction_percent'] is None
    assert operating_savings(10,2)['status']=='not established'

def test_existing_usage_dedup_and_scope(tmp_path):
    c=CompanionStore(tmp_path);s=Store(c.directory/'usage')
    for source,total in [('rollout',100),('otel',100)]:
        s.usage(id=source,source=source,session_id='session',model='cloud',started=5,total_tokens=total,input_tokens=90,output_tokens=10)
    s.usage(id='local',source='local',session_id='run',model='local',tool='contract:ollama',started=6,status='error')
    s.usage(id='local',source='local',session_id='run',model='local',started=6,total_tokens=900)
    s.usage(id='old',source='rollout',session_id='session',model='cloud',started=1,total_tokens=200)
    report=investment(c,since=2,cutoff=10,session_ids=['session'])
    assert len(report['records'])==2
    cloud=next(r for r in report['groups'] if r['backend']=='codex')
    assert cloud['tokens']['total_tokens']['total']==100
    local=next(r for r in report['groups'] if r['backend']=='ollama')
    assert local['tokens']['total_tokens']['total'] is None

def test_cache_write_and_turn_ids_are_not_added(tmp_path):
    from localagentbridge.codex_usage import RolloutReader
    from types import SimpleNamespace
    s=Store(tmp_path);r=RolloutReader(SimpleNamespace(),s);state={'session':'session','model':'cloud','activity':'turn','started':1791590400}
    value={'input_tokens':20,'cached_input_tokens':4,'cache_write_input_tokens':3,'output_tokens':5,'reasoning_output_tokens':2,'total_tokens':25}
    event={'timestamp':'2026-10-10T00:00:00Z','type':'event_msg','payload':{'type':'token_count','info':{'total_token_usage':value,'last_token_usage':value}}}
    r.ingest(event,state,'one');r.ingest(event,state,'duplicate')
    with s.connect() as db:rows=list(db.execute('SELECT * FROM usage'))
    assert len(rows)==1 and rows[0]['total_tokens']==25
    assert rows[0]['cache_write_input_tokens']==3 and rows[0]['logical_id']=='turn'

def test_inherited_counter_without_last_response_is_unknown(tmp_path):
    from localagentbridge.codex_usage import RolloutReader
    from types import SimpleNamespace
    store=Store(tmp_path);reader=RolloutReader(SimpleNamespace(),store);state={'session':'child'}
    reader.ingest({'timestamp':'2026-10-10T00:00:00Z','type':'event_msg','payload':{'type':'token_count',
        'info':{'total_token_usage':{'input_tokens':1000,'output_tokens':100,'total_tokens':1100}}}},state,'inherited')
    with store.connect() as db:
        assert db.execute('SELECT COUNT(*) FROM usage').fetchone()[0]==0
    assert state['total']['total_tokens']==1100
