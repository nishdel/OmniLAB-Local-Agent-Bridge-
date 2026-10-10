"""Opt-in actions in the existing companion CLI."""
import asyncio
import json
from pathlib import Path

from .task_contract import Contract
from .task_store import TaskStore


def add(actions):
    ingest = actions.add_parser('contract-usage-import', help='Import metadata from one explicit Codex rollout into existing accounting')
    ingest.add_argument('--rollout', type=Path, required=True)
    binding = actions.add_parser('contract-usage-bind', help='Trusted attribution of a whole cloud session/turn or local run/job')
    binding.add_argument('--kind', choices=['cloud','local'], required=True)
    binding.add_argument('--session', required=True)
    binding.add_argument('--logical-id', help='Exact complete cloud turn or local job; omit for the whole session/run')
    binding.add_argument('--run', required=True, help='Accounting run identity shared by its cloud and local work')
    binding.add_argument('--task')
    binding.add_argument('--category', choices=['implementation','evaluation','operating','unattributed'], required=True)
    binding.add_argument('--evidence', required=True)
    report = actions.add_parser('contract-usage-report', help='Report recorded investment and explicit savings coverage')
    report.add_argument('--since', type=float, default=0)
    report.add_argument('--cutoff', type=float)
    report.add_argument('--session', action='append', help='Cloud session IDs; local job receipts are retained')

    for name in ('contract-route', 'contract-submit'):
        parser = actions.add_parser(name, help='Dry-run routing' if name.endswith('route') else 'Submit approved bounded contracts')
        parser.add_argument('--request', type=Path, required=True, help='JSON array of supervisor contracts')
        if name.endswith('submit'):
            parser.add_argument('--run', required=True)
    review = actions.add_parser('contract-review', help='Record local supervisor review of an exact candidate')
    review.add_argument('--event', required=True)
    review.add_argument('--candidate', required=True)
    review.add_argument('--outcome', required=True, choices=['accepted', 'corrected', 'rejected', 'further_work'])
    review.add_argument('--validation', required=True)
    review.add_argument('--coverage', type=Path, required=True, help='Acceptance-ID to review-evidence JSON object')
    correction = actions.add_parser('contract-correct', help='One bounded supervisor-requested correction')
    correction.add_argument('--job', required=True)
    correction.add_argument('--note', required=True)
    reconcile = actions.add_parser('contract-resource-release', help='Reconcile an uncertain inference reservation')
    reconcile.add_argument('--job', required=True)
    reconcile.add_argument('--evidence', required=True)
    qualify = actions.add_parser('contract-qualify-start', help='Explicitly activate a disposable SDK tool-roundtrip probe')
    qualify.add_argument('--backend', choices=['ollama','strata'], required=True)
    qualify.add_argument('--model', required=True)
    qualify.add_argument('--activate', action='store_true')
    qualify.add_argument('--context-tokens', type=int, default=16384)
    qualify_record = actions.add_parser('contract-qualify-record', help='Export compatibility evidence after probe checks and supervisor acceptance')
    qualify_record.add_argument('--job', required=True)
    metric = actions.add_parser('contract-metric', help='Record phase measurements with explicit provenance')
    metric.add_argument('--job', required=True)
    metric.add_argument('--request', type=Path, required=True)
    integration = actions.add_parser('contract-integrate', help='Supervisor integration after exact-candidate review and isolated combined checks')
    integration.add_argument('--job', required=True)
    integration.add_argument('--candidate', required=True)


def read(path):
    raw = path.read_bytes()
    if len(raw) > 1000000:
        raise ValueError('Contract input is too large')
    return json.loads(raw)


async def contract_requests(config, raw):
    """Shared CLI/MCP admission; never broaden the configured repository."""
    from .selective import prepare
    from .task_contract import validate_graph
    from .companion import git_identity
    if not isinstance(raw, list) or not 1 <= len(raw) <= 40:
        raise ValueError('Supply an array of 1..40 meaningful contracts')
    from .local_profile import resolve_contract
    from .companion_store import CompanionStore
    selected = CompanionStore(config.data_dir/'companion').setting('default_model')
    contracts = [resolve_contract(config, c, selected) for c in raw]
    validate_graph(contracts)
    if config.source_root is None:
        raise ValueError('Configure source_root before contract admission')
    repository, revision = git_identity(config.source_root)
    if any(c.repository != repository or c.base_revision != revision for c in contracts):
        raise ValueError('Contract repository/base differs from selected source_root HEAD')
    return await prepare(config, contracts)


def run(args, config, store):
    from .selective import prepare, correction
    if args.action == 'contract-usage-import':
        from .codex_usage import RolloutReader
        from .telemetry import Store
        path = args.rollout.resolve(strict=True)
        if (not any(path.is_relative_to(config.codex_home/root) for root in ('sessions','archived_sessions'))
                or not path.name.startswith('rollout-') or path.suffix!='.jsonl'):
            raise ValueError('Select an explicit rollout within the configured Codex session directory')
        usage = Store(store.directory/'usage')
        reader = RolloutReader(config,usage)
        consumed = 0
        while consumed < 64*1024*1024:
            count = reader.read(path,1024*1024)
            if not count:
                break
            consumed += count
        return {'bytes_processed':consumed,'source':'rollout cumulative deltas','database':str(usage.path),
                'coverage':'Metadata only through persisted checkpoint; pending/incomplete lines remain for next import'}
    if args.action == 'contract-usage-bind':
        from .usage_report import bind_usage
        return bind_usage(store, kind=args.kind, session_id=args.session, logical_id=args.logical_id,
                          run_id=args.run, task_id=args.task, category=args.category, evidence=args.evidence)
    if args.action == 'contract-usage-report':
        from .usage_report import investment, operating_savings
        return {'investment':investment(store,args.since,args.cutoff,args.session),
                'operating_savings':operating_savings(None,None)}
    if args.action in ('contract-route', 'contract-submit'):
        raw = read(args.request)
        requests = asyncio.run(contract_requests(config, raw))
        if args.action == 'contract-route':
            return [{'task_id': r['contract']['task_id'], **r['routing']} for r in requests]
        return {'job_ids': TaskStore(store).submit_many(args.run, requests), 'routing':[r['routing'] for r in requests]}
    if args.action == 'contract-review':
        TaskStore(store).review(args.event, args.outcome, args.validation, args.candidate, read(args.coverage))
        return {'review_recorded': True}
    if args.action == 'contract-correct':
        return {'job_id': correction(store, args.job, args.note)}
    if args.action == 'contract-resource-release':
        TaskStore(store).reconcile_resource(args.job, args.evidence)
        return {'resource_reconciled': True}
    if args.action == 'contract-qualify-start':
        from .qualification import start
        return asyncio.run(start(store,config,args.backend,args.model,args.activate,args.context_tokens))
    if args.action == 'contract-qualify-record':
        from .qualification import record
        return record(store,args.job)
    if args.action == 'contract-metric':
        from .measurements import record, summary
        record(store,args.job,**read(args.request))
        return summary(store,args.job)
    if args.action == 'contract-integrate':
        from .integration import integrate
        return asyncio.run(integrate(store, args.job, args.candidate))
    raise ValueError('Unknown contract action')
