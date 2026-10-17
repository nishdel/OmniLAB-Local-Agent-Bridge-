import asyncio
import io
import json
from pathlib import Path
import tarfile
import uuid

import httpx
import pytest

from localagentbridge.companion_store import CompanionStore
from localagentbridge.measurements import record, summary
from localagentbridge.selective import execute
from localagentbridge.selective_resources import memory_admission, competing_runtime
from localagentbridge.task_store import TaskStore
from test_selective_contracts import contract, request


class FakeSandbox:
    image='sha256:'+'a'*64
    def __init__(self, wrong=False):
        self.containers={}; self.creates=[]; self.wrong=wrong
    def preflight(self): return True
    def inspect(self,name,owner):
        if name not in self.containers: raise RuntimeError('No such container')
        row=self.containers[name]
        return {'State':{'Running':row['running'],'Status':row['state'],'ExitCode':0}}
    def create(self,name,owner,c,mode='agent'):
        self.creates.append(name)
        self.containers[name]={'running':False,'state':'created','mode':mode,'c':c,'request_id':str(uuid.uuid4())}
    def put(self,name,owner,raw):
        files={}
        with tarfile.open(fileobj=io.BytesIO(raw)) as tar:
            for item in tar:
                if item.isfile() and item.name.startswith('workspace/'):
                    files[item.name[10:]]=tar.extractfile(item).read()
        self.containers[name]['files']=files
    def start(self,name,owner):
        row=self.containers[name]
        if row['state']=='exited': return
        row['running']=row['mode']=='agent'
        row['state']='running' if row['running'] else 'exited'
    def read(self,name,owner,path,*args):
        row=self.containers[name]
        if path=='/exchange/request.json':
            return {'id':row['request_id'],'body':{'model':row['c'].model,'stream':False,
                'messages':[{'role':'user','content':'fix source'}],'tools':[]}}
        if path=='/workspace/.': return row['files']
        if path=='/exchange/result.json':
            correct=row['files']['subject.py']==b'x=2\n'
            return {'checks':[{'id':'check','argv':['python','check.py'],'covers':['a'],
                'exit_code':0 if correct else 1,'timed_out':False,'output':'passed' if correct else 'AssertionError',
                'output_truncated':False,'seconds':.01}]}
        raise AssertionError(path)
    def respond(self,name,owner,response):
        row=self.containers[name]
        row['files']['subject.py']=b'x=3\n' if self.wrong else b'x=2\n'
        row['running']=False; row['state']='exited'
    def stop(self,name,owner):
        self.containers[name]['running']=False
        self.containers[name]['state']='exited'
        return True


def transport():
    def handler(req):
        if req.url.path=='/api/tags': data={'models':[{'name':'exact:tag','digest':'weights'}]}
        elif req.url.path=='/api/show': data={'capabilities':['completion','tools'],'model_info':{'x.context_length':32768}}
        elif req.url.path=='/api/ps': data={'models':[]}
        elif req.url.path=='/api/chat':
            answer={'behavior':'boundary','findings':[],'uncertainties':[],'recommended_tests':[],'confidence':'medium'}
            return httpx.Response(200,text=json.dumps({'done':True,'message':{'content':json.dumps(answer)},
                'prompt_eval_count':10,'eval_count':4})+'\n')
        elif req.url.path=='/v1/chat/completions': data={'choices':[{'message':{'content':'Candidate is ready'},'finish_reason':'stop'}],
                                                     'usage':{'prompt_tokens':10,'completion_tokens':4}}
        else: raise AssertionError(req.url.path)
        return httpx.Response(200,json=data)
    return httpx.MockTransport(handler)


def flow(tmp_path,monkeypatch,wrong=False,lane='local_implementation'):
    import localagentbridge.selective as selective
    monkeypatch.setattr(selective,'git_snapshot',lambda *a:{'subject.py':b'x=1\n','check.py':b'assert x==2\n'})
    c=contract(tmp_path,requested_lane=lane)
    r=request(c)
    r['policy'].update(providers={'ollama':{'endpoint':'http://127.0.0.1:11434'}}, sandbox={},
        memory_plan={'supervisor_verified':True,'os_and_apps_mb':1,'lab_mb':1,'runtime_mb':1,
                     'context_cache_mb':1,'headroom_mb':1})
    store=CompanionStore(tmp_path/'state'); run=store.create_run(tmp_path,'a'*40)
    jid=TaskStore(store).submit_many(run,[r])[0]; job=store.claim_job({})
    sandbox=FakeSandbox(wrong)
    asyncio.run(execute(store,job,transport(),lambda _:sandbox))
    return store,job,sandbox


@pytest.mark.parametrize('wrong',[False,True])
def test_isolated_mock_flow_separates_baseline_candidate_and_review(tmp_path,monkeypatch,wrong):
    store,job,sandbox=flow(tmp_path,monkeypatch,wrong)
    state=TaskStore(store).get(job['id'])
    assert store.job(job['id'])['state']=='succeeded', store.job(job['id'])['error']
    assert state['execution_status']=='finished'
    assert state['verification_status']==('verification_failed' if wrong else 'passed')
    assert state['evidence']['baseline_checks'][0]['exit_code']==1
    assert state['review_status']==('escalated' if wrong else 'awaiting_review')
    assert len(sandbox.creates)==3
    assert state['accepted_hash'] is None
    assert store.snapshot()['inference_reservation'] is None
    assert store.claim_job({}) is None


def test_advisory_mock_flow_keeps_skills_and_usage(tmp_path,monkeypatch):
    store,job,_=flow(tmp_path,monkeypatch,lane='local_advisory')
    state=TaskStore(store).get(job['id'])
    assert store.job(job['id'])['state']=='succeeded', store.job(job['id'])['error']
    assert state['verification_status']=='not_run' and state['review_status']=='awaiting_review'
    assert store.job(job['id'])['result']['usage']['input_tokens']==10
    assert summary(store,job['id'])[0]['kind']=='observed'


def test_measurement_provenance_and_idempotency(tmp_path):
    store=CompanionStore(tmp_path/'state'); run=store.create_run(tmp_path,'base')
    jid=store.submit(run,'test',{})
    record(store,jid,'review','review',{'cloud_input_tokens':None},'unavailable','No attributable telemetry')
    record(store,jid,'review','review',{'cloud_input_tokens':None},'unavailable','No attributable telemetry')
    assert len(summary(store,jid))==1
    with pytest.raises(ValueError): record(store,jid,'bad','planning',{'cloud_input_tokens':100},'unavailable','estimate')
    with pytest.raises(ValueError): record(store,jid,'nan','planning',{'elapsed_seconds':float('nan')},'observed','clock')


def test_combined_memory_is_not_weight_size_only(tmp_path):
    c=contract(tmp_path)
    plan={'memory_plan':{'supervisor_verified':True,'os_and_apps_mb':8000,'lab_mb':500,
                        'runtime_mb':23000,'context_cache_mb':1000,'headroom_mb':1000}}
    assert not memory_admission(c,plan,total_mb=32768,available_mb=10000)[0]
    assert memory_admission(c,plan,total_mb=64000,available_mb=20000)[0]
    assert not memory_admission(c,{},total_mb=64000,available_mb=20000)[0]


def test_resident_other_provider_blocks_without_unloading(tmp_path):
    calls=[]
    def handler(req):
        calls.append(req.method+' '+req.url.path)
        return httpx.Response(200,json={'models':[{'name':'other:large'}]})
    c=contract(tmp_path,backend='strata')
    policy={'providers':{'ollama':{'endpoint':'http://localhost:11434','enabled':True}}}
    reason=asyncio.run(competing_runtime(c,policy,httpx.MockTransport(handler)))
    assert 'resident' in reason
    assert calls==['GET /api/ps']


def test_pilot_fixtures_have_matching_arms_and_are_not_run(tmp_path):
    import importlib.util
    path=Path(__file__).resolve().parents[1]/'scripts/prepare_selective_pilot.py'
    spec=importlib.util.spec_from_file_location('pilot',path); module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    manifest=module.prepare(tmp_path/'pilot')
    assert len(manifest['cases'])==8 and not manifest['executed']
    for case in manifest['cases']:
        arms=case['arms']
        assert len({(Path(a['directory'])/'subject.py').read_bytes() for a in arms})==1
        assert len({(Path(a['directory'])/'acceptance.py').read_bytes() for a in arms})==1
        assert all(a['result']=='not_run' for a in arms)
