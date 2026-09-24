import asyncio
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import subprocess
import sys
import time
import uuid

import httpx
import pytest

from localagentbridge.callbacks import classify, command, dispatch
from localagentbridge.companion_store import CompanionStore
from localagentbridge.config import Config
from localagentbridge.dock import presentation
from localagentbridge.selection import discover, select_model, SelectionError
from localagentbridge.selection import remote_model


# Corrected local GPT-OSS proposal: public import and untruncated test body.
def test_select_valid_completion():
    rows=[{'name':'modelA','remote':False,'capabilities':['completion']}]
    assert select_model(rows,'modelA')==rows[0]


def test_select_capabilities_none_allowed():
    rows=[{'name':'modelC','remote':False,'capabilities':None}]
    assert select_model(rows,'modelC')==rows[0]


@pytest.mark.parametrize('tag,show,expected',[({}, {},False),({'remote_host':'host'}, {},True),({}, {'remote_model':'name'},True),({'remote_model':''},{'remote_host':None},False)])
def test_local_agent_remote_helper(tag,show,expected):
    assert remote_model(tag,show) is expected


@pytest.mark.parametrize('rows,name', [([], 'missing'),
    ([{'name':'custom','remote':True,'capabilities':['completion']}],'custom'),
    ([{'name':'embed','remote':False,'capabilities':['embedding']}],'embed')])
def test_selection_never_substitutes(rows,name):
    with pytest.raises(SelectionError):
        select_model(rows,name)


def test_inventory_reads_show_remote_metadata_and_preserves_custom_tags(tmp_path):
    calls=[]
    def handler(request):
        calls.append(request.url.path)
        if request.url.path=='/api/tags':
            return httpx.Response(200,json={'models':[{'name':'custom:tag','digest':'one','size':42},{'name':'remote:tag','digest':'two'}]})
        name=json.loads(request.content)['model']
        return httpx.Response(200,json={'capabilities':['completion'],'remote_host':'cloud.invalid' if name=='remote:tag' else ''})
    rows=asyncio.run(discover(Config(data_dir=tmp_path),httpx.MockTransport(handler)))
    assert select_model(rows,'custom:tag')['digest']=='one'
    assert rows[0]['validation']=='untested'
    with pytest.raises(SelectionError): select_model(rows,'remote:tag')
    assert calls==['/api/tags','/api/show','/api/show']


@pytest.mark.parametrize('payload',[{}, {'models':None}, {'models':[{'name':'bad;name'}]}])
def test_invalid_inventory(tmp_path,payload):
    with pytest.raises(SelectionError):
        asyncio.run(discover(Config(data_dir=tmp_path),httpx.MockTransport(lambda req:httpx.Response(200,json=payload))))


@pytest.mark.parametrize('error',[httpx.ConnectError('offline'),httpx.ReadTimeout('lost')])
def test_inventory_offline_is_visible(tmp_path,error):
    def fail(request): raise error
    with pytest.raises(httpx.HTTPError):
        asyncio.run(discover(Config(data_dir=tmp_path),httpx.MockTransport(fail)))


def setup_run(tmp_path,clock=lambda:100):
    store=CompanionStore(tmp_path/'state',clock)
    run=store.create_run(tmp_path,'base',str(uuid.uuid4()))
    return store,run


def completed(store,run,key='one'):
    jid=store.submit(run,key,{'tool':'analyze_code','objective':key,'selection':{'name':'custom','digest':'hash'}})
    job=store.claim_job({'pid':999,'created':10})
    assert job['id']==jid
    store.complete(jid,job['attempt_id'],{'answer':{},'usage':{'input_tokens':4,'output_tokens':5}})
    return job


def test_duplicate_submission_and_completion_are_atomic(tmp_path):
    store,run=setup_run(tmp_path)
    with ThreadPoolExecutor(4) as pool:
        ids=list(pool.map(lambda _:store.submit(run,'same',{'content':'bounded'}),range(8)))
    assert len(set(ids))==1
    with pytest.raises(ValueError): store.submit(run,'same',{'content':'different'})
    job=store.claim_job({})
    with ThreadPoolExecutor(4) as pool:
        results=list(pool.map(lambda _:store.complete(job['id'],job['attempt_id'],{'result':'persisted'}),range(8)))
    assert sum(results)==1
    snapshot=CompanionStore(store.directory).snapshot()
    assert len(snapshot['events'])==1 and snapshot['jobs'][0]['result']=={'result':'persisted'}


def test_busy_session_and_simultaneous_review_claims(tmp_path):
    store,run=setup_run(tmp_path)
    completed(store,run,'one'); completed(store,run,'two')
    with ThreadPoolExecutor(4) as pool:
        events=list(pool.map(lambda _:store.claim_event(),range(4)))
    claimed=[e for e in events if e]
    assert len(claimed)==1
    event=claimed[0]
    store.delivery(event['id'],event['delivery_id'],'awaiting_decision')
    assert store.claim_event() is None
    store.decide(event['id'],'accepted','Verified test passed')
    assert store.claim_event()['job_id']!=event['job_id']


def test_controller_restart_uncertain_delivery_never_replays(tmp_path):
    store,run=setup_run(tmp_path)
    completed(store,run)
    event=store.claim_event()
    restarted=CompanionStore(store.directory)
    restarted.recover_deliveries()
    assert restarted.snapshot()['events'][0]['state']=='uncertain'
    assert restarted.claim_event() is None
    with pytest.raises(ValueError): restarted.decide(event['id'],'accepted','guess')
    restarted.reconcile(event['id'],'not_delivered','Inspected artifacts: launch failed before dispatch')
    assert restarted.claim_event()['delivery_id']!=event['delivery_id']


def test_uncertain_initialization_blocks_callbacks_until_inspected(tmp_path):
    store,run=setup_run(tmp_path)
    completed(store,run)
    store.setting('session_init:'+run,'uncertain')
    assert store.claim_event() is None
    store.reconcile_session(run,'Reviewed initialization event and verified the CLI is no longer active')
    assert store.claim_event()


def test_simulated_seven_days_quota_reset_and_six_hour_execution(tmp_path):
    now=[100.0]
    store,run=setup_run(tmp_path,lambda:now[0])
    store.submit(run,'slow',{})
    job=store.claim_job({})
    now[0]+=6*3600
    assert store.job(job['id'])['state']=='running'
    store.complete(job['id'],job['attempt_id'],{})
    event=store.claim_event()
    reset=now[0]+7*86400
    store.delivery(event['id'],event['delivery_id'],'retry','quota_exhausted',reset)
    now[0]+=5*3600
    assert store.claim_event() is None
    now[0]=reset
    assert store.claim_event()


@pytest.mark.parametrize('code,expected',[('authentication_error','blocked'),('network_error','retry'),('usage_limit_reached','retry'),('unknown','uncertain')])
def test_callback_availability_metadata(code,expected):
    events=[{'type':'turn.failed','error':{'code':code,'resets_at':999999}}]
    assert classify(1,events)[0]==expected
    assert classify(None,[{'type':'turn.started'}])[0]=='uncertain'


def test_quota_without_reset_requires_recovery_and_missing_usage_is_unknown():
    assert classify(1,[{'type':'turn.failed','error':{'code':'quota_exhausted'}}])[:3]==('blocked','quota_exhausted',None)
    assert classify(0,[{'type':'turn.completed'}])[3] is None


def test_pause_cancel_and_worker_failure_not_success(tmp_path):
    store,run=setup_run(tmp_path)
    first=store.submit(run,'first',{})
    second=store.submit(run,'second',{})
    store.setting('paused',True)
    assert store.claim_job({}) is None
    store.setting('paused',False)
    job=store.claim_job({})
    store.cancel(run)
    store.complete(job['id'],job['attempt_id'],{'answer':'late'})
    assert {j['state'] for j in store.snapshot()['jobs']}=={'cancelled'}
    assert {e['job_id'] for e in store.snapshot()['events']}=={first,second}
    with pytest.raises(ValueError): store.finalize(run,'unreviewed',True)


def test_finalization_deduplicated_after_review_and_validation(tmp_path):
    store,run=setup_run(tmp_path)
    completed(store,run)
    event=store.claim_event()
    store.delivery(event['id'],event['delivery_id'],'awaiting_decision')
    with pytest.raises(ValueError): store.finalize(run,'premature',True)
    store.decide(event['id'],'accepted','Validated result and ran regression suite')
    assert store.finalize(run,'Verified final report',True)=='completed'
    assert store.finalize(run,'duplicate attempt',True)=='completed'
    assert store.snapshot()['runs'][0]['summary']=='Verified final report'
    with pytest.raises(ValueError): store.submit(run,'late',{})


def test_failure_review_finalizes_blocked(tmp_path):
    store,run=setup_run(tmp_path)
    jid=store.submit(run,'broken',{})
    job=store.claim_job({})
    store.complete(jid,job['attempt_id'],state='failed',error='worker failure')
    event=store.claim_event()
    store.delivery(event['id'],event['delivery_id'],'awaiting_decision')
    store.decide(event['id'],'rejected','Observed worker failure')
    assert store.finalize(run,'Blocked by failed work',False)=='blocked'


def test_callback_exact_id_and_restricted_command(tmp_path):
    session=str(uuid.uuid4())
    argv=command(sys.executable,str(tmp_path),tmp_path/'out',session)
    assert argv[argv.index('resume')+1]==session
    assert '--last' not in argv and '--ephemeral' not in argv
    assert argv[argv.index('--sandbox')+1]=='read-only'
    assert argv[argv.index('-a')+1]=='never'


def test_missing_repository_blocks_dispatch_without_invoke(tmp_path,monkeypatch):
    store,run=setup_run(tmp_path)
    completed(store,run)
    event=store.claim_event()
    from localagentbridge import callbacks
    monkeypatch.setattr(callbacks,'invoke',lambda *a:pytest.fail('must not dispatch'))
    dispatch(store,event,sys.executable)
    assert store.snapshot()['events'][0]['state']=='uncertain'


def test_dock_reports_unknown_usage_and_cancellation_controls(tmp_path):
    store,run=setup_run(tmp_path)
    completed(store,run)
    view=presentation(store.snapshot())
    assert 'Local in 4 / out 5' in view['title']
    assert 'Codex reported usage: unavailable' in view['details']
    store.submit(run,'pending',{'selection':{'name':'next'}})
    assert 'Local in unavailable' in presentation(store.snapshot())['title']


def test_public_no_deadline_cancels_and_retains_connection_timeout(tmp_path):
    from localagentbridge.bridge import Bridge
    class Waiting(httpx.AsyncByteStream):
        async def __aiter__(self):
            await asyncio.sleep(3600)
            yield b''
    async def test():
        cfg=Config(data_dir=tmp_path,no_inference_deadline=True)
        task=asyncio.create_task(Bridge(cfg,httpx.MockTransport(lambda req:httpx.Response(200,stream=Waiting()))).analyze('analyze_code','bounded'))
        await asyncio.sleep(.05)
        assert not task.done()
        task.cancel()
        with pytest.raises(asyncio.CancelledError): await task
    asyncio.run(test())


def test_actual_worker_survives_launcher_and_completion_survives_restart(tmp_path):
    from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
    import threading
    from localagentbridge.companion import git_identity
    root=Path(__file__).resolve().parents[1]
    repository,base=git_identity(root)
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*a): pass
        def do_GET(self):
            self.reply({'models':[{'name':'fixture:latest','digest':'fixed'}]})
        def reply(self,value):
            raw=json.dumps(value).encode()+b'\n'
            self.send_response(200);self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
        def do_POST(self):
            self.rfile.read(int(self.headers['Content-Length']))
            if self.path=='/api/show': return self.reply({'capabilities':['completion']})
            time.sleep(.4)
            self.reply({'message':{'content':json.dumps({'behavior':'fixture','findings':[],'uncertainties':[],'recommended_tests':[],'confidence':'high'})},'done':True,'prompt_eval_count':8,'eval_count':9})
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    threading.Thread(target=server.serve_forever,daemon=True).start()
    store=CompanionStore(tmp_path/'state')
    run=store.create_run(repository,base)
    store.submit(run,'independent',dict(tool='analyze_code',objective='fixture',content='fixture evidence',selection={'name':'fixture:latest','digest':'fixed'},endpoint=f'http://127.0.0.1:{server.server_port}',timeout_seconds=None,max_input_chars=10000,max_output_tokens=600,max_output_bytes=3000,num_ctx=8192,thinking=False))
    try:
        launcher=subprocess.run([sys.executable,'-B','-c',
            'from localagentbridge.companion import serve; import sys; serve(sys.argv[1],once=True)',str(store.directory)],cwd=root,capture_output=True,text=True,timeout=20)
        assert launcher.returncode==0,launcher.stderr
        until=time.monotonic()+25
        while time.monotonic()<until:
            snap=store.snapshot()
            if snap['events']: break
            time.sleep(.1)
        assert snap['jobs'][0]['state']=='succeeded',snap
        restarted=CompanionStore(store.directory)
        assert restarted.snapshot()['jobs'][0]['result']['usage']['input_tokens']==8
        assert restarted.snapshot()['events'][0]['state']=='pending'
    finally:
        server.shutdown();server.server_close()


def test_database_upgrade_and_future_version_guard(tmp_path):
    import sqlite3
    from localagentbridge.telemetry import Store
    old=Store(tmp_path)
    old.activity('historical','local','session','old',1,1,'complete')
    before=(tmp_path/'usage.sqlite3').read_bytes()
    CompanionStore(tmp_path/'companion')
    assert (tmp_path/'usage.sqlite3').read_bytes()==before
    path=tmp_path/'companion/companion.sqlite3'
    with sqlite3.connect(path) as db: db.execute('PRAGMA user_version=99')
    with pytest.raises(ValueError,match='newer'): CompanionStore(path.parent)


@pytest.mark.skipif(sys.platform!='win32',reason='Native Tk dock')
def test_native_companion_dock_is_only_a_client(tmp_path,monkeypatch):
    import tkinter as tk
    from localagentbridge import dock
    async def inventory(config):
        return [{'name':'custom:tag','remote':False,'capabilities':['completion'],'validation':'untested','size':1024,'details':{}}]
    monkeypatch.setattr(dock,'discover',inventory)
    store,run=setup_run(tmp_path)
    store.submit(run,'queued',{'selection':{'name':'custom:tag'}})
    root=tk.Tk()
    panel=dock.CompanionDock(root,Config(data_dir=tmp_path),store)
    try:
        panel.refresh();root.update()
        panel.pause()
        assert store.setting('paused')
        panel.toggle();root.update()
        assert panel.details.winfo_ismapped()
        panel.hide();root.update()
        assert root.state()=='withdrawn'
        assert store.snapshot()['jobs'][0]['state']=='queued'
        panel.cancel_run()
        assert store.snapshot()['jobs'][0]['state']=='cancelled'
        assert not (store.directory/'controller.lock').exists()
    finally:
        panel.closed=True
        root.destroy()
