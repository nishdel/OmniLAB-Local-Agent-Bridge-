import asyncio
import hashlib
import json

import httpx
import pytest

from localagentbridge.inference import ChatProvider, ProviderError, validate_completion
from localagentbridge.task_contract import TaskLimits


def completion(content='answer', **values):
    return {'choices':[{'message':{'content':content},'finish_reason':'stop'}],**values}


def test_strata_health_alias_is_not_identity():
    def handler(req):
        payload={'/health':{'service':'strata','loaded':True,'model':'coder','max_context':32768},
                 '/v1/models':{'data':[{'id':'alias','alias_of':'coder'}]},
                 '/props':{'model_path':'/pack','build_info':'Strata 0.1.41'}}
        return httpx.Response(200,json=payload[req.url.path])
    p=ChatProvider('strata',{'enabled':True,'endpoint':'http://localhost:8080'},httpx.MockTransport(handler))
    result=asyncio.run(p.inspect('alias'))
    assert result['ready'] and not result['identity_verified']
    assert result['identity'] is None and 'weights' in result['identity_uncertainty']
    with pytest.raises(ProviderError,match='not listed'): asyncio.run(p.inspect('wrong'))


@pytest.mark.parametrize('health,models',[({},[]),({'service':'elsewhere'},[]),
    ({'service':'strata','loaded':True,'max_context':0},[{'id':'coder'}]),
    ({'service':'strata','loaded':True,'max_context':8192},'wrong')])
def test_invalid_strata_readiness(health,models):
    def handler(req):
        return httpx.Response(200,json=health if req.url.path=='/health' else
                              {'data':models} if req.url.path=='/v1/models' else {})
    p=ChatProvider('strata',{'enabled':True,'endpoint':'http://127.0.0.1:8080'},httpx.MockTransport(handler))
    with pytest.raises(ProviderError): asyncio.run(p.inspect('coder'))


@pytest.mark.parametrize('url',['http://example.com','http://0.0.0.0:8080','http://u:p@localhost','http://localhost/v1'])
def test_provider_local_boundary(url):
    with pytest.raises(ProviderError): ChatProvider('strata',{'enabled':True,'endpoint':url})
    with pytest.raises(ProviderError): ChatProvider('strata',{'endpoint':'http://localhost'})


def test_nonstream_reasoning_and_optional_usage():
    response=completion(usage={'prompt_tokens':11,'completion_tokens':3,'prompt_tokens_details':{'cached_tokens':7}})
    response['choices'][0]['message']['reasoning_content']='private reasoning'
    p=ChatProvider('strata',{'enabled':True,'endpoint':'http://localhost:8080'},
                   httpx.MockTransport(lambda req:httpx.Response(200,json=response)))
    result=asyncio.run(p.chat('coder',[{'role':'user','content':'test'}],TaskLimits()))
    assert result['content']=='answer' and result['reasoning']=='private reasoning'
    assert result['usage']=={'input_tokens':11,'output_tokens':3,'cached_input_tokens':7}
    assert validate_completion(completion())['usage']['input_tokens'] is None


def test_streaming_separates_reasoning_and_requires_done():
    lines=[
      {'choices':[{'delta':{'reasoning_content':'think'},'finish_reason':None}]},
      {'choices':[{'delta':{'content':'final'},'finish_reason':None}]},
      {'choices':[{'delta':{},'finish_reason':'stop'}],'usage':{'prompt_tokens':2,'completion_tokens':3}}]
    stream=''.join('data: '+json.dumps(x)+'\n\n' for x in lines)+'data: [DONE]\n\n'
    for data,success in ((stream,True),(stream.replace('data: [DONE]\n\n',''),False)):
        p=ChatProvider('strata',{'enabled':True,'endpoint':'http://localhost:8080'},
                       httpx.MockTransport(lambda req:httpx.Response(200,text=data)))
        if success:
            result=asyncio.run(p.chat('coder',[{'role':'user','content':'x'}],TaskLimits(),stream=True))
            assert result['content']=='final' and result['reasoning']=='think'
        else:
            with pytest.raises(ProviderError,match='disconnected'):
                asyncio.run(p.chat('coder',[{'role':'user','content':'x'}],TaskLimits(),stream=True))


@pytest.mark.parametrize('raw',[{}, {'choices':[]}, {'choices':[{'message':{'content':'x'},'finish_reason':'length'}]},
    {'choices':[{'message':{'content':['x']},'finish_reason':'stop'}]},
    {'choices':[{'message':{'content':''},'finish_reason':'stop'}]}, completion(usage='bad')])
def test_malformed_outputs(raw):
    with pytest.raises(ProviderError): validate_completion(raw)


def test_tool_call_roundtrip_contract_validation():
    tools=[{'type':'function','function':{'name':'terminal','parameters':{'type':'object'}}}]
    raw={'choices':[{'finish_reason':'tool_calls','message':{'content':None,'tool_calls':[
        {'id':'call1','type':'function','function':{'name':'terminal','arguments':'{"command":"echo test"}'}}]}}]}
    assert validate_completion(raw,tools=tools)['tool_calls'][0]['id']=='call1'
    with pytest.raises(ProviderError): validate_completion(raw)
    raw['choices'][0]['message']['tool_calls'][0]['function']['arguments']='malformed'
    with pytest.raises(ProviderError): validate_completion(raw,tools=tools)


def test_context_overflow_and_output_budget_fail_without_truncation():
    calls=[]
    def handler(req):
        calls.append(req)
        return httpx.Response(200,json=completion('x'*4000))
    p=ChatProvider('ollama',{'endpoint':'http://localhost:11434'},httpx.MockTransport(handler))
    with pytest.raises(ProviderError,match='context'):
        asyncio.run(p.chat('exact',[{'role':'user','content':'x'*3000}],TaskLimits(context_tokens=2048)))
    assert not calls
    with pytest.raises(ProviderError,match='byte'):
        asyncio.run(p.chat('exact',[{'role':'user','content':'x'}],TaskLimits(output_bytes=1024)))


def test_connect_retries_but_never_replays_read_timeout():
    calls=[]
    def handler(req):
        calls.append(req)
        raise httpx.ConnectError('offline')
    p=ChatProvider('ollama',{'endpoint':'http://localhost:11434'},httpx.MockTransport(handler))
    with pytest.raises(httpx.ConnectError):
        asyncio.run(p.chat('exact',[{'role':'user','content':'x'}],TaskLimits(transport_retries=1)))
    assert len(calls)==2
    calls.clear()
    def uncertain(req):
        calls.append(req)
        raise httpx.ReadTimeout('unknown')
    p.transport=httpx.MockTransport(uncertain)
    with pytest.raises(httpx.ReadTimeout):
        asyncio.run(p.chat('exact',[{'role':'user','content':'x'}],TaskLimits()))
    assert len(calls)==1


def test_no_deadline_preserves_connect_timeout_and_no_redirect():
    seen=[]
    def handler(req):
        seen.append(req.extensions['timeout'])
        return httpx.Response(302,headers={'Location':'http://external.invalid'})
    p=ChatProvider('strata',{'enabled':True,'endpoint':'http://localhost'},httpx.MockTransport(handler))
    with pytest.raises(httpx.HTTPStatusError):
        asyncio.run(p.chat('coder',[{'role':'user','content':'x'}],TaskLimits()))
    assert len(seen)==1 and seen[0]['read'] is None and seen[0]['connect']==5


@pytest.mark.parametrize('backend,payload',[('ollama',[]),('ollama',{'models':['bad']}),
                                          ('strata',[])])
def test_nonobject_inventory_fails_with_provider_error(backend,payload):
    def handler(req):
        return httpx.Response(200,json=payload if backend=='ollama' or req.url.path=='/v1/models' else
            {'service':'strata','loaded':True,'model':'coder','max_context':8192})
    p=ChatProvider(backend,{'enabled':True,'endpoint':'http://localhost'},httpx.MockTransport(handler))
    with pytest.raises(ProviderError):
        asyncio.run(p.inspect('coder'))


def test_nonobject_tool_function_fails_with_provider_error():
    raw={'choices':[{'finish_reason':'tool_calls','message':{'tool_calls':[
        {'id':'call','type':'function','function':None}]}}]}
    with pytest.raises(ProviderError):
        validate_completion(raw)


@pytest.mark.parametrize('loaded', [65536, 8192, None])
def test_ollama_reasoning_roundtrip_checks_actual_context(loaded):
    payloads = []
    def handler(req):
        if req.url.path == '/api/ps':
            return httpx.Response(200, json={'models':[{'name':'exact', 'context_length':loaded}]})
        payloads.append(json.loads(req.content))
        value = completion(usage={'prompt_tokens':7000, 'completion_tokens':50})
        value['choices'][0]['message']['reasoning'] = 'retained reasoning'
        return httpx.Response(200, json=value)
    provider = ChatProvider('ollama', {'endpoint':'http://localhost:11435',
        'temperature':0.6, 'reasoning_effort':'medium', 'verify_loaded_context':True}, httpx.MockTransport(handler))
    messages = [{'role':'assistant','content':'prior','reasoning_content':'earlier reasoning'},
                {'role':'user','content':'continue'}]
    operation = provider.chat('exact', messages, TaskLimits(context_tokens=65536))
    if loaded == 65536:
        result = asyncio.run(operation)
        assert result['reasoning'] == 'retained reasoning'
        assert result['loaded_context_tokens'] == loaded
    else:
        with pytest.raises(ProviderError, match='Effective loaded context') as error:
            asyncio.run(operation)
        assert error.value.termination_confirmed
    assert payloads[0]['messages'][0]['reasoning'] == 'earlier reasoning'
    assert 'reasoning_content' not in payloads[0]['messages'][0]
    assert 'reasoning_content' in messages[0]
    assert payloads[0]['temperature'] == 0.6 and payloads[0]['reasoning_effort'] == 'medium'


@pytest.mark.parametrize('key,value', [('temperature',float('nan')),('temperature',True),
    ('reasoning_effort','unbounded'),('verify_loaded_context','true')])
def test_sampling_and_context_policy_reject_invalid_values(key,value):
    from localagentbridge.config import Config
    with pytest.raises(ValueError):
        Config(selective={'providers':{'ollama':{key:value}}})
