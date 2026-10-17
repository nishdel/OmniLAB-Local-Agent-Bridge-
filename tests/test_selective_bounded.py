import asyncio
import json
import sys
import threading

import httpx
import pytest

from localagentbridge.executor_assets.bounded import CommandPolicy, run_bounded
from localagentbridge.inference import ChatProvider, ProviderError
from localagentbridge.task_contract import TaskLimits


def policy(tmp_path):
    (tmp_path/'subject.py').write_bytes(b'x=1\n')
    (tmp_path/'check.py').write_text('print("checked")\n')
    c = dict(context_files=['subject.py'], permitted_files=['subject.py'], acceptance_files=['check.py'],
        checks=[{'argv':[sys.executable,'check.py']}], operations=['read','test'],
        limits={'output_bytes':1024,'test_seconds':2})
    return CommandPolicy(c,tmp_path)


@pytest.mark.parametrize('command', ['python -c print(1)','cat ../secret','cat /etc/passwd',
    'cat subject.py; echo bad','cat subject.py && python check.py','cat subject.py | cat',
    'cat subject.py > check.py','cat subject.py\ncat check.py','sh',''])
def test_bounded_command_denial(tmp_path, command):
    p = policy(tmp_path)
    with pytest.raises(ValueError): p.execute(command)
    assert (tmp_path/'check.py').read_text() == 'print("checked")\n'


def test_bounded_read_and_exact_test(tmp_path):
    p = policy(tmp_path)
    assert p.execute('cat subject.py')['output'] == 'x=1\n'
    command = '"'+sys.executable.replace('\\','/')+'" check.py'
    # shlex uses POSIX paths; bind the exact normalized spelling in this Windows test.
    p.checks = [[sys.executable.replace('\\','/'),'check.py']]
    r = p.execute(command)
    assert r['exit_code'] == 0 and 'checked' in r['output']
    assert not r['timed_out'] and not r['output_truncated']


@pytest.mark.parametrize('kind', ['timeout','cancel','output'])
def test_bounded_process_termination(tmp_path,kind):
    stop = threading.Event()
    if kind == 'cancel': stop.set()
    code = 'import time; time.sleep(60)' if kind != 'output' else 'while True: print("x"*4096,flush=True)'
    r = run_bounded([sys.executable,'-c',code],cwd=tmp_path,seconds=.25 if kind=='timeout' else 5,
        output_bytes=1024,cancel=stop)
    assert r[{'timeout':'timed_out','cancel':'cancelled','output':'output_truncated'}[kind]]
    assert len(r['output'].encode()) <= 1024
    assert r['seconds'] < 8


def test_read_output_exhaustion(tmp_path):
    p=policy(tmp_path);(tmp_path/'subject.py').write_bytes(b'x'*1025)
    with pytest.raises(ValueError,match='output budget'): p.execute('cat subject.py')


def test_native_context_sdk_roundtrip_translation():
    seen=[]
    def handle(req):
        if req.url.path=='/api/ps':return httpx.Response(200,json={'models':[{'name':'exact:tag','context_length':32768}]})
        assert req.url.path=='/api/chat'
        seen.append(json.loads(req.content))
        return httpx.Response(200,json={'done':True,'done_reason':'stop','message':{'role':'assistant','content':'',
            'thinking':'reason','tool_calls':[{'function':{'name':'terminal','arguments':{'command':'cat f'}}}]},'prompt_eval_count':17,'eval_count':5})
    p=ChatProvider('ollama',{'endpoint':'http://localhost:11434','native_context':True,'verify_loaded_context':True},httpx.MockTransport(handle))
    tools=[{'type':'function','function':{'name':'terminal'}}]
    result=asyncio.run(p.chat('exact:tag',[{'role':'assistant','content':[{'type':'text','text':'part one'},{'type':'text','text':'part two'}],'reasoning_content':'prior',
        'tool_calls':[{'id':'old','type':'function','function':{'name':'terminal','arguments':'{"command":"cat f"}'}}]},
        {'role':'tool','tool_call_id':'old','content':'file'}],TaskLimits(context_tokens=32768),tools=tools))
    assert seen[0]['options']['num_ctx']==32768 and seen[0]['think'] is False
    assert seen[0]['messages'][0]['content']=='part one\npart two'
    assert seen[0]['messages'][0]['thinking']=='prior'
    assert seen[0]['messages'][0]['tool_calls'][0]['function']['arguments']=={'command':'cat f'}
    assert result['tool_calls'][0]['id'].startswith('call_') and result['reasoning']=='reason'
    assert result['loaded_context_tokens']==32768 and result['usage']['input_tokens']==17


@pytest.mark.parametrize('response', [{}, {'done':False,'message':{}},
    {'done':True,'done_reason':'length','message':{'content':'partial'}},
    {'done':True,'done_reason':'stop','message':{'tool_calls':[{'function':{'name':'terminal','arguments':'bad'}}]}}])
def test_native_context_rejects_incomplete_or_malformed(response):
    p=ChatProvider('ollama',{'endpoint':'http://localhost:11434','native_context':True},
        httpx.MockTransport(lambda req:httpx.Response(200,json=response)))
    with pytest.raises(ProviderError):asyncio.run(p.chat('exact:tag',[],TaskLimits()))


def test_collection_failure_never_creates_success_checkpoint(tmp_path):
    from test_selective_contracts import contract, setup
    from localagentbridge.selective import verify, artifact_dir
    c=contract(tmp_path)
    store,_,_=setup(tmp_path,c);job=store.claim_job({})
    class Broken:
        readonly=True
        image='sha256:'+'a'*64
        stopped=False
        def inspect(self,*a): return {'State':{'Running':True,'Status':'running'}}
        def start(self,*a): pass
        def completion(self,*a): return {'ExitCode':0}
        def read(self,*a): raise ValueError('collection incomplete')
        def stop(self,*a): self.stopped=True;return True
    sandbox=Broken()
    with pytest.raises(ValueError,match='collection incomplete'):
        asyncio.run(verify(store,job,sandbox,c,{'subject.py':b'x=1'},'verify'))
    assert sandbox.stopped
    assert not list(artifact_dir(store,job).glob('*collected.json'))


def test_qualification_requires_activation_without_comparison_pilot(tmp_path,monkeypatch):
    from dataclasses import replace
    from localagentbridge.config import Config
    from localagentbridge.companion_store import CompanionStore
    import localagentbridge.qualification as q
    cfg=Config(source_root=tmp_path,data_dir=tmp_path/'data',selective={'enabled':True,'implementation_enabled':True,'pilot_enabled':False})
    store=CompanionStore(cfg.data_dir)
    with pytest.raises(ValueError,match='explicit activation'):
        asyncio.run(q.start(store,cfg,'ollama','exact:tag'))
    class Provider:
        def __init__(self,*a): pass
        async def inspect(self,model):return {'ready':True,'identity_verified':True,'identity':'weights','context_tokens':32768,'tools_advertised':True}
    class Sandbox:
        def __init__(self,*a):pass
        def preflight(self):return True
    async def prepare(config,contracts):
        from test_selective_contracts import request
        return [request(contracts[0])]
    monkeypatch.setattr(q,'ChatProvider',Provider);monkeypatch.setattr(q,'DockerSandbox',Sandbox)
    monkeypatch.setattr(q,'prepare',prepare);monkeypatch.setattr(q,'git_identity',lambda p:(str(tmp_path),'a'*40))
    monkeypatch.setattr(q,'memory_admission',lambda *a:(True,None))
    cfg=replace(cfg,selective=cfg.selective|{'providers':{'ollama':{}},'sandbox':{}})
    result=asyncio.run(q.start(store,cfg,'ollama','exact:tag',activate=True,fixture_seed='a'*32,
        limits={'context_tokens':32768,'output_tokens':1536},execution_guidance='Use only declared file paths.'))
    job=store.job(result['job_id'])
    from localagentbridge.selective import original_files
    from localagentbridge.task_contract import Contract
    files=original_files(store,job,Contract.model_validate(job['request']['contract']))
    assert set(files)=={'subject.py','seed.txt','acceptance.py'}
    assert files['seed.txt'].decode().strip()=='a'*32
    assert job['request']['contract']['context']=='Use only declared file paths.'
    assert job['request']['contract']['limits']['output_tokens']==1536
    assert not list(tmp_path.rglob('.git'))
    assert cfg.selective['pilot_enabled'] is False


def test_correction_keeps_frozen_supplemental_acceptance(tmp_path):
    from test_selective_contracts import setup
    from localagentbridge.selective import save_tree,artifact_dir,original_files,correction
    from localagentbridge.task_store import TaskStore
    from localagentbridge.task_contract import Contract
    from localagentbridge.sandbox import tree_hash
    store,_,jid=setup(tmp_path);job=store.claim_job({})
    frozen={'subject.py':b'x=1', 'check.py':b'assert False'}
    save_tree(artifact_dir(store,job)/'base.json',frozen)
    TaskStore(store).update(job,evidence={'base_tree_hash':tree_hash(frozen)},review_status='escalated')
    store.complete(jid,job['attempt_id'],state='failed',error='fixture')
    child=correction(store,jid,'Keep original scope and frozen checks')
    revised=store.claim_job({});assert revised['id']==child
    assert original_files(store,revised,Contract.model_validate(revised['request']['contract']))==frozen
    assert (artifact_dir(store,job)/'base.json').read_bytes()==(artifact_dir(store,revised)/'base.json').read_bytes()


@pytest.mark.parametrize('fail', [False, True])
def test_failed_collection_is_bounded_and_never_acceptance(tmp_path,fail):
    from test_selective_contracts import setup
    from localagentbridge.selective import collect_failed_attempt,artifact_dir
    store,_,_=setup(tmp_path);job=store.claim_job({})
    class Sandbox:
        def freeze(self,*a):return {'quiesced':True}
        def read(self,name,owner,path,cap):
            if path=='/workspace/.':return {'subject.py':b'x=broken'}
            if fail:raise ValueError('missing command audit')
            return [{'argv':['python','check.py'],'exit_code':1,'output':'failed'}]
    result=collect_failed_attempt(store,job,Sandbox(),'owned',ValueError('model failure'))
    assert result['collection_complete'] is not fail
    assert result['execution_finished'] is False
    assert (artifact_dir(store,job)/'failed-tree.json').exists()
    assert not (artifact_dir(store,job)/'candidate.json').exists()


def test_native_text_blocks_never_drop_unsupported_content():
    def unexpected(req):raise AssertionError('Must reject before sending')
    p=ChatProvider('ollama',{'endpoint':'http://localhost:11434','native_context':True},httpx.MockTransport(unexpected))
    with pytest.raises(ProviderError,match='Only SDK text'):
        asyncio.run(p.chat('exact:tag',[{'role':'user','content':[{'type':'image_url','image_url':{'url':'secret'}}]}],TaskLimits()))


def test_native_rejection_retains_bounded_error_and_confirmed_rejection():
    p=ChatProvider('ollama',{'endpoint':'http://localhost:11434','native_context':True},
        httpx.MockTransport(lambda req:httpx.Response(400,text='invalid wire type'+'x'*10000)))
    with pytest.raises(ProviderError,match='HTTP 400') as exc:asyncio.run(p.chat('exact:tag',[],TaskLimits()))
    assert exc.value.termination_confirmed and len(str(exc.value))<4200


@pytest.mark.parametrize('stop_confirmed', [True, False])
def test_evidence_exhaustion_still_stops_owned_executor(monkeypatch, stop_confirmed):
    import localagentbridge.selective as selective
    calls=[]
    class Sandbox:
        readonly=True
        def inspect(self,*args):return {'State':{'Running':True}}
        def stop(self,name,owner):calls.append((name,owner));return stop_confirmed
    def exhausted(*args):raise ValueError('Host evidence budget exhausted')
    monkeypatch.setattr(selective,'collect_failed_attempt',exhausted)
    expected='Host evidence budget' if stop_confirmed else 'termination is unconfirmed'
    with pytest.raises(ValueError,match=expected):
        selective.collect_then_stop(None,{'attempt_id':'owned-attempt'},Sandbox(),'owned-container',ValueError('failed'))
    assert calls==[('owned-container','owned-attempt')]


def test_context_accounting_preserves_bytes_margin_and_failure_history():
    from localagentbridge.inference import context_accounting
    payload={'messages':[{'role':'system','content':'requirements'}, {'role':'tool','content':'failed check \u00e4'}],
             'tools':[{'type':'function','function':{'name':'terminal'}}]}
    limits=TaskLimits(context_tokens=2048,output_tokens=64,context_safety_tokens=512)
    result=context_accounting(payload,limits)
    assert result['input_token_upper_bound']==len(json.dumps(payload,ensure_ascii=False).encode())
    assert result['required_capacity_bound']==result['serialized_bytes']+576
    assert result['message_bytes_by_role']['tool']>0 and not result['history_compacted']
    assert result['actual_input_tokens'] is None and not result['exact_tokenizer']
    payload['messages'][1]['content']='failure'*500
    assert context_accounting(payload,limits)['classification']=='conservative_admission_rejection'


def test_scoped_approval_is_exact_and_cannot_bypass_security(tmp_path):
    from test_selective_contracts import contract
    from localagentbridge.task_contract import route,digest
    c=contract(tmp_path)
    cap={'ready':True,'identity_verified':True,'identity':c.exact_identity,'context_tokens':131072,
         'sandbox_available':True,'context_verified':True,'tool_roundtrip_verified':True}
    policy={'enabled':True,'implementation_enabled':True,'pilot_enabled':False,
            'scoped_task_approvals':[digest(c.model_dump())]}
    assert route(c,cap,policy)['effective_lane']=='local_implementation'
    assert route(c,cap|{'sandbox_available':False},policy)['effective_lane']=='codex_direct'
    assert route(c,cap|{'tool_roundtrip_verified':False},policy)['effective_lane']=='codex_direct'
    changed=c.model_copy(update={'context':'Different task'})
    assert route(changed,cap,policy)['effective_lane']=='codex_direct'


def test_native_scoped_offload_strict_context_and_request_accounting():
    seen=[]
    def handle(req):
        seen.append(json.loads(req.content))
        return httpx.Response(200,json={'done':True,'done_reason':'stop','message':{'content':'ok'},
            'prompt_eval_count':19,'eval_count':2,'load_duration':123})
    p=ChatProvider('ollama',{'endpoint':'http://localhost:11434','native_context':True,
        'num_gpu':14,'keep_alive_seconds':60,'strict_context':True},httpx.MockTransport(handle))
    result=asyncio.run(p.chat('exact:tag',[],TaskLimits(context_safety_tokens=1024)))
    assert seen[0]['options']['num_gpu']==14 and seen[0]['keep_alive']==60
    assert seen[0]['truncate'] is False and seen[0]['shift'] is False
    assert result['context_accounting']['actual_input_tokens']==19
    assert result['context_accounting']['safety_tokens']==1024
    assert result['provider_timing_ns']['load_duration']==123


def test_fixture_seed_rejects_noncanonical_input_before_dispatch(tmp_path):
    from localagentbridge.qualification import start
    with pytest.raises(ValueError,match='Fixture seed'):
        asyncio.run(start(None,None,'ollama','exact:tag',fixture_seed='../outside'))


@pytest.mark.parametrize('setting,value', [('num_gpu',-1),('keep_alive_seconds',1801),('strict_context','yes')])
def test_native_scope_options_fail_closed(setting,value):
    from localagentbridge.selective_config import validate_policy
    with pytest.raises(ValueError):
        validate_policy({'providers':{'ollama':{'native_context':True,setting:value}}})


def test_sdk_repair_budget_counts_only_error_observations():
    from localagentbridge.selective import enforce_repair_budget
    failure={'role':'tool','content':[{'type':'text','text':'[An error occurred during execution.] denied'}]}
    history=[{'role':'user','content':failure['content']}, {'role':'tool','content':[{'type':'text','text':'passed'}]}]
    enforce_repair_budget(history+[failure]*2,2)
    with pytest.raises(ValueError,match='self-repair cycle budget'):
        enforce_repair_budget(history+[failure]*3,2)
    enforce_repair_budget(history+[failure]*5,None)


def test_implementation_cancel_collects_before_volatile_stop(tmp_path,monkeypatch):
    from test_selective_contracts import setup
    from localagentbridge import selective
    from localagentbridge.task_contract import Contract
    store,_,_=setup(tmp_path);job=store.claim_job({});c=Contract.model_validate(job['request']['contract'])
    frozen={'subject.py':b'x=1\n','check.py':b'assert False\n'}
    monkeypatch.setattr(selective,'original_files',lambda *a:frozen)
    monkeypatch.setattr(store,'job',lambda *a:dict(job,cancel_requested=True))
    calls=[]
    class Sandbox:
        readonly=True
        def inspect(self,*a):return {'State':{'Running':True,'Status':'running'}}
        def start(self,*a):pass
        def completion(self,*a):return None
        def freeze(self,*a):calls.append('freeze');return {'quiesced':True}
        def read(self,name,owner,path,cap):
            calls.append('read')
            return frozen if path=='/workspace/.' else []
        def stop(self,*a):calls.append('stop');return True
    sandbox=Sandbox()
    with pytest.raises(asyncio.CancelledError):
        asyncio.run(selective.implementation(store,job,None,c,sandbox))
    assert 'stop' not in calls
    selective.collect_then_stop(store,job,sandbox,'lab-'+job['attempt_id'],asyncio.CancelledError())
    assert calls[0]=='freeze' and calls[-1]=='stop'
    packet=json.loads((selective.artifact_dir(store,job)/'failed-collection.json').read_text())
    assert packet['collection_complete'] and not packet['execution_finished']


@pytest.mark.parametrize('draft', [0, 3])
def test_scoped_draft_loading_option_is_explicit_and_native_only(draft):
    from localagentbridge.selective_config import validate_policy
    settings={'endpoint':'http://localhost:11434','native_context':True,'draft_num_predict':draft}
    validate_policy({'providers':{'ollama':settings}})
    seen=[]
    def handle(req):
        seen.append(json.loads(req.content))
        return httpx.Response(200,json={'done':True,'done_reason':'stop','message':{'content':'ok'}})
    provider=ChatProvider('ollama',settings,httpx.MockTransport(handle))
    asyncio.run(provider.chat('exact:tag',[],TaskLimits()))
    assert seen[0]['options']['draft_num_predict']==draft
    assert seen[0]['think'] is False
    for invalid in ({'native_context':False}, {'draft_num_predict':-1},
                    {'draft_num_predict':True}, {'draft_num_predict':17}):
        with pytest.raises(ValueError,match='scoped native'):
            validate_policy({'providers':{'ollama':settings|invalid}})
    with pytest.raises(ValueError,match='scoped native'):
        validate_policy({'providers':{'strata':settings}})


def test_absent_scoped_draft_preserves_installed_runtime_default():
    seen=[]
    def handle(req):
        seen.append(json.loads(req.content))
        return httpx.Response(200,json={'done':True,'done_reason':'stop','message':{'content':'ok'}})
    provider=ChatProvider('ollama',{'endpoint':'http://localhost:11434','native_context':True},httpx.MockTransport(handle))
    asyncio.run(provider.chat('exact:tag',[],TaskLimits()))
    assert 'draft_num_predict' not in seen[0]['options']
