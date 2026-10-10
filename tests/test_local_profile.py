import asyncio
from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest

from localagentbridge.config import Config
from localagentbridge.local_profile import resolve_contract, provider_settings
from localagentbridge.runtime_profile import runner_evidence
from localagentbridge.selective_resources import HostGuard
from localagentbridge.task_contract import TaskLimits

def settings(tmp_path):
    return {'project_root':str(tmp_path), 'defaults':{'backend':'ollama','model':'qualified:tag'},
            'model_profiles':[{'backend':'ollama','model':'qualified:tag','identity':'pinned',
                'limits':{'context_tokens':65536,'output_tokens':1536,'steps':8,'transport_retries':0,
                          'self_repair_cycles':2,'attempt_seconds':1800},
                'provider':{'enabled':True,'native_context':True,'num_gpu':28,'draft_num_predict':4}}]}

def request(tmp_path):
    return dict(task_id='scope',objective='Inspect',requirement_ref='test',
                acceptance={'a':'Report'},repository=str(tmp_path),base_revision='a'*40)

def test_default_selection_and_explicit_override(tmp_path):
    cfg=Config(selective=settings(tmp_path))
    selected=resolve_contract(cfg,request(tmp_path))
    assert (selected.model,selected.exact_identity,selected.limits.context_tokens)==('qualified:tag','pinned',65536)
    assert provider_settings(cfg.selective,selected)['num_gpu']==28
    explicit=resolve_contract(cfg,request(tmp_path)|{'model':'other:tag'})
    assert explicit.model=='other:tag' and explicit.exact_identity is None
    public=resolve_contract(cfg,request(tmp_path),'selector:tag')
    assert public.model=='selector:tag' and public.exact_identity is None
    assert resolve_contract(cfg,request(tmp_path)|{'model':'other:tag'},'selector:tag').model=='other:tag'

def test_profile_narrowing_identity_and_scope(tmp_path):
    cfg=Config(selective=settings(tmp_path))
    assert resolve_contract(cfg,request(tmp_path)|{'limits':{'output_tokens':512}}).limits.output_tokens==512
    for values in ({'limits':{'output_tokens':1537}},{'limits':{'context_tokens':32768}},
                   {'limits':{'transport_retries':1}},{'repository':str(tmp_path/'other')}):
        with pytest.raises(ValueError): resolve_contract(cfg,request(tmp_path)|values)
    wrong=resolve_contract(cfg,request(tmp_path)|{'exact_identity':'wrong'})
    with pytest.raises(ValueError,match='identity'):provider_settings(cfg.selective,wrong)

def test_effective_runner_flags_fail_closed():
    binding={'runner_model':'weights','runner_flags':{'-c':65536,'-ngl':28,'--spec-draft-n-max':4}}
    proc=SimpleNamespace(pid=123,cmdline=lambda:['llama-server.exe','--model','weights','-c','65536','-ngl','28','--spec-draft-n-max','4'],
                         create_time=lambda:42,exe=lambda:'llama-server.exe')
    assert runner_evidence(binding,TaskLimits(context_tokens=65536),[proc])['pid']==123
    for processes in ([],[proc,proc]):
        with pytest.raises(ValueError):runner_evidence(binding,TaskLimits(context_tokens=65536),processes)
    binding['runner_flags']['-ngl']=0
    with pytest.raises(ValueError,match='setting'):runner_evidence(binding,TaskLimits(context_tokens=65536),[proc])

def test_host_admission_and_sustained_pressure(tmp_path):
    limits=dict(minimum_available_before_bytes=6,hard_available_bytes=2,
                sustained_available_bytes=3,sustained_seconds=15,maximum_gpu_mib=100)
    current={'host_available':8,'gpu_used_mib':[50]}; now=[0]
    guard=HostGuard(limits,tmp_path/'resources.jsonl',lambda:current,lambda:now[0])
    guard.check(True)
    current['host_available']=5
    with pytest.raises(ValueError,match='admission'):guard.check(True)
    current['host_available']=2.5;guard.check()
    now[0]=16
    with pytest.raises(ValueError,match='Sustained'):guard.check()
    current['host_available']=1
    with pytest.raises(ValueError,match='Hard'):guard.check()
    current.update(host_available=8,gpu_used_mib=[101])
    with pytest.raises(ValueError,match='GPU'):guard.check()
    current['gpu_used_mib']=[]
    with pytest.raises(ValueError,match='diagnostics'):guard.check()

def test_wrong_backend_version_stops_before_inference():
    from localagentbridge.inference import ChatProvider,ProviderError
    from localagentbridge.runtime_profile import template_identity
    calls=[]
    def response(req):
        calls.append(req.url.path)
        return httpx.Response(200,json={
          '/api/tags':{'models':[{'name':'m','digest':'exact'}]},
          '/api/show':{'details':{'quantization_level':'Q4_K_M'},'template':'t'},
          '/api/version':{'version':'unexpected'}}[req.url.path])
    p=ChatProvider('ollama',{'endpoint':'http://127.0.0.1:11434','runtime_binding':{
       'identity':'exact','quantization':'Q4_K_M','template_sha256':template_identity('t'),'backend_version':'pinned'}},
       httpx.MockTransport(response))
    with pytest.raises(ProviderError,match='identity'):asyncio.run(p.inspect('m'))
    assert '/api/chat' not in calls

def test_qualified_profile_never_uses_legacy_transport(tmp_path):
    from localagentbridge.bridge import Bridge,BridgeError
    cfg=Config(model='qualified:tag',data_dir=tmp_path/'usage',selective=settings(tmp_path))
    with pytest.raises(BridgeError,match='runtime settings'):
        asyncio.run(Bridge(cfg).analyze('analyze_code','bounded source'))

def test_explicit_backend_needs_explicit_model(tmp_path):
    cfg=Config(selective=settings(tmp_path))
    with pytest.raises(ValueError,match='explicit model'):
        resolve_contract(cfg,request(tmp_path)|{'backend':'strata'},'qualified:tag')

def test_profile_preserves_tool_and_host_ceilings(tmp_path):
    cfg=Config(selective=settings(tmp_path))
    for key,value in [('test_seconds',121),('memory_mb',2049),('cpus',3),('output_bytes',65537),('snapshot_bytes',16000001)]:
        with pytest.raises(ValueError,match='exceeds'):
            resolve_contract(cfg,request(tmp_path)|{'limits':{key:value}})


@pytest.mark.parametrize('loaded_vram',[None,0,8192])
def test_qualified_gpu_requires_actual_loaded_vram(monkeypatch,loaded_vram):
    from localagentbridge.inference import ChatProvider,ProviderError
    from localagentbridge.runtime_profile import template_identity
    def response(req):
        data={
          '/api/tags':{'models':[{'name':'m','digest':'exact'}]},
          '/api/show':{'details':{'quantization_level':'Q4_K_M'},'template':'t',
                       'capabilities':['completion'],'model_info':{'qwen.context_length':65536}},
          '/api/version':{'version':'pinned'},
          '/api/chat':{'done':True,'done_reason':'stop','message':{'role':'assistant','content':'done'},
                       'prompt_eval_count':10,'eval_count':1},
          '/api/ps':{'models':[{'name':'m','digest':'exact','context_length':65536,'size_vram':loaded_vram}]}}
        return httpx.Response(200,json=data[req.url.path])
    monkeypatch.setattr('localagentbridge.runtime_profile.runner_evidence',lambda *args:{'pid':123})
    p=ChatProvider('ollama',{'endpoint':'http://127.0.0.1:11434','native_context':True,
        'verify_loaded_context':True,'num_gpu':28,'runtime_binding':{
        'identity':'exact','quantization':'Q4_K_M','template_sha256':template_identity('t'),
        'backend_version':'pinned','maximum_output_tokens':1536}},httpx.MockTransport(response))
    call=p.chat('m',[{'role':'user','content':'brief'}],TaskLimits(context_tokens=65536,output_tokens=1536))
    if loaded_vram:
        answer=asyncio.run(call)
        assert answer['effective_runtime']['loaded_vram_bytes']==loaded_vram
    else:
        with pytest.raises(ProviderError,match='CPU fallback forbidden'):asyncio.run(call)
