"""One small, source-grounded direct/workflow comparison. No source edits or model pulls.

Run from the repository with its Python environment. The output directory must be new.
Results stop at the Codex decision; inspect them before supplying a checkpoint.
"""
import argparse
import asyncio
import json
from pathlib import Path
import time

from localagentbridge.config import load_config
from localagentbridge.schemas import compact
from localagentbridge.service import Service
from localagentbridge.workflow import WorkflowTask


async def compare(output):
    root = Path(__file__).resolve().parents[1]
    output.mkdir(parents=True, exist_ok=False)
    config = load_config(root / 'examples/v0.5/minimal.toml')
    config.data_dir = output / 'history'
    config.search.max_candidates = 1
    config.search.max_results = 1
    service = Service(config)
    engine = service.workflows
    lines = (root / 'localagentbridge/models.py').read_text(encoding='utf-8').splitlines()
    first = next(i for i, line in enumerate(lines, 1) if line.startswith('def eligibility('))
    last = next(i for i, line in enumerate(lines, 1) if line.startswith('async def registry_status('))-2
    task = WorkflowTask(task_id='v05-model-tier-docstring-review', kind='review_change',
        objective='Review model_tier in localagentbridge/models.py: does the proposed docstring accurately describe runtime eligibility?',
        scope='localagentbridge',
        context='Small synthetic documentation proposal for this actual source file. Review only the proposed claim; no production edit has been applied.',
        diff='--- a/localagentbridge/models.py\n+++ b/localagentbridge/models.py\n@@ def model_tier(profile, policy):\n+    """Return a tier guaranteeing all current runtime memory, latency and quality gates pass."""\n',
        files=[{'path':'localagentbridge/models.py','first_line':first,'last_line':last}])
    (output / 'task.json').write_text(json.dumps(task.model_dump(), indent=2), encoding='utf-8')
    evidence, sources, snapshot = engine._evidence(task)
    report = {'model':'qwen3:4b','source_fingerprints':sources,'snapshot':snapshot,
        'search_max_candidates':1,'search_max_results':1,
        'order':['direct','workflow'],
        'limitations':['Single synthetic documentation review; no general quality or performance inference.',
                       'Direct runs first; OS/model cache and load timing can differ.',
                       'Provider token counts are actual; energy, peak RAM/VRAM and monetary cost are not measured.']}
    def save():
        (output / 'comparison.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    def usage(since):
        with service.bridge.store.connect() as db:
            return [dict(row) for row in db.execute('SELECT * FROM usage WHERE started >= ? ORDER BY started',(since,))]
    async def direct():
        skill = engine.catalog.skills['code-review']
        return await service.bridge.analyze('review_diff',engine._content(skill,evidence,[]),task.objective,
            role='coding',with_metadata=True,routing={'complexity':'simple','auto_escalate':True})
    started, wall = time.time(), time.perf_counter()
    print('Running direct review', flush=True)
    try:
        result = await direct()
        report['direct'] = {'result':result,'returned_bytes':len(compact(result).encode())}
    except Exception as error:
        report['direct'] = {'error':str(error)}
    report['direct'].update(wall_seconds=time.perf_counter()-wall,usage=usage(started))
    save()
    started, wall = time.time(), time.perf_counter()
    state = engine.start(task)
    steps = []
    while state['state'] == 'ready':
        print('Running workflow stage '+str(state['next_stage']), flush=True)
        state = await engine.step(state['run_id'],state['version'],task)
        steps.append(state)
        # Each call advances one bounded stage or stops. A separate Codex decision is required.
    report['workflow'] = {'steps':steps,'status':state,
        'wall_seconds':time.perf_counter()-wall,'usage':usage(started),
        'returned_bytes':sum(len(compact(step).encode()) for step in steps)}
    save()
    print(json.dumps({'state':state['state'],'run_id':state['run_id'],'output':str(output)}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    asyncio.run(compare(parser.parse_args().output.resolve()))
