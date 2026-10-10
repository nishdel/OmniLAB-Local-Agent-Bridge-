"""Reuse LAB's proven native Ollama transport/schema and accounting for advisory."""
import json
from pathlib import Path

from .bridge import Bridge
from .config import Config


async def run(store, job, contract, content, transport=None):
    if contract.limits.context_tokens > 16384 or contract.limits.output_tokens > 1200:
        raise ValueError('Native advisory uses existing LAB limits: context <=16384, output <=1200; narrow the contract')
    cfg=Config(model=contract.model,endpoint=job['request']['policy']['providers']['ollama']['endpoint'],
               data_dir=store.directory/'usage',source_root=Path(contract.repository),
               num_ctx=contract.limits.context_tokens,max_output_tokens=contract.limits.output_tokens,
               max_input_chars=24000,max_output_bytes=min(6000,contract.limits.output_bytes),
               thinking=job['request'].get('thinking',False),
               no_inference_deadline=contract.limits.inference_deadline_seconds is None,
               timeout_seconds=min(600,contract.limits.inference_deadline_seconds or 180))
    bridge=Bridge(cfg,transport)
    final={}
    class Hooks:
        instructions='\n'.join(s['instruction'] for s in job['request']['skills'])
        def admit(self, request_id, body, input_chars):
            if len(json.dumps(body,ensure_ascii=False).encode()) + contract.limits.output_tokens > contract.limits.context_tokens:
                raise ValueError('Whole native advisory prompt exceeds context budget')
        def finished(self, request_id, value, status, output_bytes):
            final.update(value)
    async def guard(model):
        from .inference import ChatProvider
        observation=await ChatProvider('ollama',job['request']['policy']['providers']['ollama'],transport).inspect(model)
        if contract.require_exact and observation['identity']!=contract.exact_identity:
            raise ValueError('Ollama exact identity changed')
    bridge.model_guard=guard
    try:
        result=await bridge.analyze('analyze_code',content,contract.objective,with_metadata=True,_execution=Hooks())
    except Exception as error:
        error.termination_confirmed=final.get('done') is True
        raise
    return {'content':json.dumps(result,ensure_ascii=False),'reasoning':'','tool_calls':[],
            'usage':{'input_tokens':final.get('prompt_eval_count'),'output_tokens':final.get('eval_count'),
                     'cached_input_tokens':None},
            'timing':{'load_seconds':final.get('load_duration',0)/1e9 if final.get('load_duration') is not None else None,
                      'inference_seconds':final.get('total_duration',0)/1e9 if final.get('total_duration') is not None else None}}
