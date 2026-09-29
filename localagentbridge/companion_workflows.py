"""Durable adapters for the existing Service and caller-driven WorkflowEngine.

One job executes one step or one explicitly supplied checkpoint. The workflow
ledger remains authoritative for budgets, evidence, versions and ownership.
"""
from dataclasses import asdict, replace
import hashlib
import json
from pathlib import Path

from .config import Config
from .bridge import BridgeError
from .schemas import RoutingHints
from .selection import discover, select_model
from .service import Service
from .workflow import Checkpoint, WorkflowTask, digest


def configuration(config, store):
    values = asdict(replace(config, data_dir=store.directory/'usage'))
    values['agentic'] = config.agentic.model_dump()
    return json.loads(json.dumps(values, default=str))


def restore(store, request):
    values = dict(request['configuration'])
    # A persisted job cannot redirect the worker to another usage ledger.
    values['data_dir'] = store.directory/'usage'
    return Config(**values)


def check_run(store, config, run_id):
    from .companion import verify_repository
    runs = store.snapshot(run_id)['runs']
    if not runs:
        raise ValueError('Unknown run')
    repository = verify_repository(runs[0])
    if config.source_root != Path(repository):
        raise ValueError('Configured source_root must match the selected worktree')


async def pins(config):
    names = {p.name for p in config.model_registry if p.enabled} if config.adaptive.enabled else set(config.roles.values()) or {config.model}
    rows = await discover(config)
    # Missing registered models remain unavailable, never replaced with an alias.
    return {name:select_model(rows,name)['digest'] for name in sorted(names) if any(r['name']==name for r in rows)}


def label(model_pins):
    return {'name':'configured routing', 'digest':None, 'models':list(model_pins)}


async def submit_service(store, config, run_id, task_key, tool, objective, content,
                         role=None, routing=None, consensus=False, roles=None):
    check_run(store,config,run_id)
    if tool not in ('analyze_code','summarize_context','review_diff','analyze_test_output','second_opinion'):
        raise ValueError('Unsupported routed contribution tool')
    if not content.strip() or len(content)+len(objective)>config.max_input_chars:
        raise ValueError('Empty or oversized contribution')
    if role is not None and role not in ('general','coding','reasoning'):
        raise ValueError('Unknown model role')
    routing = RoutingHints.model_validate(routing).model_dump() if routing is not None else None
    if tool!='second_opinion' and (consensus or roles):
        raise ValueError('Consensus and roles apply only to second_opinion')
    if tool=='second_opinion' and role:
        raise ValueError('Second opinion uses the configured route, or explicit consensus roles')
    model_pins = await pins(config)
    if consensus:
        selected = roles or config.consensus_roles
        models = [config.resolve_model(tool,r)[1] for r in selected]
        if len(selected) not in (2,3) or len(set(selected))!=len(selected) or len(set(models))!=len(models):
            raise ValueError('Consensus requires two or three distinct roles and models')
        if any(m not in model_pins for m in models):
            raise ValueError('Exact consensus model is unavailable; no substitute was selected')
    request = dict(execution='routed',tool=tool,objective=objective,content=content,
                   configuration=configuration(config,store),model_pins=model_pins,
                   selection=label(model_pins),endpoint=config.endpoint,role=role,routing=routing,
                   consensus=consensus,roles=roles,source_sha256=hashlib.sha256(content.encode()).hexdigest())
    return store.submit(run_id,task_key,request)


async def submit_workflow(store, config, run_id, task_key, task):
    check_run(store,config,run_id)
    if not config.agentic.enabled:
        raise ValueError('Workflow support is disabled; configure [agentic]')
    values = configuration(config,store)
    engine = Service(Config(**values)).workflows
    task = WorkflowTask.model_validate(task)
    # The same caller task ID in another companion run must not share a ledger.
    task = task.model_copy(update={'task_id':run_id+':'+hashlib.sha256(task.task_id.encode()).hexdigest()})
    plan = engine.plan(task)
    model_pins = await pins(config)
    request = dict(execution='workflow',tool='workflow_step',objective=task.objective,
        content=json.dumps(task.model_dump()),configuration=values,model_pins=model_pins,
        selection=label(model_pins),endpoint=config.endpoint,workflow_task=task.model_dump(),
        workflow_policy=engine.policy_digest,workflow_plan=plan,workflow_id=None,version=None,
        handoffs=[],checkpoint=None)
    return store.submit(run_id,task_key,request)


def follow_workflow(store, job_id, checkpoint=None, task=None):
    previous = store.job(job_id)
    if previous['state']!='succeeded' or previous['request'].get('execution')!='workflow':
        raise ValueError('Inspect the interrupted/failed workflow; only completed steps can be continued')
    request = dict(previous['request'])
    answer = previous['result']['answer']
    state = answer['workflow']
    if checkpoint is None and state['state']!='ready':
        raise ValueError('Workflow is not ready; an explicit supervising checkpoint is required')
    if checkpoint is not None:
        checkpoint = Checkpoint.model_validate(checkpoint).model_dump()
        if state['state'] not in ('waiting_for_codex','handed_off','cancelled'):
            raise ValueError('Workflow is not waiting for a checkpoint')
    if task is not None:
        if checkpoint is None:
            raise ValueError('Evidence changes require a checkpoint')
        task = dict(task,task_id=request['workflow_task']['task_id'])
        request['workflow_task'] = WorkflowTask.model_validate(task).model_dump()
    request.update(workflow_id=state['run_id'],version=state['version'],
                   handoffs=answer['handoffs'],checkpoint=checkpoint,
                   tool='workflow_checkpoint' if checkpoint else 'workflow_step',
                   content=json.dumps(request['workflow_task']))
    key = 'workflow:'+state['run_id']+':'+str(state['version'])+':'+hashlib.sha256(
        json.dumps(request,sort_keys=True).encode()).hexdigest()[:16]
    # Identical retries share admission; a corrected rejected request can be
    # submitted explicitly. The engine's version lease prevents double progress.
    return store.submit(previous['run_id'],key,request)


def service_for(store, job):
    request = job['request']
    config = restore(store,request)
    check_run(store,config,job['run_id'])
    service = Service(config)
    if request['execution']=='workflow' and service.workflows.policy_digest!=request['workflow_policy']:
        raise ValueError('Workflow catalog/policy changed; restore the pinned policy or scope new work')

    async def guard(model):
        if model not in request['model_pins']:
            raise BridgeError('Routed model was unavailable at submission; resubmit explicitly')
        selected = select_model(await discover(config),model)
        if selected.get('digest')!=request['model_pins'][model]:
            raise BridgeError('Routed model digest changed since submission')
    service.bridge.model_guard = guard
    return service


async def perform(service, request):
    if request['execution']=='routed':
        if request['tool']=='second_opinion':
            return await service.second_opinion(request['objective'],request['content'],
                consensus=request['consensus'],roles=request['roles'],routing=request['routing'])
        return await service.analyze(request['tool'],request['content'],request['objective'],
                                     role=request['role'],routing=request['routing'])
    engine = service.workflows
    task = request['workflow_task']
    state = engine.start(task) if request['workflow_id'] is None else engine.status(request['workflow_id'])
    if engine.ledger.journal:
        with engine.ledger.store.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            engine.ledger.journal.attach(db,state['run_id'])
    version = state['version'] if request['version'] is None else request['version']
    if request['checkpoint'] is not None:
        state = engine.checkpoint(state['run_id'],version,task,request['checkpoint'])
    elif state['state']=='ready':
        row = engine.ledger.read(state['run_id'])
        stage = json.loads(row['plan'])['stages'][row['position']]
        needed = [p for p in request['handoffs'] if p['stage_id'] in stage['inputs_from']]
        state = await engine.step(state['run_id'],version,task,needed)
    else:
        # Initial policy handoffs are visible; they never become implicit acceptance.
        if request['workflow_id'] is not None:
            raise ValueError('Workflow is not ready; inspect its current ledger state')
    packets = {(p['stage_id'],p['skill_id']):p for p in request['handoffs']}
    packets.update({(p['stage_id'],p['skill_id']):p for p in state.pop('handoffs',[])})
    if request['checkpoint'] and request['checkpoint']['action']=='revise':
        packets = {}
    # Keep only references still valid after a correction checkpoint.
    packets = {k:p for k,p in packets.items() if any(r['digest']==digest(p)
        for r in engine.ledger.result_refs(state['run_id'],k[0]))}
    return {'workflow':state,'handoffs':list(packets.values())}


def usage_since(service, started):
    with service.bridge.store.connect() as db:
        rows = [dict(r) for r in db.execute("SELECT * FROM usage WHERE source='local' AND started>=?",(started,))]
    def total(field):
        return sum(r[field] for r in rows) if all(r[field] is not None for r in rows) else None
    return {'input_tokens':total('input_tokens'),'output_tokens':total('output_tokens'),'attempts':rows}
