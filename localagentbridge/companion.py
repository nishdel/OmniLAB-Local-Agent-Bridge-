"""Controller and independent, serial local worker. CLI/file interface, no listener."""
import asyncio
from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from .bridge import Bridge
from .companion_store import CompanionStore
from .config import Config
from .process_control import Lock, detached, identity
from .selection import discover, select_model
from .schemas import SCHEMAS


def git_identity(repository):
    repository = Path(repository).resolve(strict=True)
    def git(*args):
        return subprocess.check_output(['git','-C',str(repository),*args],text=True,stderr=subprocess.DEVNULL,timeout=10).strip()
    root = Path(git('rev-parse','--show-toplevel')).resolve()
    if root != repository:
        raise ValueError('Select a repository/worktree root')
    return str(root), git('rev-parse','HEAD')


def verify_repository(run):
    root, revision = git_identity(run['repository'])
    if revision != run['base_revision']:
        raise ValueError('Repository base revision changed; create a new run after reviewing changes')
    return root


async def submit(store, config, run_id, task_key, tool, objective, content, model=None, no_deadline=False):
    if tool not in ('analyze_code','summarize_context','review_diff','analyze_test_output'):
        raise ValueError('Unsupported bounded contribution tool')
    if not content.strip() or len(content)+len(objective)>config.max_input_chars:
        raise ValueError('Empty or oversized contribution; supply a bounded excerpt')
    snap = store.snapshot(run_id)
    if not snap['runs']:
        raise ValueError('Unknown run')
    run = snap['runs'][0]
    verify_repository(run)
    if config.source_root is None or str(config.source_root) != run['repository']:
        raise ValueError('Configured source_root must match the selected worktree')
    rows = await discover(config)
    selected = select_model(rows, model or store.setting('default_model') or config.adaptive.preferred_model or config.model)
    request = dict(tool=tool, objective=objective, content=content, selection=selected,
                   endpoint=config.endpoint, timeout_seconds=None if no_deadline else config.timeout_seconds,
                   max_input_chars=config.max_input_chars, max_output_tokens=config.max_output_tokens,
                   max_output_bytes=config.max_output_bytes, num_ctx=config.num_ctx,
                   source_sha256=hashlib.sha256(content.encode()).hexdigest(),
                   thinking=next((p.thinking for p in config.model_registry if p.name==selected['name']), config.thinking))
    return store.submit(run_id, task_key, request)


def job_config(store, job):
    req = job['request']
    run = store.snapshot(job['run_id'])['runs'][0]
    verify_repository(run)
    cfg = Config(model=req['selection']['name'], endpoint=req['endpoint'], source_root=Path(run['repository']),
                 data_dir=store.directory/'usage', max_input_chars=req['max_input_chars'],
                 max_output_tokens=req['max_output_tokens'], max_output_bytes=req['max_output_bytes'],
                 num_ctx=req['num_ctx'], timeout_seconds=req['timeout_seconds'] or 180,
                 no_inference_deadline=req['timeout_seconds'] is None, thinking=req['thinking'])
    return cfg


async def execute(store, job):
    attempt = job['attempt_id']
    try:
        cfg = job_config(store, job)
        selection = select_model(await discover(cfg), cfg.model)
        if selection.get('digest') != job['request']['selection'].get('digest'):
            raise ValueError('Selected model digest changed since submission')
        bridge = Bridge(cfg)
        req = job['request']
        task = asyncio.create_task(bridge.analyze(req['tool'],req['content'],req['objective'],with_metadata=True))
        try:
            while not task.done():
                if store.job(job['id'])['cancel_requested']:
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
                    store.complete(job['id'],attempt,state='cancelled',error='HTTP request cancelled; shared Ollama may continue inference')
                    return
                # Controller runtime checks cancellation; no Codex/model polling calls.
                await asyncio.wait({task}, timeout=.25)
            result = task.result()
        finally:
            if not task.done():
                task.cancel()
                await asyncio.gather(task,return_exceptions=True)
        with bridge.store.connect() as db:
            usage = db.execute('SELECT * FROM usage WHERE id=?',(result['_meta']['request_id'],)).fetchone()
        store.complete(job['id'],attempt,result={'answer':result,'usage':dict(usage) if usage else None})
    except Exception as error:
        store.complete(job['id'],attempt,error=type(error).__name__+': '+str(error),state='failed')


def worker(directory):
    store = CompanionStore(directory)
    with Lock(store.directory/'worker.lock'):
        # An acquired kernel lock proves there is no previous cooperating worker.
        for old in store.snapshot()['jobs']:
            if old['state']=='running':
                store.complete(old['id'],old['attempt_id'],state='interrupted',error='Worker exited; generation cannot resume mid-token')
        while True:
            job = store.claim_job(identity())
            if not job:
                return
            asyncio.run(execute(store,job))


def ensure_worker(store):
    try:
        with Lock(store.directory/'worker.lock'):
            pass
    except RuntimeError:
        return None
    snapshot = store.snapshot()
    if snapshot['paused'] or not any(j['state'] in ('queued','running') for j in snapshot['jobs']):
        return None
    # Child imports the runtime selected by this controller, never the task worktree.
    runtime = Path(__file__).resolve().parents[1]
    return detached([sys.executable,'-B','-m','localagentbridge.companion','worker',str(store.directory)],
                    runtime, store.directory/'worker.stdout.log',store.directory/'worker.stderr.log')


def serve(directory, codex_exe=None, once=False):
    from .callbacks import dispatch
    store = CompanionStore(directory)
    with Lock(store.directory/'controller.lock'):
        store.recover_deliveries()
        store.setting('controller_stop',False)
        store.setting('controller_process',identity())
        try:
            while not store.setting('controller_stop'):
                store.setting('controller_heartbeat',store.clock())
                ensure_worker(store)
                if codex_exe:
                    event = store.claim_event()
                    if event:
                        dispatch(store,event,codex_exe)
                if once:
                    return
                time.sleep(1)  # Process scheduling; no active Codex turn while waiting.
        finally:
            store.setting('controller_stopped_at',store.clock())


if __name__=='__main__':
    if len(sys.argv)==3 and sys.argv[1]=='worker':
        worker(sys.argv[2])
    elif len(sys.argv) in (3,4) and sys.argv[1]=='controller':
        serve(sys.argv[2],sys.argv[3] if len(sys.argv)==4 else None)
    else:
        raise SystemExit('Internal entry point: worker|controller DIRECTORY [CODEX_EXE]')
