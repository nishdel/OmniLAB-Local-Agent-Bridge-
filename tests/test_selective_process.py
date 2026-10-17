"""Real detached process + local mock HTTP server. No live LLM or Docker claim."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import subprocess
import sys
import threading
import time

from localagentbridge.companion_store import CompanionStore
from localagentbridge.task_store import TaskStore
from test_selective_contracts import contract, request
from test_selective_integration import repo


def test_contract_worker_survives_launcher_exit(tmp_path):
    root,revision=repo(tmp_path/'repo')
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args): pass
        def respond(self,payload,ndjson=False):
            data=(json.dumps(payload)+('\n' if ndjson else '')).encode()
            self.send_response(200); self.send_header('Content-Type','application/json')
            self.send_header('Content-Length',str(len(data))); self.end_headers(); self.wfile.write(data)
        def do_GET(self):
            self.respond({'models':[]} if self.path=='/api/ps' else {'models':[{'name':'exact:tag','digest':'weights'}]})
        def do_POST(self):
            self.rfile.read(int(self.headers['Content-Length']))
            if self.path=='/api/show':
                self.respond({'capabilities':['completion'],'model_info':{'x.context_length':32768}})
            else:
                # Gives the short-lived launcher time to exit before inference completes.
                time.sleep(.2)
                answer={'behavior':'mock bounded finding','findings':[],'uncertainties':[],
                        'recommended_tests':[],'confidence':'medium'}
                self.respond({'done':True,'message':{'content':json.dumps(answer)},
                              'prompt_eval_count':1,'eval_count':2},True)
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=threading.Thread(target=server.serve_forever,daemon=True); thread.start()
    try:
        c=contract(Path(root),base_revision=revision,requested_lane='local_advisory')
        req=request(c); req['policy']['providers']={'ollama':{'endpoint':f'http://127.0.0.1:{server.server_port}'}}
        store=CompanionStore(tmp_path/'state'); run=store.create_run(root,revision)
        jid=TaskStore(store).submit_many(run,[req])[0]
        script="from localagentbridge.companion import ensure_worker; from localagentbridge.companion_store import CompanionStore; import sys; ensure_worker(CompanionStore(sys.argv[1]))"
        result=subprocess.run([sys.executable,'-c',script,str(store.directory)],
            cwd=Path(__file__).resolve().parents[1],capture_output=True,timeout=15)
        assert result.returncode==0,result.stderr
        deadline=time.monotonic()+20
        while store.job(jid)['state'] in ('queued','running') and time.monotonic()<deadline:
            time.sleep(.05)
        job=store.job(jid)
        assert job['state']=='succeeded',job['error']
        assert job['process']['pid'] and job['result']['usage']['output_tokens']==2
        assert TaskStore(store).get(jid)['review_status']=='awaiting_review'
        assert store.claim_job({}) is None
    finally:
        server.shutdown(); server.server_close()


def test_restart_reconciles_reservation_after_saved_completion(tmp_path):
    from localagentbridge.companion import worker
    from test_selective_contracts import setup, finish_candidate
    store, run, jid = setup(tmp_path)
    job = store.claim_job({})
    tasks = TaskStore(store)
    tasks.reserve(job)
    finish_candidate(store,job,{'changes':{}})
    before = store.job(jid)
    worker(store.directory)
    after = store.job(jid)
    assert after['state']==before['state']
    assert after['attempt_id']==before['attempt_id']
    assert store.snapshot()['inference_reservation']['state']=='cancellation_pending'
    tasks.reconcile_resource(jid,'Test controller confirmed owned provider termination')
    assert store.snapshot()['inference_reservation'] is None
