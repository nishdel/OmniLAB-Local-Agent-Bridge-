"""Prepare, check, mock-run and report a bounded comparison; no live dispatch.

Run from the candidate checkout. Live work uses the existing reviewed LAB CLI,
after approval, with the frozen contract and isolated store identified here.
"""
import argparse
import asyncio
from contextlib import ExitStack
import hashlib
import json
from pathlib import Path
import socket
import subprocess
import sys
import time
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT/'scripts'))
from comparison_fixtures import FIXTURES
from localagentbridge.comparison import empty_attempt, report, energy, next_step
from localagentbridge.companion_store import CompanionStore
from localagentbridge.task_contract import Contract, digest


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    with Path(path).open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(value, indent=2, allow_nan=False)+'\n')


def git(repository, *args):
    return subprocess.check_output(['git', '-C', str(repository), *args],
        stderr=subprocess.PIPE, text=True, encoding='utf-8').strip()


def prepare(output, plan_path=ROOT/'examples/comparison-plan.json'):
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    plan = json.loads(Path(plan_path).read_text(encoding='utf-8'))
    if plan['trials'] != 2 or set(plan['arms']) != set('ABCD') or plan['arms']['D']['status'] != 'blocked':
        raise ValueError('This preparation requires the reviewed four-arm/two-trial plan with Strata blocked')
    candidate = git(ROOT, 'rev-parse', 'HEAD')
    source_hashes = {p: sha(ROOT/p) for p in (ROOT/'PUBLIC-FILES.txt').read_text().splitlines()
                     if p and not p.startswith('#')}
    cases = []
    for trial in range(1, 3):
        for fixture_id in plan['fixture_order']:
            fixture = next(f for f in FIXTURES if f['id'] == fixture_id)
            files = dict(fixture['files'], **{'acceptance.py': fixture['authority']})
            if sum(len(v.encode()) for v in files.values()) > plan['shared_context']['maximum_fixture_utf8_bytes']:
                raise ValueError('Common fixture context ceiling exceeded')
            for arm in plan['arm_order_by_trial'][trial-1]:
                profile = plan['arms'][arm]
                key = f'{fixture_id}-t{trial}-{arm}'
                folder = output/key
                repo = folder/'workspace'
                repo.mkdir(parents=True)
                for name, content in files.items():
                    (repo/name).write_text(content, encoding='utf-8', newline='\n')
                git(repo, 'init', '--quiet')
                git(repo, 'add', '--', *files)
                git(repo, '-c', 'user.name=LAB synthetic fixture', '-c', 'user.email=fixture@example.invalid',
                    '-c', 'commit.gpgsign=false', 'commit', '--quiet', '-m', 'Frozen synthetic comparison fixture')
                base = git(repo, 'rev-parse', 'HEAD')
                store = CompanionStore(folder/'state/companion')
                store.setting('paused', True)
                settings = profile['settings']
                contract = None
                if arm != 'A':
                    implementation = fixture['lane'] == 'local_implementation'
                    contract = Contract(task_id=key, objective=fixture['objective'],
                        requirement_ref='readiness-comparison-v1/'+fixture_id,
                        acceptance=fixture['acceptance'], non_goals=['No network, dependencies, unrelated edits or acceptance changes'],
                        repository=str(repo), base_revision=base, permitted_files=fixture['editable'],
                        context_files=list(fixture['files']),
                        acceptance_files=['acceptance.py'] if implementation else [],
                        operations=['read','edit','test'] if implementation else ['read'],
                        requested_lane=fixture['lane'], orchestration='direct', backend=profile['backend'],
                        model=profile['model'], exact_identity=profile['identity'], risk='low', ambiguity=False,
                        coherent_scope=True, reversible=True, category=fixture['category'],
                        supervisor_approved=False,  # Approval is a subsequent trusted action, not preparation.
                        checks=[{'id':'acceptance', 'argv':['python','acceptance.py'],
                                 'covers':list(fixture['acceptance'])}] if implementation else [],
                        limits=dict(context_tokens=settings['context_tokens'],
                            context_safety_tokens=settings['context_safety_tokens'],
                            output_tokens=settings['output_tokens'], output_bytes=settings['output_bytes'],
                            steps=8, self_repair_cycles=settings['self_repair_cycles'],
                            implementation_attempts=1 if arm == 'D' else 2, transport_retries=0,
                            attempt_seconds=600, test_seconds=15))
                    write(folder/'contract.json', [contract.model_dump()])
                request = dict(objective=fixture['objective'], acceptance=fixture['acceptance'],
                               context_files=list(fixture['files']), editable_files=fixture['editable'],
                               independent_acceptance=['python','acceptance.py'],
                               manual_review='Source-grounded independent review of all claims/diffs, even when checks pass')
                write(folder/'request.json', request)
                row = empty_attempt(arm=arm, fixture=fixture_id, trial=trial, attempt=1,
                    candidate=candidate, settings_sha256=digest(profile), fixture_sha256=digest(fixture))
                row['lane'] = fixture['lane']
                if arm == 'D':
                    row.update(outcome='blocked', failure_class='qualification',
                               admission={'status':'blocked','reason':profile['reason']})
                write(folder/'attempt-template.json', row)
                cases.append(dict(key=key, arm=arm, fixture=fixture_id, trial=trial,
                    directory=str(folder), repository=str(repo), base_revision=base,
                    files_sha256={name: sha(repo/name) for name in files},
                    contract_sha256=sha(folder/'contract.json') if contract else None,
                    request_sha256=sha(folder/'request.json'), store=str(store.directory),
                    status=row['outcome'], cloud_session=None,
                    proposed_lane=fixture['lane'], settings_sha256=digest(profile),
                    fixture_sha256=digest(fixture),
                    attempt_template_sha256=sha(folder/'attempt-template.json')))
    manifest = dict(schema_version=1, mode='prepared_not_run', candidate_commit=candidate,
        candidate_source_sha256=digest(source_hashes), source_sha256=source_hashes,
        plan=plan, plan_sha256=sha(plan_path), cases=cases,
        freshness='New synthetic cases; evaluator knows authorities. Fresh generation sessions required; not a blind held-out claim.',
        live_authorized=False, startup_actions_executed=[],
        isolation='Separate Git snapshots and paused empty stores. No controller or model is started.',
        package_identity=None)
    write(output/'manifest.json', manifest)
    return manifest


def verify(manifest_path):
    manifest = json.loads(Path(manifest_path).read_text())
    if manifest.get('live_authorized') or manifest['plan']['arms']['D']['status'] != 'blocked':
        raise ValueError('Offline manifest cannot authorize live work or unblock Strata')
    plan_path = ROOT/'examples/comparison-plan.json'
    if (sha(plan_path) != manifest['plan_sha256'] or
            json.loads(plan_path.read_text()) != manifest['plan']):
        raise ValueError('Embedded plan differs from the reviewed canonical plan')
    if digest(manifest['source_sha256']) != manifest['candidate_source_sha256']:
        raise ValueError('Candidate source identity is inconsistent')
    for path, want in manifest['source_sha256'].items():
        if sha(ROOT/path) != want:
            raise ValueError('Candidate source changed: '+path)
    binding = manifest.get('package_identity')
    if binding:
        if sha(binding['path']) != binding['sha256']:
            raise ValueError('Candidate package identity changed')
        package = json.loads(Path(binding['path']).read_text())
        if (package['source_sha256'] != manifest['source_sha256'] or
                sha(package['wheel']) != binding['wheel_sha256'] or
                package['wheel_sha256'] != binding['wheel_sha256'] or
                digest(package['runtime_sha256']) != binding['runtime_tree_sha256']):
            raise ValueError('Candidate package does not match the frozen source/wheel/runtime')
        for name, want in package['runtime_sha256'].items():
            if sha(Path(package['runtime_root'])/name) != want:
                raise ValueError('Installed candidate runtime changed: '+name)
    for case in manifest['cases']:
        folder, repo = Path(case['directory']), Path(case['repository'])
        if git(repo, 'rev-parse', 'HEAD') != case['base_revision']:
            raise ValueError('Fixture revision changed')
        for name, want in case['files_sha256'].items():
            if sha(repo/name) != want:
                raise ValueError('Frozen fixture changed: '+name)
        for name, field in [('request.json','request_sha256'), ('attempt-template.json','attempt_template_sha256'),
                            ('contract.json','contract_sha256')]:
            if case[field] and sha(folder/name) != case[field]:
                raise ValueError('Frozen '+name+' changed')
        if case.get('disabled_config'):
            import tomllib
            config_path = Path(case['disabled_config'])
            if sha(config_path) != case['disabled_config_sha256']:
                raise ValueError('Frozen disabled configuration changed')
            config = tomllib.loads(config_path.read_text())
            policy = config['selective']
            if (policy['enabled'] or policy['implementation_enabled'] or
                    policy['providers']['strata']['enabled'] or
                    Path(config['data_dir'])/'companion' != Path(case['store']) or
                    Path(config['source_root']) != repo):
                raise ValueError('Offline configuration must stay disabled and isolated')
        # Read-only check; do not initialize/migrate the acceptance store.
        import sqlite3
        with sqlite3.connect((Path(case['store'])/'companion.sqlite3').as_uri()+'?mode=ro', uri=True) as db:
            if db.execute('SELECT COUNT(*) FROM jobs').fetchone()[0] or not json.loads(
                    db.execute("SELECT value FROM settings WHERE key='paused'").fetchone()[0]):
                raise ValueError('Preparation store is no longer paused and empty')
    return manifest


def mock(manifest_path, output):
    """Exercise real LAB admission/execution/usage against in-process fakes only."""
    manifest = verify(manifest_path)
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    from comparison_mock import exercise
    attempts, reports, paths = [], [], []
    original_popen = subprocess.Popen
    def only_git(args, *a, **kw):
        if not isinstance(args, (list, tuple)) or str(args[0]).lower() != 'git':
            raise AssertionError('Mock harness forbids child processes except read-only Git snapshots')
        if 'archive' not in args:
            raise AssertionError('Unexpected Git command during mock dispatch')
        return original_popen(args, *a, **kw)
    def no_socket(*a, **kw):
        raise AssertionError('Mock harness forbids network/listener activity')
    # Windows asyncio creates an internal wakeup socketpair. Initialize it before
    # blocking application sockets; no HTTP/inference service is created.
    loop = asyncio.new_event_loop()
    with ExitStack() as stack:
        stack.callback(loop.close)
        stack.enter_context(patch.object(subprocess, 'Popen', only_git))
        for action in ('connect', 'connect_ex', 'bind', 'listen'):
            stack.enter_context(patch.object(socket.socket, action, no_socket))
        for case in manifest['cases']:
            row, usage, calls = loop.run_until_complete(exercise(case, output/case['key']))
            attempts.append(row)
            reports.append(usage)
            paths.extend(calls)
    combined = {'records':[r for u in reports for r in u.get('records', [])], 'categories':None}
    write(output/'attempts.json', attempts)
    write(output/'usage.json', combined)
    result = report(attempts, combined)
    result['mock_safety'] = dict(network_and_listeners='denied', non_git_child_processes='denied',
        transports='httpx.MockTransport only', request_paths=sorted(set(paths)),
        controller_started=False, docker_started=False, model_inference=False,
        strata_dispatched=False, rows=len(attempts))
    write(output/'report.json', result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='action', required=True)
    p = commands.add_parser('prepare'); p.add_argument('--output', type=Path, required=True)
    p = commands.add_parser('check'); p.add_argument('--manifest', type=Path, required=True)
    p = commands.add_parser('mock'); p.add_argument('--manifest', type=Path, required=True); p.add_argument('--output', type=Path, required=True)
    p = commands.add_parser('report'); p.add_argument('--attempts', type=Path, required=True); p.add_argument('--usage', type=Path, required=True)
    p.add_argument('--equivalence-evidence'); p.add_argument('--output', type=Path, required=True)
    p = commands.add_parser('energy'); p.add_argument('--samples', type=Path, required=True)
    p.add_argument('--start', type=float, required=True); p.add_argument('--end', type=float, required=True)
    p.add_argument('--max-gap', type=float, default=5); p.add_argument('--idle-watts', type=float)
    p.add_argument('--output', type=Path, required=True)
    p = commands.add_parser('sample'); p.add_argument('--output', type=Path, required=True)
    p.add_argument('--seconds', type=float, required=True); p.add_argument('--power-status', type=Path)
    p = commands.add_parser('summarize-telemetry'); p.add_argument('--samples', type=Path, required=True)
    p.add_argument('--start', type=float, required=True); p.add_argument('--end', type=float, required=True)
    p.add_argument('--max-gap', type=float, default=5); p.add_argument('--output', type=Path, required=True)
    p = commands.add_parser('next'); p.add_argument('--manifest', type=Path, required=True)
    p.add_argument('--attempts', type=Path, required=True); p.add_argument('--usage', type=Path, required=True)
    p.add_argument('--elapsed-seconds', type=float, required=True); p.add_argument('--evidence-bytes', type=int, required=True)
    args = parser.parse_args()
    if args.action == 'prepare':
        value = prepare(args.output)
        print(json.dumps({'candidate':value['candidate_commit'], 'cases':len(value['cases']), 'live_authorized':False}))
    elif args.action == 'check':
        value = verify(args.manifest)
        print(json.dumps({'verified_cases':len(value['cases']), 'live_authorized':False}))
    elif args.action == 'mock':
        print(json.dumps(mock(args.manifest, args.output)['mock_safety']))
    elif args.action == 'report':
        value = report(json.loads(args.attempts.read_text()), json.loads(args.usage.read_text()),
                       equivalence_evidence=args.equivalence_evidence)
        write(args.output, value)
    elif args.action == 'energy':
        value = energy(json.loads(args.samples.read_text()), args.start, args.end,
                       max_gap_seconds=args.max_gap, idle_watts=args.idle_watts)
        write(args.output, value)
    elif args.action == 'summarize-telemetry':
        from localagentbridge.comparison_telemetry import summarize
        rows = [json.loads(line) for line in args.samples.read_text().splitlines() if line.strip()]
        write(args.output, summarize(rows,args.start,args.end,args.max_gap))
    elif args.action == 'next':
        print(json.dumps(next_step(json.loads(args.manifest.read_text()), json.loads(args.attempts.read_text()),
            json.loads(args.usage.read_text()), elapsed_seconds=args.elapsed_seconds,
            evidence_bytes=args.evidence_bytes), indent=2))
    else:
        from localagentbridge.comparison_telemetry import capture
        print(json.dumps(capture(args.output, args.seconds, power_status=args.power_status)))


if __name__ == '__main__':
    main()
