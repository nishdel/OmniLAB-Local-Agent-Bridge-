"""Paired, opt-in, real-model benchmark. Explicit model selection; no retries.

Frozen v0.2 prompts/content, fixed 8K context / 600-token generation limit.
Results are review artifacts, never automatically accepted or enabled in routing.
"""
import argparse
import asyncio
from dataclasses import replace
import json
from pathlib import Path
import time
from localagentbridge.bridge import Bridge, BridgeError
from localagentbridge.config import load_config
from localagentbridge.context import evidence_result,fit_evidence
from localagentbridge.hardware import HardwareSampler
from localagentbridge.models import eligibility
from localagentbridge.routing import model_status


async def run(options):
    cfg = load_config(options.config)
    fixtures = json.loads(Path('tests/fixtures/paired_requests.json').read_text(encoding='utf-8'))
    profiles = {p.name:p for p in cfg.model_registry}
    output = Path(options.output)
    output.mkdir(parents=True,exist_ok=True)
    for model in options.models:
        if model not in profiles:
            raise ValueError('Benchmark model must exist in registry; no substitution')
        profile = profiles[model]
        candidate = replace(cfg,roles={r:model for r in ('general','coding','reasoning')},
                            adaptive=replace(cfg.adaptive,enabled=False),timeout_seconds=600)
        statuses = await model_status(candidate)
        if not all(row['installed'] for row in statuses):
            raise ValueError('Missing model. Run: ollama pull '+model)
        bridge = Bridge(candidate)
        path = output / (model.replace(':','_').replace('/','_')+'.json')
        if path.exists():
            raise ValueError('Choose a new output directory; benchmark evidence is never overwritten')
        record = {'run_id':str(time.time_ns()),'model':model,'started':time.time(),
            'protocol': {'think': options.think or False, 'original_protocol': options.think is None},
            'sampling_note':'One-second sampled peaks, not continuous peaks. RSS sums Ollama processes and may count shared pages; GPU used is whole-system. API allocation is not process RSS.',
            'cases':[]}
        for fixture in fixtures:
            if options.category and fixture['category'] not in options.category:
                continue
            cap = bridge.store.compute_cap(cfg.adaptive.default_cap)
            memory = bridge.store.checkpoint('model-measurement:'+model)
            allowed,reason = eligibility(profile,cfg.adaptive,cap,memory)  # explicit benchmark ignores learned quality/latency, not resource/cap bounds
            if not allowed:
                record['blocked'] = reason
                path.write_text(json.dumps(record,indent=2),encoding='utf-8')
                raise ValueError(f'{model} blocked by {reason} at {cap}; no inference attempted')
            bridge.request_template = fixture['body']
            if options.think is not None:
                bridge.request_template = fixture['body'] | {'think':options.think}
            project = None
            if fixture['tool']=='find_relevant_context':
                selected = json.loads(fixture['content'])
                def project(result,budget):
                    return fit_evidence(evidence_result(selected,{'fixture':'frozen-v02'},result,5),budget)
            before = time.time()
            async with HardwareSampler(cfg.endpoint,model) as hardware:
                try:
                    result = await bridge.analyze(fixture['tool'],fixture['content'],fixture['objective'],
                        with_metadata=True,projection=project,
                        max_bytes=1350 if fixture['category']=='consensus_review' else None)
                    error = None
                except BridgeError as exc:
                    result,error = None,str(exc)
            with bridge.store.connect() as db:
                rows = [dict(row) for row in db.execute("SELECT * FROM usage WHERE source='local' AND model=? AND started>=? ORDER BY started",(model,before))]
            entry = {'category':fixture['category'],'tool':fixture['tool'],'input_sha256':fixture['sha256'],
                     'cap':cap,'result':result,'error':error,'usage':rows,'hardware':hardware.values}
            if hardware.values['model_allocation_bytes']:
                bridge.store.checkpoint('model-measurement:'+model,hardware.values | {'model_memory_gb':hardware.values['model_allocation_bytes']/2**30})
            record['cases'].append(entry)
            record['finished'] = time.time()
            path.write_text(json.dumps(record,indent=2),encoding='utf-8')
            print(json.dumps({'model':model,'case':fixture['category'],'error':error,'seconds':rows[-1]['duration'] if rows else None}),flush=True)
        measured = [c['hardware']['model_allocation_bytes'] for c in record['cases'] if c['hardware']['model_allocation_bytes']]
        if measured:
            maximum = {key:max((c['hardware'].get(key) or 0 for c in record['cases']),default=0) for key in hardware.values if key.endswith('_bytes') or key.endswith('_sampled')}
            bridge.store.checkpoint('model-measurement:'+model,maximum | {'model_memory_gb':max(measured)/2**30})


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',default='config.toml')
    parser.add_argument('--models',nargs='+',required=True)
    parser.add_argument('--output',default='benchmarks/v03/results')
    parser.add_argument('--category',action='append')
    parser.add_argument('--think', choices=['low','medium','high'], help='Explicit compatibility run; changes original think=false protocol and is recorded separately')
    asyncio.run(run(parser.parse_args()))
