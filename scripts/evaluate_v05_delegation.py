"""Seven bounded self-review cases: direct, forced workflow, auto. Never edits source.

Outputs stop at Codex checkpoints for separate source-grounded assessment. Fresh
history per cell prevents earlier grades/latency from changing later routing.
"""
import argparse
import asyncio
import hashlib
import json
from pathlib import Path
import time

from localagentbridge.config import load_config
from localagentbridge.service import Service
from localagentbridge.workflow import WorkflowTask
from localagentbridge.schemas import compact

ROOT = Path(__file__).resolve().parents[1]


def excerpt(path, anchor, count, offset=0):
    lines=(ROOT/path).read_text(encoding='utf-8').splitlines()
    first=next(i for i,line in enumerate(lines,1) if anchor in line)+offset
    return {'path':path,'first_line':first,'last_line':min(first+count-1,len(lines))}


def cases():
    common={'scope':'localagentbridge','validation_status':'not_run',
        'context':'Synthetic candidate change against current LocalAgentBridge source. No production edit was applied. Identify only consequential issues supported by this evidence.'}
    def case(name,kind,objective,oracle,**kwargs):
        return {'id':name,'oracle':oracle,'task':common|{'task_id':name,'kind':kind,'objective':objective}|kwargs}
    return [
        case('discovery','repository_discovery','Locate the definition of model_tier in localagentbridge/models.py.',
             {'tier-location':'models.py contains the model_tier definition; verify its exact line.'},delegation={}),
        case('narrow-review','review_change','Review the proposed model_tier docstring for accuracy; suggest the smallest correction.',
             {'false-guarantee':'model_tier classifies static tiers; runtime memory/latency and reviewed quality are separate gates.'},
             diff='--- a/localagentbridge/models.py\n+++ b/localagentbridge/models.py\n@@ def model_tier(profile, policy):\n+    """Return a tier guaranteeing all current memory, latency and quality gates pass."""',
             files=[excerpt('localagentbridge/models.py','def eligibility(',38)],delegation={}),
        case('isolated-bug','bug_analysis','Explain the exact-limit input rejection and the minimal fix. The stated contract allows input equal to max_input_chars.',
             {'inclusive-boundary':'Changing > to >= rejects an exactly-at-limit input; restore strict greater-than.'},
             diff='--- a/localagentbridge/bridge.py\n+++ b/localagentbridge/bridge.py\n-        if input_chars > cfg.max_input_chars:\n+        if input_chars >= cfg.max_input_chars:',
             test_output='Candidate report: content plus objective has exactly 10000 characters; max_input_chars is 10000; candidate rejects it.',
             files=[excerpt('localagentbridge/bridge.py','input_chars = len(content)',4)],delegation={}),
        case('architecture','architecture_review','Review a public workflow-status response change across store, engine and MCP consumers. Identify concrete compatibility failures.',
             {'version-contract':'Removing version prevents callers supplying the version required by step/checkpoint.',
              'run-id-contract':'Renaming run_id to id breaks callers consuming run_id to continue/status a run.'},
             diff='--- a/localagentbridge/workflow_store.py\n+++ b/localagentbridge/workflow_store.py\n-        result = {"run_id":run_id,"version":row["version"], ...}\n+        result = {"id":run_id, ...}',
             files=[excerpt('localagentbridge/workflow_store.py',"result = {'run_id'",4),
                    excerpt('localagentbridge/workflow.py','async def step(',10),
                    excerpt('localagentbridge/server.py','async def workflow_step(',5)],
             delegation={'components':3,'expected_files':3,'independent_concerns':2,'architecture_impact':True,'independent_review':True}),
        case('security','security_review','Review this simplified selected-file resolver for source-root confinement. What can a caller read outside its authorized root?',
             {'path-escape':'Joining root/name without validation admits ../ or absolute paths and follows symlinks outside root.'},
             diff='--- a/localagentbridge/files.py\n+++ b/localagentbridge/files.py\n@@ replace entire resolve_selected body\n+    return (root / name).resolve(strict=True)',
             files=[excerpt('localagentbridge/files.py','def resolve_selected(',15)],
             delegation={'security_sensitive':True}),
        case('resources','resource_review','Review removing handoff-cache eviction to retain results from every workflow. Describe the resource consequence without claiming measured memory or speed.',
             {'retained-cache-growth':'Removing the 64-entry eviction retains packets across runs and grows memory until lifecycle/history limits; durable hashes do not need these bodies.'},
             diff='--- a/localagentbridge/workflow.py\n+++ b/localagentbridge/workflow.py\n-                        if len(self.cache) >= 64:\n-                            self.cache.pop(next(iter(self.cache)))',
             files=[excerpt('localagentbridge/workflow.py','self.cache = {}',1),
                    excerpt('localagentbridge/workflow.py','if len(self.cache) >= 64:',5)],
             delegation={'resource_sensitive':True}),
        case('release','release_review','Audit this candidate v0.5 source export for runtime completeness. Distinguish missing Python modules from missing bundled definition data. Do not publish anything.',
             {'missing-modules':'The old public allowlist omits catalog.py, workflow.py, workflow_store.py and delegation.py required by the new runtime.',
              'missing-definitions':'The old allowlist omits the TOML definitions that Catalog loads at startup.'},
             context='Candidate export: use unchanged PUBLIC-FILES.txt to copy the new development source. Complete allowlisted localagentbridge entries:\n'+
                 '\n'.join(line for line in (ROOT/'PUBLIC-FILES.txt').read_text().splitlines() if line.startswith('localagentbridge/'))+
                 '\nThe supplied new code is exported only when explicitly listed. No directory expansion or packaging step adds omitted files. This is an audit proposal, not a publication instruction.',
             files=[excerpt('localagentbridge/service.py','if config.agentic.enabled:',3),
                    excerpt('localagentbridge/config.py','from .catalog import',1),
                    excerpt('localagentbridge/catalog.py',"roots = [Path(__file__)",4),
                    excerpt('localagentbridge/workflow.py','from .delegation import',1)],
             delegation={'release_scope':True,'components':2,'expected_files':8}),
    ]


async def evaluate(output, selected=None):
    output.mkdir(parents=True,exist_ok=False)
    dataset=cases()
    if selected:
        dataset=[case for case in dataset if case['id'] in selected]
        if len(dataset)!=len(set(selected)):
            raise ValueError('Unknown evaluation case')
    paths={f['path'] for c in dataset for f in c['task'].get('files',[])}
    source_hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(paths)}
    (output/'source-hashes.json').write_text(json.dumps(source_hashes,indent=2),encoding='utf-8')
    (output/'cases.json').write_text(json.dumps(dataset,indent=2),encoding='utf-8')
    results=[]
    for case in dataset:
        for mode in ('direct','workflow','auto'):
            if any(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=expected for p,expected in source_hashes.items()):
                raise RuntimeError('Evaluation source changed; preserve this run and rebuild exact excerpts.')
            cfg=load_config(ROOT/'examples/v0.5/minimal.toml')
            cfg.data_dir=output/case['id']/mode/'history'
            cfg.search.max_candidates=cfg.search.max_results=1
            engine=Service(cfg).workflows
            task=WorkflowTask.model_validate(case['task']|{'task_id':case['id']+'-'+mode,
                'delegation':case['task']['delegation']|{'mode':mode}})
            print(f"{case['id']} / {mode}: planning",flush=True)
            start=time.perf_counter()
            state=engine.start(task)
            steps=[]
            error=None
            try:
                for _ in range(12):
                    if state['state']!='ready':
                        break
                    state=await engine.step(state['run_id'],state['version'],task)
                    steps.append(state)
            except Exception as exc:
                error=str(exc)
                state=engine.status(state['run_id'])
            wall=time.perf_counter()-start
            with engine.service.bridge.store.connect() as db:
                rows=[dict(row) for row in db.execute('SELECT * FROM usage ORDER BY started')]
            result={'case':case['id'],'mode':mode,'task':task.model_dump(),'status':state,
                'steps':steps,'wall_seconds':wall,'usage':rows,'error':error,
                'model_calls':sum(row['input_tokens'] is not None for row in rows),
                'preflight_or_unknown_usage':sum(row['input_tokens'] is None for row in rows),
                'input_tokens':sum(row['input_tokens'] or 0 for row in rows),
                'output_tokens':sum(row['output_tokens'] or 0 for row in rows),
                'automatic_corrections':state['budget']['corrections'],
                'returned_bytes':sum(len(compact(s).encode()) for s in steps)}
            results.append(result)
            (output/'results.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
            print(f"{case['id']} / {mode}: {state['state']}, {result['model_calls']} calls, {wall:.2f}s",flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--cases',nargs='+',help='Repeat only named cases; keep prior evidence unchanged.')
    args=parser.parse_args()
    asyncio.run(evaluate(args.output.resolve(),args.cases))
