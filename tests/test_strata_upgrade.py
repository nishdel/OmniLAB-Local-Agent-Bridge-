"""Protocol/identity fixtures, never live Strata qualification."""
import asyncio
import copy
import hashlib
import json
from types import SimpleNamespace

import httpx
import pytest

from localagentbridge.config import Config
from localagentbridge.inference import ChatProvider, ProviderError, strata_messages
from localagentbridge.local_profile import resolve_contract
from localagentbridge.selection import discover, provider_status, select_model
from localagentbridge.strata_identity import verify_binding
from localagentbridge.task_contract import TaskLimits, digest


def verified():
    return dict(ready=True,identity_verified=True,identity='fixture',context_tokens=16384,
                tools_advertised=True,template_sha256='template',build_info='Strata 0.1.43',
                serving_model='actual-coder',backend='strata',model='alias')


def provider(handler, monkeypatch):
    p=ChatProvider('strata',{'enabled':True,'endpoint':'http://localhost:8095'},httpx.MockTransport(handler))
    async def inspect(model): return verified()
    monkeypatch.setattr(p,'inspect',inspect)
    return p


def test_sdk_tool_result_multiturn_and_real_identity_receipt(monkeypatch):
    requests=[]
    tool={'type':'function','function':{'name':'file_editor','parameters':{'type':'object'}}}
    call={'id':'call1','type':'function','function':{'name':'file_editor','arguments':'{"path":"a.py"}'}}
    def handler(req):
        body=json.loads(req.content);requests.append(body)
        msg={'role':'assistant','content':None,'tool_calls':[call]} if len(requests)==1 else {'role':'assistant','content':'done'}
        return httpx.Response(200,json={'model':'arbitrary-echo','choices':[{'message':msg,'finish_reason':'tool_calls' if len(requests)==1 else 'stop'}]})
    p=provider(handler,monkeypatch)
    messages=[{'role':'user','content':[{'type':'text','text':'read declared a.py'}]}]
    first=asyncio.run(p.chat('alias',messages,TaskLimits(),tools=[tool]))
    messages += [first['raw']['choices'][0]['message'],{'role':'tool','tool_call_id':'call1','content':[{'type':'text','text':'bounded result'}]}]
    second=asyncio.run(p.chat('alias',messages,TaskLimits(),tools=[tool]))
    assert requests[1]['messages'][-1]['content']=='bounded result'
    assert requests[0]['strata_mcp'] is False
    assert requests[0]['chat_template_kwargs']=={'enable_thinking':False}
    assert second['effective_runtime']['serving_model']=='actual-coder'
    assert second['usage']==dict(input_tokens=None,output_tokens=None,cached_input_tokens=None)


@pytest.mark.parametrize('messages',[
    [{'role':'user','content':[{'type':'image_url','image_url':{'url':'file:///private'}}]}],
    [{'role':'tool','tool_call_id':'missing','content':'x'}],
    [{'role':'assistant','tool_calls':[{'id':'a','type':'function','function':{'name':'x','arguments':'{}'}}]}],
])
def test_unsupported_history_fails_before_dispatch(messages):
    with pytest.raises(ProviderError): strata_messages(messages)


def test_binding_and_loaded_state_required_before_chat():
    sent=[]
    def handler(req):
        sent.append(req.url.path)
        return httpx.Response(200,json={
            '/health':{'service':'strata','loaded':True,'model':'coder','max_context':16384},
            '/v1/models':{'data':[{'id':'alias'}]},'/props':{}}[req.url.path])
    p=ChatProvider('strata',{'enabled':True,'endpoint':'http://localhost:8095'},httpx.MockTransport(handler))
    with pytest.raises(ProviderError,match='binding'):
        asyncio.run(p.chat('alias',[{'role':'user','content':'x'}],TaskLimits()))
    assert '/v1/chat/completions' not in sent


def test_changed_identity_withholds_response(monkeypatch):
    p=provider(lambda r:httpx.Response(200,json={'choices':[{'message':{'content':'done'},'finish_reason':'stop'}]}),monkeypatch)
    calls=[]
    async def inspect(model):
        calls.append(model)
        return verified() | {'identity':'before' if len(calls)==1 else 'after'}
    monkeypatch.setattr(p,'inspect',inspect)
    with pytest.raises(ProviderError,match='changed') as error:
        asyncio.run(p.chat('alias',[{'role':'user','content':'x'}],TaskLimits()))
    assert error.value.termination_confirmed


def test_oversized_unterminated_sse_and_output_counter(monkeypatch):
    p=provider(lambda r:httpx.Response(200,content=b'data: '+b'x'*2048),monkeypatch)
    with pytest.raises(ProviderError,match='byte'):
        asyncio.run(p.chat('alias',[{'role':'user','content':'x'}],TaskLimits(output_bytes=1024),stream=True))
    p.transport=httpx.MockTransport(lambda r:httpx.Response(200,json={'choices':[{'message':{'content':'x'},'finish_reason':'stop'}],'usage':{'completion_tokens':2000}}))
    with pytest.raises(ProviderError,match='output limit'):
        asyncio.run(p.chat('alias',[{'role':'user','content':'x'}],TaskLimits(output_tokens=128)))


def test_cancel_closes_transport_without_claiming_server_termination(monkeypatch):
    events=[]
    class Waiting(httpx.AsyncByteStream):
        async def __aiter__(self):
            events.append('started')
            await asyncio.Event().wait()
            yield b''
        async def aclose(self): events.append('closed')
    p=provider(lambda r:httpx.Response(200,stream=Waiting()),monkeypatch)
    async def run():
        task=asyncio.create_task(p.chat('alias',[{'role':'user','content':'x'}],TaskLimits()))
        while not events: await asyncio.sleep(.001)
        task.cancel()
        with pytest.raises(asyncio.CancelledError): await task
    asyncio.run(run())
    assert events==['started','closed']


def test_diagnostics_disabled_unreachable_and_no_alias_substitution():
    cfg=Config(selective={'providers':{'strata':{'enabled':False,'endpoint':'http://localhost:8095'}}})
    assert asyncio.run(provider_status(cfg,'strata'))['enabled'] is False
    cfg.selective['providers']['strata'].update(enabled=True,binding={'family':'coder'})
    def offline(req): raise httpx.ConnectError('refused')
    result=asyncio.run(provider_status(cfg,'strata','alias',httpx.MockTransport(offline)))
    assert not result['selectable'] and 'unreachable' in result['reason']


def test_disabled_profile_visible_but_not_selectable_and_exact_override(tmp_path):
    cfg=Config(selective={'model_profiles':[{'backend':'strata','model':'alias','identity':'pin','limits':{'context_tokens':16384}}]})
    def handler(req): return httpx.Response(200,json={'models':[]})
    rows=asyncio.run(discover(cfg,httpx.MockTransport(handler)))
    assert rows[0]['name']=='strata::alias' and not rows[0]['enabled']
    with pytest.raises(ValueError,match='disabled'): select_model(rows,'strata::alias')
    raw=dict(task_id='a',objective='inspect',requirement_ref='test',acceptance={'a':'report'},repository=str(tmp_path),base_revision='a'*40)
    chosen=resolve_contract(cfg,raw,'strata::alias')
    assert (chosen.backend,chosen.model,chosen.exact_identity)==('strata','alias','pin')
    explicit=resolve_contract(cfg,raw|{'backend':'ollama','model':'exact'},'strata::alias')
    assert explicit.backend=='ollama' and explicit.model=='exact'


@pytest.fixture
def binding(tmp_path,monkeypatch):
    import localagentbridge.strata_identity as mod
    artifacts=[]
    for role in ('weights','engine','server','tokenizer','template'):
        p=tmp_path/('server.py' if role=='server' else role);p.write_text(role)
        artifacts.append(dict(path=str(p),role=role,size=p.stat().st_size,mtime_ns=p.stat().st_mtime_ns,
                              sha256=hashlib.sha256(p.read_bytes()).hexdigest(),verified_by_supervisor=True))
    args=['--native',str(tmp_path/'weights'),'--max-context','16384']
    cfg={'host':'127.0.0.1','model_name':'actual-coder','args':args,'exe':str(tmp_path/'engine'),'cwd':str(tmp_path)}
    p=tmp_path/'runtime.json';p.write_text(json.dumps(cfg))
    b=dict(family='coder',identity='pending',config_path=str(p),config_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
        model_path=str(tmp_path/'weights'),build_info='Strata 0.1.43',artifacts=artifacts,
        process={'pid':1},engine_process={'pid':2},server_argv=['python',str(tmp_path/'server.py'),'--config',str(p)],
        engine_argv=[str(tmp_path/'engine'),'--serve',*args],source_commit='a'*40,
        template_sha256=hashlib.sha256(b'template').hexdigest(),context_tokens=16384,
        model_metadata={'model':'Qwen3.8-Flash-Next-GSQ-RCO-Coder','format':'GGUF','quantization':'IQ1_M','expert_count':256})
    b['identity']=digest({k:b[k] for k in ('config_sha256','source_commit','template_sha256','model_metadata')} |
        {'artifacts':[{k:a[k] for k in ('path','size','sha256','role')} for a in artifacts]})
    server=SimpleNamespace(pid=1,cmdline=lambda:b['server_argv'],cwd=lambda:str(tmp_path),net_connections=lambda **kw:[SimpleNamespace(status=mod.psutil.CONN_LISTEN,laddr=SimpleNamespace(ip='127.0.0.1',port=8095))])
    engine=SimpleNamespace(ppid=lambda:1,cmdline=lambda:b['engine_argv'],exe=lambda:str(tmp_path/'engine'))
    monkeypatch.setattr(mod,'alive',lambda p:True)
    monkeypatch.setattr(mod.psutil,'Process',lambda pid:server if pid==1 else engine)
    health={'model':'actual-coder','max_context':16384}
    props=dict(build_info=b['build_info'],model_alias='actual-coder',model_path=b['model_path'],chat_template='template',total_slots=1,default_generation_settings={'n_ctx':16384})
    return b,health,props


def test_complete_local_binding_and_changed_artifact(binding):
    from pathlib import Path
    b,h,p=binding
    assert verify_binding(b,h,p,'http://127.0.0.1:8095')
    Path(b['artifacts'][0]['path']).write_text('changed weights')
    assert not verify_binding(b,h,p,'http://127.0.0.1:8095')


@pytest.mark.parametrize('key,value',[('model_path','wrong'),('build_info','Strata fake'),('chat_template','wrong'),('total_slots',2),('default_generation_settings',{'n_ctx':4096})])
def test_binding_rejects_changed_runtime_metadata(binding,key,value):
    b,h,p=binding;p[key]=value
    assert not verify_binding(b,h,p,'http://127.0.0.1:8095')


def test_binding_rejects_unsafe_startup_and_ollama_weight_label(binding):
    b,h,p=binding
    b['server_argv']+=['--fit-max-tokens']
    assert not verify_binding(b,h,p,'http://127.0.0.1:8095')
    b['server_argv'].pop();b['model_metadata']['model']='qwen3.6:35b-a3b'
    assert not verify_binding(b,h,p,'http://127.0.0.1:8095')


@pytest.mark.parametrize('status,confirmed',[(400,True),(404,True),(413,True),(422,True),(503,False)])
def test_backend_failure_terminal_certainty(monkeypatch,status,confirmed):
    p=provider(lambda req:httpx.Response(status,json={'error':'synthetic failure'}),monkeypatch)
    with pytest.raises(ProviderError,match='HTTP') as error:
        asyncio.run(p.chat('alias',[{'role':'user','content':'x'}],TaskLimits()))
    assert error.value.termination_confirmed == confirmed


def test_preflight_failure_is_confirmed_without_request(monkeypatch):
    p=provider(lambda req:pytest.fail('No inference may dispatch'),monkeypatch)
    async def unavailable(model): raise ProviderError('unreachable')
    monkeypatch.setattr(p,'inspect',unavailable)
    with pytest.raises(ProviderError) as error:
        asyncio.run(p.chat('alias',[{'role':'user','content':'x'}],TaskLimits()))
    assert error.value.termination_confirmed and not p.request_dispatched
