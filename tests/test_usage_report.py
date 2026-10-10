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


def test_whole_session_and_run_include_all_attempts_and_future_rows(tmp_path):
    from localagentbridge.usage_report import bind_usage
    c=CompanionStore(tmp_path);s=Store(c.directory/'usage')
    bind_usage(c,kind='cloud',session_id='supervisor',run_id='work',task_id='task',
               category='operating',evidence='Isolated supervisor session from planning through review')
    bind_usage(c,kind='local',session_id='local-run',run_id='work',task_id='task',
               category='operating',evidence='LAB run includes failed first attempt and retry')
    for ident,source,session,total in [('plan','rollout','supervisor',12),('repair','rollout','supervisor',8),
                                       ('failed','local','local-run',None),('retry','local','local-run',20)]:
        s.usage(id=ident,source=source,session_id=session,model=source,started=3,total_tokens=total)
    report=investment(c,cutoff=4)
    assert report['categories']['operating']['cloud']['tokens']['total_tokens']['total']==20
    local=report['categories']['operating']['local']['tokens']['total_tokens']
    assert local['total'] is None and local['known_total']==20 and local['missing_records']==1
    assert {r['attribution']['run_id'] for r in report['records']}=={'work'}
    assert {r['kind'] for r in report['runs']}=={'cloud','local'}


def test_whole_turns_separate_investment_evaluation_and_unattributed(tmp_path):
    from localagentbridge.usage_report import bind_usage
    c=CompanionStore(tmp_path);s=Store(c.directory/'usage')
    for turn,category in [('setup','implementation'),('controller','evaluation')]:
        bind_usage(c,kind='cloud',session_id='shared',logical_id=turn,run_id='milestone',
                   category=category,evidence='Complete identified turn, no fractional allocation')
    for turn in ('setup','controller','unbound'):
        s.usage(id=turn,source='rollout',session_id='shared',logical_id=turn,model='cloud',
                started=5,input_tokens=10,cached_input_tokens=6,output_tokens=2,total_tokens=12)
    report=investment(c,cutoff=6)
    for category in ('implementation','evaluation','unattributed'):
        totals=report['categories'][category]['cloud']['tokens']
        assert totals['total_tokens']['total']==12 and totals['cached_input_tokens']['total']==6
    assert report['categories']['operating']['cloud']['records']==0
    assert report['categories']['operating']['cloud']['tokens']['total_tokens']['total'] is None


def test_attribution_is_idempotent_conflict_safe_and_nonoverlapping(tmp_path):
    import pytest
    from localagentbridge.usage_report import bind_usage
    c=CompanionStore(tmp_path)
    args=dict(kind='cloud',session_id='s',logical_id='turn',run_id='run',
              category='implementation',evidence='whole turn')
    assert bind_usage(c,**args)==bind_usage(c,**args)
    for changes in ({'category':'operating'},{'run_id':'different'},{'logical_id':None},
                    {'evidence':''},{'logical_id':''},{'category':'invented'}):
        with pytest.raises(ValueError):bind_usage(c,**(args|changes))
    bind_usage(c,**(args|{'session_id':'whole','logical_id':None}))
    with pytest.raises(ValueError):bind_usage(c,**(args|{'session_id':'whole'}))
    # Separate domains cannot accidentally label a cloud session as a local run.
    bind_usage(c,**(args|{'kind':'local','logical_id':None}))


def test_attribution_does_not_override_stream_dedup_or_invent_turn_ids(tmp_path):
    from localagentbridge.usage_report import bind_usage
    c=CompanionStore(tmp_path);s=Store(c.directory/'usage')
    bind_usage(c,kind='cloud',session_id='s',logical_id='t',run_id='r',
               category='operating',evidence='whole exact rollout turn')
    for source,turn in [('rollout','t'),('otel',None)]:
        s.usage(id=source,source=source,session_id='s',logical_id=turn,model='cloud',started=1,total_tokens=10)
    report=investment(c,cutoff=2)
    assert len(report['records'])==1
    assert report['categories']['unattributed']['cloud']['tokens']['total_tokens']['total']==10


def test_bind_cli_and_old_usage_upgrade(tmp_path):
    import argparse,sqlite3
    from localagentbridge import selective_cli
    path=tmp_path/'usage';path.mkdir()
    db=sqlite3.connect(path/'usage.sqlite3')
    db.execute('CREATE TABLE checkpoints (id TEXT PRIMARY KEY,state TEXT NOT NULL)')
    db.execute("INSERT INTO checkpoints VALUES ('old','{}')");db.commit();db.close()
    c=CompanionStore(tmp_path); parser=argparse.ArgumentParser();selective_cli.add(parser.add_subparsers(dest='action'))
    args=parser.parse_args(['contract-usage-bind','--kind','local','--session','lab-run','--run','work',
                           '--category','evaluation','--evidence','retained evaluation'])
    assert selective_cli.run(args,None,c)['run_id']=='work'
    assert Store(path).checkpoint('old')=={}
