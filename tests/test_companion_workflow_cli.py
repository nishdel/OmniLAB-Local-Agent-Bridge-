"""Actual CLI + detached worker processes, deterministic loopback Ollama."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time

from test_v05_workflows import ANSWERS


def test_workflow_commands_across_detached_worker_restarts(tmp_path):
    root = Path(__file__).resolve().parents[1]
    repository = tmp_path/'repository'
    repository.mkdir()
    # Own a disposable repository; do not depend on the candidate checkout's
    # Windows owner or an extracted sdist having Git metadata.
    subprocess.run(['git','init',str(repository)],check=True,capture_output=True)
    subprocess.run(['git','-C',str(repository),'-c','user.name=Fixture','-c',
        'user.email=fixture@example.invalid','commit','--allow-empty','-m','Fixture base'],
        check=True,capture_output=True)
    chats = []
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*_): pass
        def send(self,payload):
            raw = json.dumps(payload).encode()+b'\n'
            self.send_response(200)
            self.send_header('Content-Length',str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
        def do_GET(self):
            self.send({'models':[{'name':'qwen3:4b','digest':'fixture'}]})
        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            if self.path=='/api/show':
                self.send({'capabilities':['completion']})
            else:
                chats.append(body)
                self.send({'message':{'content':json.dumps(ANSWERS[body['format']['title']])},
                    'done':True,'prompt_eval_count':42,'eval_count':12})
    server = ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread = threading.Thread(target=server.serve_forever,daemon=True)
    thread.start()
    config = tmp_path/'config.toml'
    text = (root/'examples/v0.5/minimal.toml').read_text()
    text = text.replace('source_root = "../.."','source_root = '+json.dumps(repository.as_posix()))
    text = text.replace('data_dir = "../../data/v05-example"','data_dir = "history"')
    text = text.replace('http://localhost:11434',f'http://127.0.0.1:{server.server_port}')
    config.write_text(text)
    env = {k:v for k,v in os.environ.items() if not k.startswith('LAB_')}
    def cli(*args):
        result = subprocess.run([sys.executable,'-B','-m','localagentbridge','--config',str(config),
            'companion',*args],cwd=root,env=env,capture_output=True,text=True,timeout=30)
        assert result.returncode==0,result.stderr
        return json.loads(result.stdout) if result.stdout.strip() else None
    from localagentbridge.companion_store import CompanionStore
    store = CompanionStore(tmp_path/'history/companion')
    def run_job(job_id):
        cli('controller','--once')
        deadline = time.monotonic()+30
        while time.monotonic()<deadline:
            job = store.job(job_id)
            if job['state'] in ('succeeded','failed','interrupted'):
                assert job['state']=='succeeded',job['error']
                return job
            time.sleep(.05)
        raise AssertionError('Detached CLI worker did not finish')
    try:
        run = cli('create')['run_id']
        request = tmp_path/'task.json'
        request.write_text(json.dumps({'task_key':'cli-workflow','task':{
            'task_id':'cli-workflow','kind':'review_change','objective':'Review helper',
            'context':'Pure helper','diff':'+return value','test_output':'1 passed',
            'validation_status':'passed','delegation':{'mode':'direct'}}}))
        submitted = cli('workflow-submit','--run',run,'--request',str(request))['job_id']
        assert cli('workflow-submit','--run',run,'--request',str(request))['job_id']==submitted
        job = run_job(submitted)
        assert cli('workflow-status','--job',submitted)['next_stage']=='decide'
        job = run_job(cli('workflow-next','--job',submitted)['job_id'])
        assert job['result']['answer']['workflow']['state']=='waiting_for_codex'
        checkpoint = tmp_path/'checkpoint.json'
        checkpoint.write_text(json.dumps({'checkpoint':{'action':'accept','note':'Synthetic test supervisor decision'}}))
        final = run_job(cli('workflow-checkpoint','--job',job['id'],'--request',str(checkpoint))['job_id'])
        assert final['result']['answer']['workflow']['state']=='codex_verified'
        for event in store.snapshot(run)['events']:
            cli('decide','--event',event['id'],'--outcome','accepted','--validation','Synthetic provider/CLI test','--local')
        assert cli('finalize','--run',run,'--summary','Synthetic CLI validation','--validation-passed')['state']=='completed'
        assert len(chats)==1
        assert store.snapshot(run)['runs'][0]['session_id'] is None
    finally:
        server.shutdown()
        server.server_close()
