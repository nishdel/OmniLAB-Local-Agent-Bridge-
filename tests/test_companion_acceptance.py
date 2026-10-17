"""Focused process-boundary acceptance of durable workflow recovery.

Run from outside the checkout with the installed wheel and --import-mode=importlib.
Provider answers are synthetic. Crashes are real os._exit calls after commits.
The original failing expectations remain in companion_crash_baseline.py and can
be run explicitly against the pre-repair installed wheel. Unsaved output is not
recoverable; process termination is not proof of host power-loss durability.
"""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
import uuid

import pytest
import localagentbridge

from localagentbridge.companion_store import CompanionStore
from localagentbridge.companion_workflows import follow_workflow, service_for


CRASH_WORKER = r'''
import os, sys, inspect
from localagentbridge.companion import worker
from localagentbridge.companion_store import CompanionStore
from localagentbridge.workflow_store import WorkflowStore
from localagentbridge.workflow_recovery import RecoveryJournal
name, directory = sys.argv[1:]
if name == 'companion:apply_recovery:inside':
    from contextlib import contextmanager
    original_db = CompanionStore.db
    @contextmanager
    def interrupted_db(self):
        with original_db(self) as db:
            def trace(sql):
                if sql.startswith('INSERT') and 'INTO events' in sql: os._exit(91)
            db.set_trace_callback(trace)
            yield db
    CompanionStore.db = interrupted_db
elif name != 'none':
    owner, method, when = name.split(':')
    cls = {'companion':CompanionStore,'workflow':WorkflowStore,'journal':RecoveryJournal}[owner]
    original = getattr(cls, method)
    def interrupted(*args, **kwargs):
        if when == 'before': os._exit(91)
        result = original(*args, **kwargs)
        os._exit(91)
        return result
    setattr(cls, method, staticmethod(interrupted) if isinstance(inspect.getattr_static(cls,method),staticmethod) else interrupted)
worker(directory)
'''


@pytest.fixture
def candidate(tmp_path,monkeypatch):
    source = Path(__file__).resolve().parents[1]
    # Subprocesses use the same selected runtime as the test process. For package
    # checks this is site-packages; for development it is the isolated worktree.
    monkeypatch.setenv('PYTHONPATH',str(Path(localagentbridge.__file__).resolve().parents[1]))
    if subprocess.run(['git','-c','safe.directory='+source.as_posix(),
                      '-C',str(source),'rev-parse','--git-dir'],
                      capture_output=True).returncode:
        pytest.skip('Process acceptance needs a Git candidate checkout to clone')
    repository = tmp_path/'repository'
    subprocess.run(['git','clone','--quiet','--shared',str(source),str(repository)],
                   check=True,capture_output=True)
    chats = []
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*_): pass
        def send(self,value):
            raw = json.dumps(value).encode()+b'\n'
            self.send_response(200)
            self.send_header('Content-Length',str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
        def do_GET(self):
            self.send({'models':[{'name':'qwen3:4b','digest':'acceptance-fixture'}]})
        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            if self.path == '/api/show':
                self.send({'capabilities':['completion']})
                return
            chats.append(body)
            self.send({'message':{'content':json.dumps({'possible_bugs':[],
                'regressions':[],'suspicious_logic':[],'missing_tests':[], 'confidence':'high'})},
                'done':True,'prompt_eval_count':42,'eval_count':12})
    server = ThreadingHTTPServer(('127.0.0.1',0),Handler)
    threading.Thread(target=server.serve_forever,daemon=True).start()
    config = tmp_path/'config.toml'
    content = (source/'examples/v0.5/minimal.toml').read_text()
    content = content.replace('source_root = "../.."','source_root = '+json.dumps(repository.as_posix()))
    content = content.replace('data_dir = "../../data/v05-example"','data_dir = "history"')
    content = content.replace('http://localhost:11434',f'http://127.0.0.1:{server.server_port}')
    # This fixture tests committed crash boundaries, not four-second latency.
    # Windows file/SQLite work can consume that lease before the injected crash.
    # Expiry checks below still wait for the actual recorded lease; runtime
    # defaults and production resource/time budgets are unchanged.
    content = content.replace('timeout_seconds = 180','timeout_seconds = 15')
    config.write_text(content)
    env = {k:v for k,v in os.environ.items() if not k.startswith('LAB_')}
    def cli(*args):
        result = subprocess.run([sys.executable,'-B','-m','localagentbridge',
            '--config',str(config),'companion',*args],cwd=tmp_path,env=env,
            capture_output=True,text=True,timeout=30)
        assert result.returncode == 0, result.stderr
        return json.loads(result.stdout) if result.stdout.strip() else None
    store = CompanionStore(tmp_path/'history/companion')
    run = cli('create')['run_id']
    request = tmp_path/'task.json'
    request.write_text(json.dumps({'task_key':'recovery','task':{
        'task_id':'recovery','kind':'review_change','objective':'Review a fixture helper',
        'context':'Synthetic acceptance evidence','diff':'+return value',
        'test_output':'Synthetic validation','validation_status':'passed',
        'delegation':{'mode':'direct'}}}))
    job = cli('workflow-submit','--run',run,'--request',str(request))['job_id']
    def worker(point='none'):
        result = subprocess.run([sys.executable,'-B','-c',CRASH_WORKER,point,str(store.directory)],
            cwd=tmp_path,env=env,capture_output=True,text=True,timeout=30)
        assert result.returncode == (0 if point=='none' else 91), result.stderr
    try:
        yield store,run,job,worker,cli,chats,tmp_path,request
    finally:
        server.shutdown()
        server.server_close()


@pytest.mark.parametrize('point',[
    'companion:claim_job:before','companion:claim_job:after',
    'workflow:create:after','workflow:claim:after','workflow:reserve:after',
    'workflow:result:before','workflow:result:after','workflow:finish:after',
    'journal:payload:before','journal:payload:after',
    'journal:committed:before','journal:committed:after',
    'companion:apply_recovery:before','companion:apply_recovery:inside','companion:apply_recovery:after',
    'journal:acknowledge:before','journal:acknowledge:after',
])
def test_crash_boundaries_preserve_jobs_and_prevent_blind_replay(candidate,point):
    store,run,jid,worker,cli,chats,tmp_path,request = candidate
    worker(point)
    before = store.job(jid)
    count = len(chats)
    worker()
    worker()
    after = store.job(jid)
    completed = point in ('companion:claim_job:before','workflow:finish:after',
        'companion:apply_recovery:before','companion:apply_recovery:inside','companion:apply_recovery:after',
        'journal:acknowledge:before','journal:acknowledge:after')
    assert after['state'] == ('succeeded' if completed else 'interrupted')
    assert len(chats) == (1 if point=='companion:claim_job:before' else count)
    assert cli('workflow-submit','--run',run,'--request',str(request))['job_id'] == jid
    snapshot = store.snapshot(run)
    assert len(snapshot['jobs']) == len(snapshot['events']) == 1
    assert store.claim_event() is None  # No managed Codex session in this fixture.
    status = cli('workflow-status','--job',jid)
    engine = service_for(store,after).workflows
    # Wait for the real durable lease to expire; do not modify the database clock.
    with engine.ledger.store.connect() as db:
        lease = db.execute('SELECT expires FROM workflow_lease').fetchone()
    if lease:
        remaining = max(0,lease[0]-time.time())
        assert remaining < 10, remaining
        time.sleep(remaining+.05)
        status = cli('workflow-status','--job',jid)
        assert status['state'] == 'handed_off'
        assert status['reason'] == 'interrupted'
    if not completed:
        with pytest.raises(ValueError,match='interrupted/failed'):
            follow_workflow(store,jid)
        assert (after['result'] or {}).get('answer',{}).get('workflow',{}).get('state') != 'codex_verified'
    refs = []
    if status['state'] != 'not_started':
        with engine.ledger.store.connect() as db:
            refs = [dict(row) for row in db.execute('SELECT * FROM workflow_results')]
        if count or point=='workflow:reserve:after':
            assert status['budget']['attempts'] == 1
    saved = []
    with engine.ledger.store.connect() as db:
        if db.execute("SELECT 1 FROM sqlite_master WHERE name='companion_payloads'").fetchone():
            saved = [json.loads(r[0]) for r in db.execute('SELECT packet FROM companion_payloads WHERE operation_id=?',(jid,))]
    recovered = (after['result'] or {}).get('answer',{}).get('handoffs',[])
    assert recovered == saved
    assert all(p['payload']['possible_bugs']==[] for p in saved)
    lost = bool(refs) and not recovered
    assert not lost
    # Explicit supervisor rejection closes the companion as blocked; it cannot
    # manufacture missing packets or certify the interrupted workflow.
    if not completed:
        event = snapshot['events'][0]
        store.decide(event['id'],'rejected','Observed real forced process exit; no replay',local=True)
        assert store.finalize(run,'Interrupted acceptance fixture; preserve evidence',False)=='blocked'
    (tmp_path/'observation.json').write_text(json.dumps({
        'boundary':point,'before':before['state'],'after':after['state'],
        'provider_calls':len(chats),'jobs':1,'review_events':1,
        'workflow':status,'result_references':refs,'handoff_content_lost':lost,
        'successful_recovery':completed},indent=2))


@pytest.mark.parametrize('method',['wait_or_skip','checkpoint'])
def test_checkpoint_commit_window_is_reconciled_without_replaying_decision(candidate,method):
    store,run,jid,worker,cli,chats,tmp_path,_ = candidate
    worker()
    next_id = follow_workflow(store,jid)
    if method=='checkpoint':
        worker()
        next_id = follow_workflow(store,next_id,checkpoint={
            'action':'accept','note':'Synthetic supervisor decision'})
    worker('workflow:'+method+':after')
    worker()
    worker()
    assert store.job(next_id)['state']=='succeeded'
    state = cli('workflow-status','--job',next_id)
    assert state['state'] == ('waiting_for_codex' if method=='wait_or_skip' else 'codex_verified')
    assert len(chats)==1
    snap = store.snapshot(run)
    assert len(snap['jobs']) == len(snap['events']) == (2 if method=='wait_or_skip' else 3)
    result = store.job(next_id)['result']['answer']
    assert result['workflow']==state
    assert result['handoffs']==store.job(jid)['result']['answer']['handoffs']
    assert all(e['state']=='pending' for e in snap['events'])
    (tmp_path/'observation.json').write_text(json.dumps({
        'boundary':method,'companion_state':'succeeded','workflow':state,
        'jobs':len(snap['jobs']),'review_events':len(snap['events']),
        'provider_calls':len(chats),'checkpoint_replayed':False},indent=2))


def test_review_claim_crash_reconciliation_and_authentication_failure(candidate):
    from localagentbridge.callbacks import dispatch
    store,run,jid,worker,cli,chats,tmp_path,_ = candidate
    worker()
    session = str(uuid.UUID(int=1))
    store.bind_session(run,session)  # Synthetic identifier; never used with Codex.
    claim_code = 'from localagentbridge.companion_store import CompanionStore; import os,sys; s=CompanionStore(sys.argv[1]); s.claim_event(); os._exit(91)'
    process = subprocess.run([sys.executable,'-c',claim_code,str(store.directory)],cwd=tmp_path)
    assert process.returncode == 91
    for _ in range(2):
        cli('controller','--once')
        assert store.claim_event() is None
    event = store.snapshot(run)['events'][0]
    assert event['state']=='uncertain'
    store.reconcile(event['id'],'not_delivered','Fixture process exited before dispatch/invoke')
    claimed = store.claim_event()
    assert claimed and store.claim_event() is None
    # A real subprocess exercises file/stdio/argv handling; its response is an
    # explicit fixture, never a substitute for an authenticated Codex callback.
    script = tmp_path/'auth_failure.py'
    script.write_text('import json,sys\nsys.stdin.read()\nprint(json.dumps({"type":"turn.failed","error":{"code":"authentication_error"}}))\nsys.exit(1)\n')
    shim = tmp_path/'auth_failure.cmd'
    shim.write_text('@echo off\n"'+sys.executable+'" "'+str(script)+'" %*\n')
    dispatch(store,claimed,shim)
    event = store.snapshot(run)['events'][0]
    assert event['state']=='blocked' and event['reason']=='authentication_required'
    store.recover_deliveries()
    assert store.claim_event() is None
    with store.db() as db:
        deliveries = [dict(row) for row in db.execute('SELECT * FROM deliveries ORDER BY created')]
    assert len(deliveries)==2  # One unsent claim, one explicit reconciled attempt.
    packet_dir = Path(json.loads(deliveries[-1]['evidence'])['directory'])
    invocation = json.loads((packet_dir/'invocation.json').read_text())
    assert invocation['argv'][invocation['argv'].index('resume')+1]==session
    assert 'UNTRUSTED_EVIDENCE' in (packet_dir/'prompt.txt').read_text()
    assert store.job(jid)['result'] is not None
    (tmp_path/'observation.json').write_text(json.dumps({
        'review_events':1,'claims':2,'fixture_invocations':1,
        'automatic_replays':0,'authenticated_callback':False,
        'state':event['state'],'reason':event['reason']},indent=2))


def test_status_preserves_unicode_on_redirected_windows_stdout(candidate):
    store,run,jid,worker,cli,chats,tmp_path,_ = candidate
    worker()
    validation = 'Reviewed nonbreaking hyphen \u2011 and CJK \u754c evidence'
    store.decide(store.snapshot(run)['events'][0]['id'],'accepted',validation,local=True)
    code = ('import sys; sys.stdout.reconfigure(encoding="cp1252",errors="strict"); '
            'from localagentbridge.__main__ import main; main()')
    result = subprocess.run([sys.executable,'-B','-c',code,'--config',
        str(tmp_path/'config.toml'),'companion','status','--run',run],
        cwd=tmp_path,capture_output=True,timeout=30)
    assert result.returncode==0,result.stderr.decode(errors='replace')
    assert json.loads(result.stdout)['events'][0]['validation']==validation


@pytest.mark.parametrize('boundary',['before','after'])
def test_review_response_commit_crash_never_automatically_redelivers(candidate,boundary):
    store,run,jid,worker,cli,chats,tmp_path,_ = candidate
    worker()
    store.bind_session(run,str(uuid.UUID(int=1)))
    script=tmp_path/'review_fixture.py'
    script.write_text('import json,sys,pathlib\n'
        'sys.stdin.read()\n'
        'pathlib.Path(sys.argv[sys.argv.index("--output-last-message")+1]).write_text("Synthetic review only")\n'
        'print(json.dumps({"type":"turn.completed","usage":{"input_tokens":1,"output_tokens":1}}))\n')
    shim=tmp_path/'review_fixture.cmd'
    shim.write_text('@echo off\n"'+sys.executable+'" "'+str(script)+'" %*\n')
    code='''
import os,sys
from localagentbridge.callbacks import dispatch
from localagentbridge.companion_store import CompanionStore
store=CompanionStore(sys.argv[1])
original=store.delivery
def interrupted(*args,**kwargs):
    if sys.argv[3]=='before': os._exit(91)
    original(*args,**kwargs)
    os._exit(91)
store.delivery=interrupted
dispatch(store,store.claim_event(),sys.argv[2])
'''
    process=subprocess.run([sys.executable,'-B','-c',code,str(store.directory),str(shim),boundary],
        cwd=tmp_path,capture_output=True,timeout=30)
    assert process.returncode==91,process.stderr.decode(errors='replace')
    cli('controller','--once')
    cli('controller','--once')
    event=store.snapshot(run)['events'][0]
    assert event['state']==('uncertain' if boundary=='before' else 'awaiting_decision')
    assert store.claim_event() is None
    with store.db() as db:
        deliveries=[dict(r) for r in db.execute('SELECT * FROM deliveries')]
    assert len(deliveries)==1
    artifacts=list((store.directory/'reviews').rglob('response.txt'))
    assert len(artifacts)==1 and artifacts[0].read_text()=='Synthetic review only'
    if boundary=='before':
        store.reconcile(event['id'],'delivered','Inspected retained synthetic response and process exit')
    store.decide(event['id'],'accepted','Fixture delivery review only')
    assert store.claim_event() is None
    (tmp_path/'observation.json').write_text(json.dumps({
        'boundary':'delivery:'+boundary,'state_after_restart':event['state'],
        'review_events':1,'deliveries':1,'fixture_responses':1,
        'after_reconciliation':'reviewed','authenticated_callback':False},indent=2))
