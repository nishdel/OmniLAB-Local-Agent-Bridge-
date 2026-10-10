"""Versioned, local-user CLI interface shared by scripts and the Tk dock."""
import asyncio
import json
from pathlib import Path
import sys

from .companion_store import CompanionStore


def add_parser(commands):
    parser = commands.add_parser('companion',help='Durable local contributions and managed read-only Codex review')
    actions = parser.add_subparsers(dest='action',required=True)
    from .selective_cli import add as add_selective
    add_selective(actions)
    actions.add_parser('inventory',help='List installed models and advertised capabilities; no inference')
    select = actions.add_parser('select',help='Save an exact installed model default for future jobs')
    select.add_argument('model')
    actions.add_parser('create',help='Create a run for configured source_root at current Git HEAD')
    submit = actions.add_parser('submit',help='Durably submit a bounded task JSON; returns without inference')
    submit.add_argument('--run',required=True)
    submit.add_argument('--request',type=Path,required=True)
    submit.add_argument('--model')
    submit.add_argument('--execution',choices=['exact','routed'],help='Default: configured routing when roles exist; --model explicitly chooses exact execution')
    submit.add_argument('--no-deadline',action='store_true')
    workflow = actions.add_parser('workflow-submit',help='Queue one existing v0.5 workflow step, preserving policy and budgets')
    workflow.add_argument('--run',required=True)
    workflow.add_argument('--request',type=Path,required=True)
    for name in ('workflow-next','workflow-checkpoint','workflow-status'):
        command = actions.add_parser(name,help='Continue or inspect a durable v0.5 workflow')
        command.add_argument('--job',required=True)
        if name=='workflow-checkpoint':
            command.add_argument('--request',type=Path,required=True,help='Trusted checkpoint object and optional updated task evidence')
    for action in ('controller','start'):
        controller = actions.add_parser(action,help='Run the controller' if action=='controller' else 'Start a detached controller')
        controller.add_argument('--codex-exe',type=Path,help='Exact installed Codex executable; enables callbacks')
        if action=='controller':
            controller.add_argument('--once',action='store_true')
    status = actions.add_parser('status',help='Read durable state and result references')
    status.add_argument('--run')
    actions.add_parser('pause',help='Pause starting new local jobs')
    actions.add_parser('resume',help='Allow queued local jobs to start; does not restart interrupted generation')
    actions.add_parser('recover',help='Reconcile durable workflow evidence without executing jobs or sending callbacks')
    actions.add_parser('shutdown',help='Stop controller dispatch after the current callback; workers finish independently')
    cancel = actions.add_parser('cancel',help='Cancel a run, or just the specified job')
    cancel.add_argument('--run',required=True)
    cancel.add_argument('--job')
    init = actions.add_parser('init-review',help='Create one dedicated read-only Codex session and save its exact ID')
    init.add_argument('--run',required=True)
    init.add_argument('--codex-exe',type=Path,required=True)
    session = actions.add_parser('reconcile-session',help='Enable a recorded session only after inspecting uncertain initialization')
    session.add_argument('--run',required=True)
    session.add_argument('--evidence',required=True)
    reconcile = actions.add_parser('reconcile',help='Resolve uncertain delivery after inspecting evidence')
    reconcile.add_argument('--event',required=True)
    reconcile.add_argument('--disposition',choices=['delivered','not_delivered'],required=True)
    reconcile.add_argument('--evidence',required=True)
    decide = actions.add_parser('decide',help='Record supervising Codex/user review and validation')
    decide.add_argument('--event',required=True)
    decide.add_argument('--outcome',choices=['accepted','corrected','rejected','further_work'],required=True)
    decide.add_argument('--validation',required=True)
    decide.add_argument('--local',action='store_true',help='Record supervising review locally, without sending a callback; uncertain delivery still requires reconciliation')
    final = actions.add_parser('finalize',help='Finalize only after every job and review is resolved')
    final.add_argument('--run',required=True)
    final.add_argument('--summary',required=True)
    final.add_argument('--validation-passed',action='store_true')
    actions.add_parser('dock',help='Open the Tk companion dock; controller lifecycle is independent')


def run(args, config):
    from .companion import git_identity, submit, serve
    from .selection import discover, select_model
    store = CompanionStore(config.data_dir/'companion')
    action = args.action
    result = None
    if action.startswith('contract-'):
        from .selective_cli import run as selective_run
        result = selective_run(args, config, store)
    elif action=='inventory':
        result = store.annotate_inventory(asyncio.run(discover(config)),config.endpoint)
    elif action=='select':
        selected = select_model(asyncio.run(discover(config)),args.model)
        store.setting('default_model',selected['name'])
        result = selected
    elif action=='create':
        if config.source_root is None:
            raise ValueError('Configure source_root first')
        repository, revision = git_identity(config.source_root)
        result = {'run_id':store.create_run(repository,revision),'repository':repository,'base_revision':revision}
    elif action=='submit':
        with args.request.open('rb') as stream:
            raw = stream.read(100001)
        if len(raw)>100000:
            raise ValueError('Request exceeds 100,000 bytes')
        request = json.loads(raw)
        if not {'task_key','tool','objective','content'}<=set(request) or set(request)-{'task_key','tool','objective','content','role','routing','consensus','roles'}:
            raise ValueError('Request requires task_key, tool, objective and content; optional role/routing/consensus/roles')
        result = {'job_id':asyncio.run(submit(store,config,args.run,**request,model=args.model,
                                            execution=args.execution,
                                            no_deadline=args.no_deadline or config.no_inference_deadline))}
    elif action in ('workflow-submit','workflow-next','workflow-checkpoint','workflow-status'):
        from .companion_workflows import submit_workflow, follow_workflow, service_for
        request = {}
        if action in ('workflow-submit','workflow-checkpoint'):
            with args.request.open('rb') as stream:
                raw = stream.read(100001)
            if len(raw)>100000:
                raise ValueError('Request exceeds 100,000 bytes')
            request = json.loads(raw)
        if action=='workflow-submit':
            if set(request)!={'task_key','task'}:
                raise ValueError('Workflow request requires task_key and task')
            result = {'job_id':asyncio.run(submit_workflow(store,config,args.run,**request))}
        elif action=='workflow-status':
            job = store.job(args.job)
            if job['request'].get('execution')!='workflow':
                raise ValueError('Job is not a workflow operation')
            engine = service_for(store,job).workflows
            # Lookup only; never starts or replays interrupted work.
            from .workflow import digest
            with engine.ledger.store.connect() as db:
                row = db.execute('SELECT id FROM workflow_runs WHERE task_key=?',
                    (digest(job['request']['workflow_task']['task_id']),)).fetchone()
            result = engine.status(row[0]) if row else {'state':'not_started'}
        else:
            if action=='workflow-checkpoint' and ('checkpoint' not in request or set(request)-{'checkpoint','task'}):
                raise ValueError('Supply checkpoint and optional updated task')
            result = {'job_id':follow_workflow(store,args.job,**request)}
    elif action=='controller':
        serve(store.directory,args.codex_exe,args.once)
    elif action=='start':
        from .process_control import Lock, detached, identity
        # Check first, then the child takes its own lifetime lock. Concurrent starts
        # may create one losing child, but never two controller owners.
        with Lock(store.directory/'controller.lock'):
            pass
        argv = [sys.executable,'-B','-m','localagentbridge.companion','controller',str(store.directory)]
        if args.codex_exe:
            argv.append(str(args.codex_exe.resolve(strict=True)))
        process = detached(argv,Path(__file__).resolve().parents[1],store.directory/'controller.stdout.log',store.directory/'controller.stderr.log')
        result = {'controller':identity(process.pid),'directory':str(store.directory)}
    elif action=='status':
        result = store.snapshot(args.run)
    elif action=='recover':
        from .companion_recovery import recover
        result = {'recovery':recover(store)}
    elif action in ('pause','resume'):
        result = {'paused':store.setting('paused',action=='pause')}
    elif action=='shutdown':
        result = {'controller_stop_requested':store.setting('controller_stop',True)}
    elif action=='cancel':
        store.cancel(args.run,args.job)
        result = store.snapshot(args.run)
    elif action=='init-review':
        from .callbacks import create_session
        result = create_session(store,args.run,args.codex_exe)
    elif action=='reconcile':
        store.reconcile(args.event,args.disposition,args.evidence)
        result = {'event_id':args.event,'reconciled':True}
    elif action=='reconcile-session':
        store.reconcile_session(args.run,args.evidence)
        result = {'run_id':args.run,'session_reconciled':True}
    elif action=='decide':
        store.decide(args.event,args.outcome,args.validation,local=args.local)
        result = {'event_id':args.event,'decision':args.outcome}
    elif action=='finalize':
        result = {'state':store.finalize(args.run,args.summary,args.validation_passed)}
    elif action=='dock':
        from .dock import run_dock
        run_dock(config,store)
    if result is not None:
        # Redirected Windows stdout may use cp1252. JSON escapes preserve every
        # model/evidence character without depending on the terminal encoding.
        print(json.dumps(result,indent=2,ensure_ascii=True))
