"""Reconcile durable workflow evidence without executing any work or decision."""
from contextlib import contextmanager
import json
import sqlite3

from .process_control import Lock
from .telemetry import Store
from .workflow_store import WorkflowStore
from .workflow_recovery import RecoveryJournal, digest
from .schemas import compact


def legacy_receipt(journal, job, jobs):
    """Import only a uniquely attributable old committed transition with packets.

    Old hashes alone cannot recover content. A checkpoint requires its explicit
    intent, matching decision event, saved predecessor and exact successor version.
    """
    req = job['request']
    with journal.ledger.store.connect() as db:
        db.execute('BEGIN IMMEDIATE')
        existing = journal.operation(db,job['id'])
        if existing:
            return journal.read_receipt(existing) if existing['receipt'] else None
        row = db.execute('SELECT * FROM workflow_runs WHERE task_key=?',
                         (digest(req['workflow_task']['task_id']),)).fetchone()
        if not row:
            raise ValueError('No committed workflow output or transition exists; no replay')
        if row['catalog']!=req['workflow_policy']:
            raise ValueError('Legacy workflow policy identity differs')
        if req['workflow_id'] and req['workflow_id']!=row['id']:
            raise ValueError('Legacy workflow identity differs')
        base = req['version'] if req['version'] is not None else 0
        latest = db.execute('SELECT * FROM workflow_events WHERE run_id=? ORDER BY id DESC LIMIT 1',
                            (row['id'],)).fetchone()
        predecessors = [(j.get('result') or {}).get('answer',{}).get('workflow') for j in jobs]
        previous = next((p for p in predecessors if p and p['run_id']==row['id'] and p['version']==base),None)
        checkpoint = req['checkpoint']
        if checkpoint:
            matches = (previous and previous['state'] in ('waiting_for_codex','handed_off','cancelled')
                and row['version']==base+1 and latest['kind']=='codex_'+checkpoint['action']
                and latest['reason']==digest(checkpoint['note'])
                and latest['stage_id']==previous['next_stage'])
            peers = [j for j in jobs if j['request'].get('execution')=='workflow'
                and j['request'].get('workflow_id')==row['id'] and j['request'].get('version')==base
                and j['request'].get('checkpoint')==checkpoint and j['attempt_id']]
        else:
            stage = previous['next_stage'] if previous else json.loads(row['plan'])['stages'][0]['id']
            delta = 2 if latest['kind']=='role_completed' else 1
            matches = ((previous is not None or base==0) and row['version']==base+delta
                and latest['kind'] in ('role_completed','checkpoint','skipped') and latest['stage_id']==stage)
            peers = [j for j in jobs if j['request'].get('execution')=='workflow'
                and j['request']['workflow_task']['task_id']==req['workflow_task']['task_id']
                and j['request'].get('version')==req['version'] and not j['request'].get('checkpoint')
                and j['attempt_id']]
        if not matches or len(peers)!=1 or peers[0]['id']!=job['id']:
            raise ValueError('Legacy transition attribution is ambiguous or stale; supervisor inspection required')
        available = {}
        for candidate in jobs:
            other = candidate['request']
            if other.get('execution')!='workflow' or other['workflow_task']['task_id']!=req['workflow_task']['task_id']:
                continue
            packets = other['handoffs'] + ((candidate.get('result') or {}).get('answer',{}).get('handoffs') or [])
            available.update({digest(p):p for p in packets})
        refs = db.execute('''SELECT r.* FROM workflow_results r WHERE run_id=? AND version=(
            SELECT MAX(x.version) FROM workflow_results x WHERE x.run_id=r.run_id
            AND x.stage_id=r.stage_id AND x.skill_id=r.skill_id) ORDER BY r.rowid''',(row['id'],)).fetchall()
        if any(r['digest'] not in available or r['snapshot']!=row['snapshot'] for r in refs):
            raise ValueError('Legacy handoff content was never durably saved here; hashes cannot reconstruct it')
        db.execute('''INSERT INTO companion_operations
            (id,attempt,request_digest,request,started,run_id,base_version,phase)
            VALUES(?,?,?,?,?,?,?,'started')''',
            (job['id'],job['attempt_id'],digest(req),compact(req),job['started'],row['id'],base))
        for ref in refs:
            packet = available[ref['digest']]
            if (packet['stage_id'],packet['skill_id'])!=(ref['stage_id'],ref['skill_id']):
                raise ValueError('Legacy packet identity mismatch')
            db.execute('INSERT INTO companion_payloads VALUES(?,?,?,?,?,?,?,?)',
                (job['id'],row['id'],ref['stage_id'],ref['skill_id'],ref['version'],compact(packet),ref['digest'],ref['snapshot']))
        return journal.make_receipt(db,journal.operation(db,job['id']),'succeeded')


def recover_locked(store):
    """Caller owns worker.lock. No repository/model/authentication operations."""
    jobs = store.snapshot()['jobs']
    candidates = [j for j in jobs if j['request'].get('execution')=='workflow' and j['attempt_id']]
    if not candidates:
        return []
    journal = RecoveryJournal(WorkflowStore(Store(store.directory/'usage')))
    results = []
    for job in candidates:
        try:
            with journal.ledger.store.connect() as db:
                op = journal.operation(db,job['id'])
            if op:
                if not op['receipt']:
                    if job['state']=='failed':
                        raise ValueError('Execution failed before a transition receipt; inspect the original error')
                    journal.prepare_interrupted(job)
                disposition = journal.deliver(store,job['id'])
            elif job['result'] is not None:
                disposition = 'legacy_event_repaired' if store.repair_completion_event(job['id']) else 'legacy_result_preserved'
            elif job['state'] in ('running','interrupted'):
                legacy_receipt(journal,job,jobs)
                disposition = journal.deliver(store,job['id'])
            else:
                disposition = 'terminal_state_preserved'
            results.append({'job_id':job['id'],'disposition':disposition})
        except (ValueError,KeyError,TypeError,sqlite3.DatabaseError) as error:
            detail = type(error).__name__+': '+str(error)
            store.recovery_issue(job['id'],detail)
            results.append({'job_id':job['id'],'disposition':'intervention_required','detail':detail})
        current = store.job(job['id'])
        if current['state']=='running':
            with store.db() as db:
                reviewed = db.execute('SELECT 1 FROM events WHERE job_id=?',(job['id'],)).fetchone()
            if not reviewed:
                store.complete(job['id'],job['attempt_id'],state='interrupted',
                    error='Worker exited before recoverable completion; inspect companion recover diagnostics; no replay')
    return results


def recover(store):
    with Lock(store.directory/'worker.lock'):
        return recover_locked(store)


@contextmanager
def verification_guard(store):
    """Hold workflow version stable while finalizing in the companion database."""
    path = store.directory/'usage/usage.sqlite3'
    if not path.exists():
        yield None
        return
    db = sqlite3.connect(path,timeout=15)
    db.row_factory = sqlite3.Row
    try:
        with db:
            db.execute('BEGIN IMMEDIATE')
            yield db
    finally:
        db.close()


def verify_final_workflows(ledger, jobs):
    latest = {}
    for job in sorted(jobs,key=lambda j:j['created']):
        req = json.loads(job['request'])
        if req.get('execution')=='workflow':
            latest[req['workflow_task']['task_id']] = (req,json.loads(job['result']) if job['result'] else {})
    for task_id,(req,result) in latest.items():
        state = result.get('answer',{}).get('workflow') or {}
        if ledger is None or state.get('state')!='codex_verified':
            raise ValueError('Unresolved workflow checkpoints prevent successful finalization')
        row = ledger.execute('SELECT * FROM workflow_runs WHERE task_key=?',(digest(task_id),)).fetchone()
        checkpoint = req.get('checkpoint') or {}
        event = ledger.execute('SELECT * FROM workflow_events WHERE run_id=? ORDER BY id DESC LIMIT 1',
                               (state.get('run_id'),)).fetchone()
        if (not row or row['id']!=state.get('run_id') or row['version']!=state.get('version')
                or row['state']!='codex_verified' or row['catalog']!=req['workflow_policy']
                or checkpoint.get('action')!='accept' or not event or event['kind']!='codex_accept'
                or event['reason']!=digest(checkpoint.get('note'))):
            raise ValueError('Final verification requires the current committed supervisor checkpoint')
