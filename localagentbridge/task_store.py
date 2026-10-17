"""Additive contract evidence on the existing companion database; no shared conversation."""
import json
import uuid

from .companion_store import encode, submission_identity
from .task_contract import Contract, digest, validate_graph


def migrate(db):
    db.executescript("""
        CREATE TABLE IF NOT EXISTS contract_jobs (
          job_id TEXT PRIMARY KEY REFERENCES jobs(id), task_id TEXT NOT NULL,
          parent_id TEXT, lane TEXT NOT NULL, backend TEXT NOT NULL,
          execution_status TEXT NOT NULL DEFAULT 'queued',
          verification_status TEXT NOT NULL DEFAULT 'not_run',
          review_status TEXT NOT NULL DEFAULT 'awaiting_review',
          integration_status TEXT NOT NULL DEFAULT 'candidate',
          candidate_hash TEXT, accepted_hash TEXT, executor_id TEXT,
          dispatch_state TEXT NOT NULL DEFAULT 'not_dispatched',
          evidence TEXT, attempt_number INTEGER NOT NULL DEFAULT 1);
        CREATE TABLE IF NOT EXISTS contract_audit (
          id INTEGER PRIMARY KEY, job_id TEXT REFERENCES jobs(id), kind TEXT NOT NULL,
          created REAL NOT NULL, detail TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS task_measurements (
          job_id TEXT NOT NULL REFERENCES jobs(id), key TEXT NOT NULL, created REAL NOT NULL,
          payload TEXT NOT NULL, PRIMARY KEY(job_id,key));
        CREATE TABLE IF NOT EXISTS inference_reservation (
          singleton INTEGER PRIMARY KEY CHECK(singleton=1), job_id TEXT NOT NULL,
          attempt_id TEXT NOT NULL, backend TEXT NOT NULL, state TEXT NOT NULL);
    """)


class TaskStore:
    def __init__(self, store):
        self.store = store

    def audit(self, db, job_id, kind, detail):
        db.execute('INSERT INTO contract_audit(job_id,kind,created,detail) VALUES(?,?,?,?)',
                   (job_id, kind, self.store.clock(), encode(detail)))

    def submit_many(self, run_id, requests):
        """All nodes and dependencies commit together, including duplicate detection."""
        with self.store.db() as db:
            db.execute('BEGIN IMMEDIATE')
            run = db.execute('SELECT * FROM runs WHERE id=?', (run_id,)).fetchone()
            if not run or run['finalized'] or run['cancel_requested']:
                raise ValueError('Missing, finalized or cancelled run')
            prior = [json.loads(r[0]) for r in db.execute('SELECT request FROM jobs WHERE run_id=?', (run_id,))]
            by_key = {r['contract']['task_id']: r for r in prior if r.get('execution') == 'contract'}
            for request in requests:
                c = Contract.model_validate(request['contract'])
                if c.repository != run['repository'] or c.base_revision != run['base_revision']:
                    raise ValueError('Contract does not match selected repository/base')
                if request.get('correction_of'):
                    previous = db.execute('SELECT * FROM jobs WHERE id=? AND run_id=?',
                                          (request['correction_of'],run_id)).fetchone()
                    if not previous:
                        raise ValueError('Correction must reference an existing task in this run')
                    prior_request = json.loads(previous['request'])
                    prior_contract = Contract.model_validate(prior_request['contract'])
                    before = prior_contract.model_dump(exclude={'task_id','context'})
                    after = c.model_dump(exclude={'task_id','context'})
                    number = prior_request.get('attempt_number',1)+1
                    if (before != after or c.task_id != prior_contract.task_id+'.correction' or
                            not c.context.startswith(prior_contract.context+'\nSupervisor correction: ') or
                            request.get('attempt_number') != number or number > c.limits.implementation_attempts):
                        raise ValueError('Correction cannot change scope, acceptance or retry authority')
                if c.task_id in by_key and submission_identity(by_key[c.task_id]) != submission_identity(request):
                    raise ValueError('Task ID already names different work')
                by_key[c.task_id] = request
            validate_graph([Contract.model_validate(r['contract']) for r in by_key.values()])
            ids = []
            for request in requests:
                c = Contract.model_validate(request['contract'])
                old = db.execute('SELECT id FROM jobs WHERE run_id=? AND task_key=?', (run_id, c.task_id)).fetchone()
                if old:
                    ids.append(old[0])
                    continue
                job_id = str(uuid.uuid4())
                raw = encode(request)
                if len(raw.encode()) > 100000:
                    raise ValueError('Contract request exceeds 100,000 bytes')
                db.execute('INSERT INTO jobs(id,run_id,task_key,request,state,created) VALUES(?,?,?,?,?,?)',
                           (job_id, run_id, c.task_id, raw, 'queued', self.store.clock()))
                db.execute('INSERT INTO contract_jobs(job_id,task_id,parent_id,lane,backend,attempt_number) VALUES(?,?,?,?,?,?)',
                           (job_id, c.task_id, c.parent_id, request['routing']['effective_lane'],
                            c.backend, request.get('attempt_number', 1)))
                self.audit(db, job_id, 'route', request['routing'])
                ids.append(job_id)
            db.execute("UPDATE runs SET state='local_queued' WHERE id=?", (run_id,))
            return ids

    def get(self, job_id):
        with self.store.db() as db:
            row = db.execute('SELECT * FROM contract_jobs WHERE job_id=?', (job_id,)).fetchone()
        if not row:
            return None
        result = dict(row)
        result['evidence'] = json.loads(result['evidence']) if result['evidence'] else None
        return result

    def update(self, job, **values):
        allowed = {'execution_status', 'verification_status', 'review_status', 'integration_status',
                   'candidate_hash', 'executor_id', 'dispatch_state', 'evidence'}
        if not values or set(values) - allowed:
            raise ValueError('Invalid contract transition')
        with self.store.db() as db:
            db.execute('BEGIN IMMEDIATE')
            current = db.execute('SELECT attempt_id FROM jobs WHERE id=?', (job['id'],)).fetchone()
            if not current or current[0] != job['attempt_id']:
                raise ValueError('Stale contract attempt')
            if 'candidate_hash' in values:
                row = db.execute('SELECT candidate_hash FROM contract_jobs WHERE job_id=?', (job['id'],)).fetchone()
                if row and row[0] != values['candidate_hash']:
                    db.execute("UPDATE contract_jobs SET accepted_hash=NULL,review_status='awaiting_review',integration_status='candidate' WHERE job_id=?", (job['id'],))
                    db.execute("UPDATE events SET state='pending',decision=NULL,validation=NULL WHERE job_id=?", (job['id'],))
            raw = {k: encode(v) if k == 'evidence' else v for k, v in values.items()}
            db.execute('UPDATE contract_jobs SET ' + ','.join(k + '=?' for k in raw) + ' WHERE job_id=?',
                       (*raw.values(), job['id']))
            self.audit(db, job['id'], 'transition', values)

    def reserve(self, job):
        with self.store.db() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT * FROM inference_reservation WHERE singleton=1').fetchone()
            if row and (row['job_id'], row['attempt_id']) != (job['id'], job['attempt_id']):
                raise ValueError('Local inference resource is reserved; reconcile owned work first')
            db.execute('INSERT OR IGNORE INTO inference_reservation VALUES(1,?,?,?,?)',
                       (job['id'], job['attempt_id'], job['request']['contract']['backend'], 'active'))

    def release(self, job, confirmed=True):
        with self.store.db() as db:
            if confirmed:
                db.execute('DELETE FROM inference_reservation WHERE job_id=? AND attempt_id=?',
                           (job['id'], job['attempt_id']))
            else:
                db.execute("UPDATE inference_reservation SET state='cancellation_pending' WHERE job_id=? AND attempt_id=?",
                           (job['id'], job['attempt_id']))
            self.audit(db, job['id'], 'resource', {'termination_confirmed': confirmed})

    def reconcile_resource(self, job_id, evidence):
        if not evidence.strip():
            raise ValueError('Confirm provider idle/termination with independent evidence')
        with self.store.db() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT * FROM inference_reservation WHERE job_id=?', (job_id,)).fetchone()
            if not row or row['state'] != 'cancellation_pending':
                raise ValueError('Resource has no uncertain cancellation')
            job = db.execute('SELECT state FROM jobs WHERE id=?', (job_id,)).fetchone()
            if job['state'] == 'running':
                raise ValueError('Reconcile the owned executor first')
            db.execute('DELETE FROM inference_reservation WHERE job_id=?', (job_id,))
            self.audit(db, job_id, 'supervisor_resource_reconciliation', {'evidence': evidence})

    def review(self, event_id, outcome, validation, candidate_hash, coverage):
        self.store.decide(event_id, outcome, validation, local=True,
                          candidate_hash=candidate_hash, coverage=coverage)


def effective_jobs(rows):
    """Resolve an approved correction without rewriting historical contracts."""
    jobs = [dict(row) for row in rows]
    for job in jobs:
        if isinstance(job['request'],str):
            job['request'] = json.loads(job['request'])
    replacements = {j['request']['correction_of']:j for j in jobs
                    if j['request'].get('execution')=='contract' and j['request'].get('correction_of')}
    result = {}
    for original in jobs:
        current, seen = original, set()
        while current['id'] in replacements:
            if current['id'] in seen:
                raise ValueError('Correction cycle')
            seen.add(current['id'])
            current = replacements[current['id']]
        result[original['task_key']] = current
    return result


def eligible(db, row):
    request = json.loads(row['request'])
    reservation = db.execute('SELECT * FROM inference_reservation WHERE singleton=1').fetchone()
    direct = request.get('execution')=='contract' and request['routing']['effective_lane']=='codex_direct'
    if reservation and reservation['job_id'] != row['id'] and not direct:
        return False
    if request.get('execution') != 'contract':
        return True
    c = request['contract']
    dependencies = effective_jobs(db.execute('SELECT * FROM jobs WHERE run_id=?',(row['run_id'],)).fetchall())
    for dep in c['dependencies']:
        resolved = dependencies.get(dep)
        result = db.execute('SELECT * FROM contract_jobs WHERE job_id=?',(resolved['id'],)).fetchone() if resolved else None
        if not result or result['review_status'] != 'accepted' or result['accepted_hash'] != result['candidate_hash']:
            return False
    return True


def review_guard(db, row, outcome, candidate_hash, coverage):
    contract = db.execute('SELECT * FROM contract_jobs WHERE job_id=?', (row['job_id'],)).fetchone()
    if not contract:
        return
    request = json.loads(db.execute('SELECT request FROM jobs WHERE id=?', (row['job_id'],)).fetchone()[0])
    if outcome in ('accepted', 'corrected'):
        if not candidate_hash or candidate_hash != contract['candidate_hash']:
            raise ValueError('Acceptance must identify the exact current candidate')
        if contract['lane'] == 'local_implementation' and contract['verification_status'] != 'passed':
            raise ValueError('Failed or unrun independent verification cannot be accepted')
        required = set(request['contract']['acceptance']) | set(request.get('required_reviews', []))
        if set(coverage or {}) != required or not all(
                isinstance(v, str) and v.strip() for v in (coverage or {}).values()):
            raise ValueError('Supervisor must record coverage for every acceptance criterion')
        if contract['lane'] == 'local_implementation':
            from pathlib import Path
            directory = Path(db.execute('PRAGMA database_list').fetchone()[2]).parent/'artifacts'/row['job_id']
            packet = json.loads((directory/'candidate.json').read_text())
            if digest(packet) != candidate_hash:
                raise ValueError('Candidate artifact changed; acceptance is stale')
        status = 'accepted'
    else:
        status = 'escalated' if outcome == 'further_work' else 'rejected'
    if row['state']=='reviewed':
        prior = db.execute("SELECT detail FROM contract_audit WHERE job_id=? AND kind='supervisor_review' ORDER BY id DESC LIMIT 1", (row['job_id'],)).fetchone()
        if prior and json.loads(prior[0]).get('coverage') != coverage:
            raise ValueError('Review coverage already recorded differently')
        return
    import time
    db.execute('INSERT INTO contract_audit(job_id,kind,created,detail) VALUES(?,?,?,?)',
               (row['job_id'],'supervisor_review',time.time(),encode({'outcome':outcome,'candidate_hash':candidate_hash,'coverage':coverage})))
    db.execute('UPDATE contract_jobs SET review_status=?,accepted_hash=? WHERE job_id=?',
               (status, candidate_hash if status == 'accepted' else None, row['job_id']))
