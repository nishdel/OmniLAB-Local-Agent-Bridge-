"""Explicit supervisor integration. No worker can reach this controller/database."""
import base64
import hashlib
import json
from pathlib import Path

from .companion import git_identity
from .sandbox import DockerSandbox, git_snapshot, tree_hash, command
from .selective import artifact_dir, atomic_json, verify
from .task_contract import Contract, digest
from .task_store import TaskStore, effective_jobs


async def integrate(store, job_id, candidate_hash, sandbox_factory=DockerSandbox):
    tasks = TaskStore(store)
    job = store.job(job_id)
    state = tasks.get(job_id)
    if (not state or state['lane'] != 'local_implementation' or state['review_status'] != 'accepted'
            or state['accepted_hash'] != candidate_hash or state['candidate_hash'] != candidate_hash
            or state['verification_status'] != 'passed'):
        raise ValueError('Exact candidate requires successful verification and supervisor acceptance')
    c = Contract.model_validate(job['request']['contract'])
    repository, head = git_identity(c.repository)
    if head != c.base_revision:
        raise ValueError('Integration base changed; create a new reviewed contract')
    history = store.snapshot(job['run_id'])['jobs']
    jobs = effective_jobs(history)
    for key in c.dependencies:
        dependency = tasks.get(jobs[key]['id'])
        if dependency['review_status'] != 'accepted' or (dependency['lane'] == 'local_implementation' and
                dependency['integration_status'] != 'integrated'):
            raise ValueError('Integrate dependencies in order')
    files = git_snapshot(repository, head, c.limits.snapshot_bytes)
    integrated = [j for j in history if tasks.get(j['id']) and tasks.get(j['id'])['integration_status'] == 'integrated']
    integrated.sort(key=lambda j: (tasks.get(j['id'])['evidence'] or {}).get('integrated_at', 0))
    for prior in integrated:
        packet = json.loads((artifact_dir(store, prior)/'candidate.json').read_text())
        if digest(packet) != tasks.get(prior['id'])['accepted_hash']:
            raise ValueError('Previously integrated candidate was modified')
        for name, change in packet['changes'].items():
            files[name] = base64.b64decode(change['content'], validate=True)
    packet = json.loads((artifact_dir(store, job)/'candidate.json').read_text())
    if digest(packet) != candidate_hash:
        raise ValueError('Candidate artifact changed after review')
    after = dict(files)
    for name, change in packet['changes'].items():
        before_hash = hashlib.sha256(files[name]).hexdigest() if name in files else None
        if state['integration_status'] != 'integrated' and before_hash != change['before_sha256']:
            raise ValueError('Candidate conflicts with integrated changes')
        after[name] = base64.b64decode(change['content'], validate=True)
    # Reject unrelated edits/untracked files; compare every tracked byte without following links.
    status = command(['git', '-C', repository, 'ls-files', '--others', '--exclude-standard']).decode()
    permitted_untracked = {k for j in integrated for k in json.loads((artifact_dir(store,j)/'candidate.json').read_text())['changes']}
    if state['integration_status'] == 'integrating':
        permitted_untracked.update(packet['changes'])
        permitted_untracked.update(name+'.lab-'+job['attempt_id']+'.tmp' for name in packet['changes'])
    if set(status.splitlines()) - permitted_untracked:
        raise ValueError('Untracked work prevents automatic integration')
    current = {}
    for name in after:
        path = Path(repository)/name
        if any(p.is_symlink() or (hasattr(p, 'is_junction') and p.is_junction())
               for p in [path,*list(path.parents)[:len(Path(name).parts)-1]]):
            raise ValueError('Reparse/link in integration target')
        current[name] = path.read_bytes() if path.exists() else None
    before_current = {k: v for k, v in current.items() if v is not None}
    current_hash = tree_hash(before_current)
    if current_hash == tree_hash(after) and state['integration_status'] in ('integrating', 'integrated'):
        evidence = (state['evidence'] or {})
        if evidence.get('integration_tree_hash') != current_hash:
            raise ValueError('Integration receipt unavailable; inspect before reconciliation')
    else:
        partial = state['integration_status']=='integrating' and (state['evidence'] or {}).get('integration_tree_hash')==tree_hash(after)
        if current_hash != tree_hash(files) and not (partial and all(
                current.get(k) in (files.get(k), after.get(k)) for k in after)):
            raise ValueError('Unrelated staged/unstaged edits prevent integration')
        sandbox = sandbox_factory(job['request']['policy']['sandbox'])
        sandbox.preflight()
        # A new attempt identity makes combined integration checks independent of candidate checks.
        import uuid
        check_job = dict(job, attempt_id=str(uuid.uuid5(uuid.UUID(job['attempt_id']), 'integration')))
        # Re-run the union of checks for the assembled feature, including earlier children.
        from .task_contract import Check
        combined = []
        for checked in [*integrated,job]:
            for item in checked['request']['contract']['checks']:
                combined.append(Check(**(item | {'id': checked['task_key'][:50]+'.'+item['id'][:40]})))
        check_contract = c.model_copy(update={'checks':combined})
        checks = await verify(store, check_job, sandbox, check_contract, after, 'verify')
        if not all(v['exit_code'] == 0 and not v['timed_out'] and not v['skip_detected'] and not v['output_truncated'] for v in checks):
            raise ValueError('Combined integration checks failed; source was not modified')
        evidence = (state['evidence'] or {}) | {'integration_checks': checks, 'integration_tree_hash': tree_hash(after),
                                                'integrated_at': store.clock()}
        tasks.update(job, integration_status='integrating', evidence=evidence)
        patch = artifact_dir(store, job)/'candidate.patch'
        if hashlib.sha256(patch.read_bytes()).hexdigest() != evidence['patch_sha256']:
            raise ValueError('Candidate patch changed after review')
        if not partial:
            command(['git', '-C', repository, 'apply', '--check', str(patch)])
        # Git on Windows can convert reviewed LF bytes to CRLF while applying.
        # Preserve the exact independently verified bytes instead. The controller
        # records intent first and recognizes only before/after bytes on recovery.
        import os
        import stat
        for name in packet['changes']:
            destination = Path(repository)/name
            if destination.exists() and destination.read_bytes()==after[name]:
                continue
            destination.parent.mkdir(parents=True, exist_ok=True)
            temporary = destination.with_name(destination.name+'.lab-'+job['attempt_id']+'.tmp')
            if temporary.exists():
                if temporary.is_symlink() or temporary.read_bytes()!=after[name]:
                    raise ValueError('Uncertain integration temporary artifact; inspect before resuming')
            else:
                with temporary.open('xb') as stream:
                    stream.write(after[name])
                    stream.flush()
                    os.fsync(stream.fileno())
            if destination.exists():
                temporary.chmod(stat.S_IMODE(destination.stat().st_mode))
            os.replace(temporary,destination)
        if tree_hash({k: (Path(repository)/k).read_bytes() for k in after}) != tree_hash(after):
            raise ValueError('Post-integration tree differs from independently verified candidate')
    tasks.update(job, integration_status='integrated', evidence=evidence)
    return {'integrated': True, 'candidate_hash': candidate_hash, 'tree_hash': tree_hash(after),
            'committed': False, 'checks': evidence.get('integration_checks')}
