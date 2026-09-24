"""Benchmark-only checks. No real model inference; real process tests are explicit."""
import asyncio
from dataclasses import replace
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import httpx
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
import qwen_benchmark as qb
import qwen_benchmark_io as io
from localagentbridge.config import Config, load_config
from localagentbridge.bridge import Bridge, BridgeError
from localagentbridge.telemetry import Store


class Delayed(httpx.AsyncByteStream):
    async def __aiter__(self):
        await asyncio.sleep(.035)
        yield (json.dumps({'message':{'thinking':'observe'}})+'\n').encode()
        await asyncio.sleep(.035)
        yield (json.dumps({'message':{'content':'{"behavior":"ok","findings":[],"uncertainties":[],"recommended_tests":[],"confidence":"high"}'}})+'\n').encode()
        await asyncio.sleep(.035)
        yield (json.dumps({'done':True,'done_reason':'stop','prompt_eval_count':7,'eval_count':8,
                          'eval_duration':100000000,'load_duration':123,'prompt_eval_duration':456})+'\n').encode()


def test_no_deadline_and_incremental_capture(tmp_path):
    async def run():
        async def handler(request):
            return httpx.Response(200, stream=Delayed())
        cfg = Config(data_dir=tmp_path/'history')
        cfg.timeout_seconds = .01  # Accelerated former-deadline fixture; no ten-minute sleeps.
        with pytest.raises(BridgeError, match='timed out'):
            await Bridge(cfg, httpx.MockTransport(handler)).analyze('analyze_code','x')
        seen = []
        transport = io.CaptureTransport(tmp_path/'wire', lambda value, path: seen.append(dict(value)), inner=httpx.MockTransport(handler))
        answer = await Bridge(qb.unlimited_bridge_config(cfg), transport).analyze('analyze_code','x')
        assert answer['behavior'] == 'ok'
        assert cfg.timeout_seconds == .01
        path = tmp_path/'wire/call-001'
        assert io.read(path/'transport.json')['timeouts']['read'] is None
        assert io.read(path/'transport.json')['timeouts']['connect'] == 5
        assert (path/'thinking.txt').read_text() == 'observe'
        assert len(seen) == 3 and seen[0]['thinking_chars'] == 7 and seen[0]['content_chars'] == 0
        assert io.read(path/'terminal.json')['eval_count'] == 8
        assert io.read(path/'stream-state.json')['final_event_received']
    asyncio.run(run())


def test_unlimited_lease_and_other_budgets(tmp_path):
    ledger = qb.UnlimitedLedger(Store(tmp_path))
    stage = {'id':'first','role':'planner'}
    limits = dict(max_seconds=.00001,max_attempts=1,max_corrections=0,max_reserved_tokens=9000,
                  max_output_tokens=600,max_input_chars=10000)
    run = ledger.create('task','id','catalog','snapshot',{'stages':[stage]},limits)
    owner, seconds = ledger.claim(run,0,stage,.00001)
    assert seconds is None
    time.sleep(.015)
    ledger.reserve(owner,'one','skill',qb.MODEL,50,8192,600,1,False)
    with pytest.raises(BridgeError, match='workflow_attempt_budget'):
        ledger.reserve(owner,'two','skill',qb.MODEL,50,8192,600,1,False)
    ledger.finish(owner,9000,'ready')
    assert ledger.read(run)['seconds'] == 9000


def test_lock_and_recovery(tmp_path):
    with io.Lock(tmp_path/'lock'):
        with pytest.raises(RuntimeError):
            with io.Lock(tmp_path/'lock'):
                pass
    state = {'worker':None,'cases':[{'state':'completed','attempts':[{'attempt_id':'done'}]},
        {'state':'running','attempts':[{'attempt_id':'partial'}]}]}
    qb.recover(state)
    assert state['cases'][0]['state'] == 'completed'
    assert state['cases'][1]['attempts'][0]['state'] == 'interrupted'
    assert state['cases'][1]['attempts'][0]['attempt_id'] == 'partial'


def test_resource_safety_is_not_high_ram_or_elapsed():
    current = {'system_ram':{'available':1},'commit':{'CommitTotal':20*2**30,'CommitLimit':40*2**30}}
    assert io.exhaustion(current,2**30) is None
    current['commit']['CommitTotal'] = current['commit']['CommitLimit']-1
    assert io.exhaustion(current,2**30)
    assert io.exhaustion({'system_ram':{'available':2**30}},1024)


def test_normal_configuration_unchanged(tmp_path):
    config = load_config(ROOT/'config.toml')
    assert config.adaptive.preferred_model == 'gpt-oss:20b'
    assert config.timeout_seconds == 180
    assert config.num_ctx == 8192 and config.max_output_tokens == 600
    assert config.routes['analyze_code'] == 'coding'
    with pytest.raises((TypeError,ValueError)):
        Config(data_dir=tmp_path,timeout_seconds=None)
    old = io.read(qb.PRIOR/'preflight/protected-source-hashes-before.json')
    assert all(io.sha(ROOT/name)==digest for name,digest in old.items())


def test_model_metadata_ignores_only_parameter_order():
    first={'modelfile':'FROM hash\nPARAMETER top_p 0.95\nPARAMETER draft_num_predict 4\n','template':'same','parameters':'top_p 0.95\ndraft_num_predict 4'}
    second={'modelfile':'FROM hash\nPARAMETER draft_num_predict 4\nPARAMETER top_p 0.95\n','template':'same','parameters':'draft_num_predict 4\ntop_p 0.95'}
    assert qb.same_model_metadata(first,second)
    second['template']='different'
    assert not qb.same_model_metadata(first,second)


def test_terminal_token_limit_is_execution_completion(tmp_path):
    wire=tmp_path/'wire/call-001'
    wire.mkdir(parents=True)
    io.atomic(wire/'terminal.json',{'done':True,'done_reason':'length','eval_count':600})
    assert qb.execution_outcome(tmp_path,{'cases':[{}]}) == ('completed',None)
    (wire/'terminal.json').unlink()
    assert qb.execution_outcome(tmp_path,{'cases':[{}]})[0] == 'failed'


def fixture_job(tmp_path, monkeypatch):
    monkeypatch.setattr(qb,'OUT',tmp_path/'experiments')
    return qb.freeze(fixture=True)


def test_callback_failure_claim_is_durable(tmp_path, monkeypatch):
    job=fixture_job(tmp_path,monkeypatch)
    state=io.read(job/'state.json'); state['state']='completed'; io.atomic(job/'state.json',state)
    qb.finalize(job)
    calls=[]
    def fail(*args,**kwargs):
        calls.append(args)
        raise OSError('mock CLI unavailable')
    monkeypatch.setattr(qb.subprocess,'Popen',fail)
    result=qb.review(job)
    assert result['state']=='pending-review' and result['automatic_attempt_claimed']
    qb.review(job)
    assert len(calls)==1
    assert io.read(job/'state.json')['state']=='completed'
    assert io.read(job/'completion.json')['inference_state']=='completed'


def test_callback_success_only_once_and_uses_no_generated_commands(tmp_path, monkeypatch):
    job=fixture_job(tmp_path,monkeypatch)
    state=io.read(job/'state.json'); state['state']='completed'; io.atomic(job/'state.json',state)
    qb.finalize(job)
    calls=[]
    class FakeProcess:
        pid=os.getpid()
        def wait(self): return 0
    def complete(argv, **kwargs):
        calls.append(argv)
        assert '--last' not in argv and 'danger-full-access' not in argv
        assert 'read-only' in argv and 'shell_tool' in argv and 'plugins' in argv
        io.atomic(Path(argv[argv.index('--output-last-message')+1]),
                  {'review_status':'completed','report_markdown':'CALLBACK_FIXTURE_OK'})
        return FakeProcess()
    monkeypatch.setattr(qb.subprocess,'Popen',complete)
    assert qb.review(job,fixture_prompt=True)['state']=='completed'
    assert qb.review(job,fixture_prompt=True)['state']=='completed'
    assert len(calls)==1


def test_interruption_restart_keeps_completed_case_and_old_partial(tmp_path,monkeypatch):
    job=fixture_job(tmp_path,monkeypatch)
    config=io.read(job/'experiment.json'); state=io.read(job/'state.json')
    state['cases'][0].update(state='completed',attempts=[{'attempt_id':'already-completed','state':'completed'}])
    state['cases'][1].update(state='running',attempts=[{'attempt_id':'old-partial','state':'running'}])
    qb.recover(state)
    async def instant(job,config,case,attempt,progress):
        assert case['id']=='fixture/two'
        return {'fixture':True}
    monkeypatch.setattr(qb,'execute_case',instant)
    asyncio.run(qb.batch(job,state,config))
    assert state['state']=='completed'
    assert len(state['cases'][0]['attempts'])==1
    assert len(state['cases'][1]['attempts'])==2
    assert state['cases'][1]['attempts'][0]['state']=='interrupted'
    assert state['cases'][1]['attempts'][1]['attempt_id']!='old-partial'


def test_persistence_failure_stops_queue(tmp_path,monkeypatch):
    job=fixture_job(tmp_path,monkeypatch)
    config=io.read(job/'experiment.json'); state=io.read(job/'state.json')
    async def fail(*args):
        raise OSError('fixture evidence-volume write failure')
    monkeypatch.setattr(qb,'execute_case',fail)
    asyncio.run(qb.batch(job,state,config))
    assert state['state']=='safety-stopped'
    assert state['cases'][1]['state']=='queued'


def test_cancel_preserves_partial_attempt(tmp_path, monkeypatch):
    job=fixture_job(tmp_path,monkeypatch)
    config=io.read(job/'experiment.json'); state=io.read(job/'state.json')
    async def run():
        async def cancel():
            await asyncio.sleep(.1)
            io.atomic(job/'cancel.request',{})
        await asyncio.gather(qb.batch(job,state,config),cancel())
    asyncio.run(run())
    assert state['state']=='cancelled'
    assert state['cases'][0]['attempts'][0]['state']=='cancelled'
    assert state['cases'][1]['state']=='queued'
    assert (job/state['cases'][0]['attempts'][0]['path']/'fixture-request.json').exists()


def test_coroutine_interruption_cancels_owned_inference(tmp_path,monkeypatch):
    job=fixture_job(tmp_path,monkeypatch)
    config=io.read(job/'experiment.json'); state=io.read(job/'state.json')
    async def run():
        task=asyncio.create_task(qb.batch(job,state,config))
        await asyncio.sleep(.05)
        task.cancel()
        await asyncio.wait_for(task,2)  # Test harness only; a cancelled inference must close promptly.
    asyncio.run(run())
    assert state['state']=='interrupted'
    assert state['cases'][0]['attempts'][0]['state']=='interrupted'
    assert state['cases'][1]['state']=='queued'


def test_frozen_full_suite_prompts_with_mock_answers(tmp_path, monkeypatch):
    job=fixture_job(tmp_path,monkeypatch)
    config=io.read(job/'experiment.json')
    config['fixture']=False
    config['model']=io.read(qb.PRIOR/'runs/qwen-paired-v0343/model.json')
    actual_transport=qb.CaptureTransport
    def transport(directory,progress,expected):
        async def handler(request):
            if request.url.path=='/api/tags':
                return httpx.Response(200,json={'models':[config['model']['tag']]})
            body=json.loads(request.content)
            value={}
            for key, spec in body['format']['properties'].items():
                if 'enum' in spec: value[key]=spec['enum'][0]
                elif spec.get('type')=='array': value[key]=[]
                elif spec.get('type')=='string': value[key]='fixture'
                else: raise AssertionError(spec)
            if 'confidence' in value: value['confidence']='high'
            payload=json.dumps({'message':{'content':json.dumps(value)},'done':True,'done_reason':'stop',
                                'prompt_eval_count':1,'eval_count':1,'eval_duration':1000})+'\n'
            class Response(httpx.AsyncByteStream):
                async def __aiter__(self): yield payload.encode()
            return httpx.Response(200,stream=Response())
        return actual_transport(directory,progress,expected,inner=httpx.MockTransport(handler))
    monkeypatch.setattr(qb,'CaptureTransport',transport)
    monkeypatch.chdir(job/'snapshot')
    fixtures=io.read(job/'snapshot/tests/fixtures/paired_requests.json')
    cases=[{'id':'paired/'+f['category'],'suite':'paired','category':f['category']} for f in fixtures]
    cases += [{'id':'v05/'+d['id']+'/'+mode,'suite':'v05','category':d['id'],'mode':mode}
              for d in io.read(job/'v05-cases.json') for mode in ('direct','workflow','auto')]
    async def run():
        for index,case in enumerate(cases):
            attempt=job/'mock'/str(index); attempt.mkdir(parents=True)
            result=await qb.execute_case(job,config,case,attempt,lambda *_:None)
            assert qb.execution_outcome(attempt,result)[0]=='completed',case
            for path in (attempt/'wire').glob('*/prior-request-match.json'):
                checks=io.read(path)
                assert all(checks[k] for k in ('model','format','think','options','keep_alive'))
    asyncio.run(run())


@pytest.mark.skipif(os.name!='nt',reason='Windows independent execution integration')
def test_detached_worker_survives_parent_and_prevents_duplicate(tmp_path, monkeypatch):
    job=fixture_job(tmp_path,monkeypatch)
    # Real short-lived launcher exits; worker has file-backed logs and DEVNULL stdin.
    parent=subprocess.run([sys.executable,str(ROOT/'scripts/qwen_benchmark.py'),'launch','--job',str(job)],
                          capture_output=True,text=True,timeout=15)
    assert parent.returncode==0,parent.stderr
    launched=json.loads(parent.stdout)
    assert io.alive(launched['process'])
    with pytest.raises(RuntimeError): qb.launch(job)
    end=time.monotonic()+25  # Test harness bound only, never an inference/worker bound.
    while time.monotonic()<end:
        state=io.read(job/'state.json')
        if state['state'] in qb.TERMINAL: break
        time.sleep(.1)
    assert state['state']=='completed',(state,(job/'worker.stderr.log').read_text())
    assert all(c['state']=='completed' for c in state['cases'])
    assert io.read(job/'heartbeat.json')['time']>launched['launched_at']
    assert (job/'completion.json').exists()


@pytest.mark.skipif(os.name!='nt',reason='Windows job object process ownership')
def test_owned_child_exits_when_parent_dies(tmp_path):
    launcher=tmp_path/'owner.py'
    launcher.write_text('import sys,time,json\nfrom pathlib import Path\nsys.path.insert(0,'+repr(str(ROOT/'scripts'))+')\n'
        'from qwen_benchmark_io import OwnedRuntime,atomic\nimport os\n'
        'p=Path('+repr(str(tmp_path))+')\n'
        'runtime=OwnedRuntime([sys.executable,"-c","import time; time.sleep(30)"],p,os.environ.copy(),p)\n'
        'atomic(p/"child.json",runtime.identity)\ntime.sleep(30)\n',encoding='utf-8')
    process=io.detached([sys.executable,str(launcher)],tmp_path,tmp_path/'owner.out',tmp_path/'owner.err')
    end=time.monotonic()+10
    while not (tmp_path/'child.json').exists() and time.monotonic()<end: time.sleep(.05)
    child=io.read(tmp_path/'child.json')
    assert io.alive(child)
    process.terminate(); process.wait(timeout=10)
    end=time.monotonic()+5
    while io.alive(child) and time.monotonic()<end: time.sleep(.05)
    assert not io.alive(child)
