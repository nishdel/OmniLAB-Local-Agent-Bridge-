"""In-process comparison transport/executor. Only benchmark_readiness mock uses it.

This intentionally returns unsuccessful implementation proposals. Verifier results
are synthetic; none of these receipts establishes independent model acceptance.
"""
import io
import json
from pathlib import Path
import tarfile
import time
import uuid
from unittest.mock import patch

import httpx

from localagentbridge.companion_store import CompanionStore
from localagentbridge.config import Config
from localagentbridge.selective import prepare, execute
from localagentbridge.task_contract import digest
from localagentbridge.task_store import TaskStore
from localagentbridge.telemetry import Store
from localagentbridge.usage_report import bind_usage, investment


class Sandbox:
    image = 'sha256:'+'0'*64

    def __init__(self, *a):
        self.rows = {}

    def preflight(self):
        return True

    def inspect(self, name, owner):
        if name not in self.rows:
            raise RuntimeError('No such container')
        r = self.rows[name]
        return {'State':{'Running':r['running'], 'Status':'running' if r['running'] else 'exited', 'ExitCode':0}}

    def create(self, name, owner, contract, mode='agent'):
        self.rows[name] = dict(contract=contract, mode=mode, running=False, request=str(uuid.uuid4()))

    def put(self, name, owner, raw):
        with tarfile.open(fileobj=io.BytesIO(raw)) as tar:
            self.rows[name]['files'] = {i.name[10:]:tar.extractfile(i).read() for i in tar
                                       if i.isfile() and i.name.startswith('workspace/')}

    def start(self, name, owner):
        self.rows[name]['running'] = self.rows[name]['mode'] == 'agent'

    def read(self, name, owner, path, *a):
        r = self.rows[name]
        if path == '/exchange/request.json':
            return {'id':r['request'], 'body':{'model':r['contract'].model, 'stream':False,
                'messages':[{'role':'user','content':'Synthetic mock proposal only'}], 'tools':[]}}
        if path == '/workspace/.':
            return r['files']
        if path == '/exchange/result.json':
            return {'checks':[dict(id=c.id, argv=c.argv, covers=c.covers, exit_code=1,
                timed_out=False, output_truncated=False, seconds=0.01,
                output='Synthetic rejection: mock edit does not satisfy independent acceptance')
                for c in r['contract'].checks]}
        raise AssertionError('Unknown mock path')

    def respond(self, name, owner, response):
        r = self.rows[name]
        r['files'][r['contract'].permitted_files[0]] += b'\n# Synthetic mock proposal only.\n'
        r['running'] = False

    def stop(self, name, owner):
        self.rows[name]['running'] = False
        return True


async def exercise(case, directory):
    directory.mkdir(parents=True)
    row = json.loads((Path(case['directory'])/'attempt-template.json').read_text())
    row['mode'] = 'mock'
    calls = []
    if case['arm'] == 'D':
        return row, {'records':[]}, calls
    row['accounting_run_id'] = case['key']
    store = CompanionStore(directory/'companion')
    run_id = store.create_run(case['repository'], case['base_revision'])
    began = time.time()
    if case['arm'] != 'A':
        contract = json.loads((Path(case['directory'])/'contract.json').read_text())[0]
        contract['supervisor_approved'] = True  # Synthetic admission, separate mock store only.
        def respond(request):
            calls.append(request.url.path)
            model, identity = contract['model'], contract['exact_identity']
            responses = {
                '/api/tags': {'models':[{'name':model,'digest':identity}]},
                '/api/show': {'capabilities':['completion','tools'], 'model_info':{'mock.context_length':65536}},
                '/api/ps': {'models':[{'name':model,'digest':identity,'context_length':65536}]},
                '/api/chat': {'done':True, 'done_reason':'stop', 'message':{'role':'assistant','content':'Synthetic mock response; not a fixture solution'},
                              'prompt_eval_count':11, 'eval_count':7}}
            if request.url.path not in responses:
                raise AssertionError('Unexpected mock provider path '+request.url.path)
            return httpx.Response(200, json=responses[request.url.path])
        transport = httpx.MockTransport(respond)
        proof = dict(kind='openhands_roundtrip', verification_status='passed', tool_result_messages=1,
                     tools_called=['terminal','file_editor'], backend='ollama', identity=contract['exact_identity'],
                     context_tokens=65536, image=Sandbox.image, sdk_version='1.53.0')
        proof_path = directory/'synthetic-qualification.json'
        proof_path.write_text(json.dumps(proof))
        import hashlib
        config = Config(data_dir=directory/'data', thinking=False, selective=dict(
            enabled=True, implementation_enabled=True,
            providers={'ollama':{'enabled':True,'endpoint':'http://localhost:11434','native_context':True}},
            qualified=[['ollama',contract['exact_identity'],contract['category'],65536]],
            capability_evidence=[proof | dict(path=str(proof_path), sha256=hashlib.sha256(proof_path.read_bytes()).hexdigest(),
                                             supervisor_accepted=True)],
            sandbox={'image':Sandbox.image}, memory_plan=dict(supervisor_verified=True,
                os_and_apps_mb=1,lab_mb=1,runtime_mb=1,context_cache_mb=1,headroom_mb=1)))
        with patch('localagentbridge.selective.DockerSandbox', Sandbox):
            prepared = await prepare(config, [contract], transport)
        assert prepared[0]['routing']['effective_lane'] == contract['requested_lane'], prepared[0]['routing']
        task_id = TaskStore(store).submit_many(run_id, prepared)[0]
        job = store.claim_job({})
        await execute(store, job, transport=transport, sandbox_factory=Sandbox)
        state = TaskStore(store).get(task_id)
        assert store.job(task_id)['state'] == 'succeeded', store.job(task_id)['error']
        assert state['accepted_hash'] is None
        event = store.snapshot(run_id)['events'][0]
        TaskStore(store).review(event['id'], 'rejected', 'Synthetic mock response is not an accepted solution',
                                state['candidate_hash'], {})
        bind_usage(store, kind='local', session_id=run_id, run_id=case['key'], category='evaluation',
                   evidence='Synthetic mock receipts only; all attempts in this mock run', task_id=case['fixture'])
    # Actual store APIs, explicitly synthetic cloud counters; no cloud process/API.
    session = 'mock-supervisor-'+case['key']
    Store(store.directory/'usage').usage(id=session, source='rollout', session_id=session,
        model='mock-supervisor', started=began, input_tokens=100, cached_input_tokens=10,
        output_tokens=20, reasoning_output_tokens=5, total_tokens=120, status='ok')
    bind_usage(store, kind='cloud', session_id=session, run_id=case['key'], category='evaluation',
               evidence='Synthetic complete-unit mock binding; not measured cloud usage', task_id=case['fixture'])
    usage = investment(store)
    row.update(admission={'status':'admitted','reason':'Mock transport only'}, outcome='rejected',
               failure_class='synthetic_quality_rejection', first_pass_accepted=False,
               end_to_end_seconds=time.time()-began, usage_report_sha256=digest(usage),
               notes=['Mock protocol and accounting exercise, not a live model result'])
    return row, usage, calls
