"""Durable local jobs and callback outbox, separate from historical usage data.

Transactions serialize admission and review claims. An external invocation with
uncertain delivery is never retried automatically. All time is injectable.
"""
from contextlib import contextmanager
import json
from pathlib import Path
import sqlite3
import time
import uuid


def encode(value):
    # Workflow evidence digests predate the companion and include object order.
    # Preserve the packets exactly; canonicalize only submission comparison.
    return json.dumps(value, ensure_ascii=False, allow_nan=False)


def submission_identity(request):
    value = json.loads(encode(request))
    # Planning estimates use current metrics/cap observations. The typed task,
    # pinned configuration/policy and inventory identify authorized work; an
    # identical submission after completion must not become a second stage.
    value.pop('workflow_plan', None)
    if isinstance(value.get('selection'), dict):
        # A fresh inventory observation is not a different authorized task.
        value['selection'].pop('observed_at', None)
    return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False)


class CompanionStore:
    def __init__(self, directory, clock=time.time):
        self.directory = Path(directory).resolve()
        self.directory.mkdir(parents=True, exist_ok=True)
        self.path = self.directory / 'companion.sqlite3'
        self.clock = clock
        with self.db() as db:
            if db.execute('PRAGMA user_version').fetchone()[0] > 2:
                raise ValueError('Companion database is newer than this runtime; use the matching version')
            db.execute('PRAGMA journal_mode=WAL')
            db.executescript('''
                CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS runs (
                  id TEXT PRIMARY KEY, repository TEXT NOT NULL, base_revision TEXT NOT NULL,
                  session_id TEXT, state TEXT NOT NULL, created REAL NOT NULL, finalized REAL,
                  summary TEXT, cancel_requested INTEGER NOT NULL DEFAULT 0);
                CREATE TABLE IF NOT EXISTS jobs (
                  id TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES runs(id), task_key TEXT NOT NULL,
                  request TEXT NOT NULL, state TEXT NOT NULL, created REAL NOT NULL, started REAL,
                  ended REAL, attempt_id TEXT, process TEXT, result TEXT, error TEXT,
                  cancel_requested INTEGER NOT NULL DEFAULT 0, UNIQUE(run_id, task_key));
                CREATE TABLE IF NOT EXISTS events (
                  id TEXT PRIMARY KEY, job_id TEXT UNIQUE NOT NULL REFERENCES jobs(id),
                  run_id TEXT NOT NULL REFERENCES runs(id), state TEXT NOT NULL,
                  created REAL NOT NULL, retry_at REAL, reason TEXT, decision TEXT,
                  validation TEXT, review_started REAL, review_ended REAL, review_usage TEXT);
                CREATE TABLE IF NOT EXISTS deliveries (
                  id TEXT PRIMARY KEY, event_id TEXT NOT NULL REFERENCES events(id),
                  state TEXT NOT NULL, created REAL NOT NULL, ended REAL, evidence TEXT);
                CREATE TABLE IF NOT EXISTS recoveries (
                  job_id TEXT PRIMARY KEY REFERENCES jobs(id), attempt_id TEXT,
                  receipt_digest TEXT, disposition TEXT NOT NULL, detail TEXT NOT NULL,
                  updated REAL NOT NULL);
            ''')
            db.execute('PRAGMA user_version=2')

    @contextmanager
    def db(self):
        db = sqlite3.connect(self.path, timeout=15)
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA foreign_keys=ON')
        db.execute('PRAGMA synchronous=FULL')
        try:
            with db:
                yield db
        finally:
            db.close()

    def setting(self, key, value=None):
        with self.db() as db:
            if value is not None:
                db.execute('INSERT OR REPLACE INTO settings VALUES(?,?)', (key, encode(value)))
            row = db.execute('SELECT value FROM settings WHERE key=?', (key,)).fetchone()
        return json.loads(row[0]) if row else None

    def annotate_inventory(self, rows, endpoint):
        """Validation is scoped to reviewed successful tools at an exact digest."""
        with self.db() as db:
            requests = [json.loads(r[0]) for r in db.execute('''SELECT j.request FROM jobs j
                JOIN events e ON e.job_id=j.id WHERE j.state='succeeded' AND e.state='reviewed'
                AND e.decision IN ('accepted','corrected')''')]
        output = []
        for item in rows:
            row = dict(item)
            tools = sorted({r['tool'] for r in requests if not r.get('execution') and r.get('endpoint')==endpoint and row.get('digest')
                and r['selection'].get('digest')==row['digest'] and r['selection']['name']==row['name']})
            if tools and row['validation']!='incompatible':
                row.update(validation='locally_validated',validated_tools=tools,
                           validation_scope='Reviewed bounded contributions only; not general coding quality')
            output.append(row)
        return output

    def create_run(self, repository, base_revision, session_id=None):
        run_id = str(uuid.uuid4())
        if session_id:
            session_id = str(uuid.UUID(session_id))
        with self.db() as db:
            db.execute('INSERT INTO runs(id,repository,base_revision,session_id,state,created) VALUES(?,?,?,?,?,?)',
                       (run_id, str(Path(repository).resolve(strict=True)), base_revision, session_id, 'ready', self.clock()))
        return run_id

    def bind_session(self, run_id, session_id):
        session_id = str(uuid.UUID(session_id))
        with self.db() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT session_id FROM runs WHERE id=?', (run_id,)).fetchone()
            if not row or row[0] is not None:
                raise ValueError('Run already bound or missing')
            db.execute('UPDATE runs SET session_id=? WHERE id=?', (session_id, run_id))

    def submit(self, run_id, task_key, request):
        raw = encode(request)
        if not task_key or len(task_key) > 160 or len(raw.encode()) > 100_000:
            raise ValueError('Invalid task key or request too large')
        with self.db() as db:
            db.execute('BEGIN IMMEDIATE')
            run = db.execute('SELECT * FROM runs WHERE id=?', (run_id,)).fetchone()
            if not run or run['finalized'] is not None or run['cancel_requested']:
                raise ValueError('Run is missing, cancelled or finalized')
            old = db.execute('SELECT id,request FROM jobs WHERE run_id=? AND task_key=?', (run_id, task_key)).fetchone()
            if not old and request.get('execution')=='workflow' and request.get('workflow_id') is None:
                for candidate in db.execute('SELECT id,request FROM jobs WHERE run_id=?',(run_id,)):
                    prior = json.loads(candidate['request'])
                    if prior.get('execution')=='workflow' and prior.get('workflow_id') is None and prior['workflow_task']['task_id']==request['workflow_task']['task_id']:
                        old = candidate
                        break
            if old:
                if submission_identity(json.loads(old['request'])) != submission_identity(request):
                    raise ValueError('Task key already names different work')
                return old['id']
            job_id = str(uuid.uuid4())
            db.execute('INSERT INTO jobs(id,run_id,task_key,request,state,created) VALUES(?,?,?,?,?,?)',
                       (job_id, run_id, task_key, raw, 'queued', self.clock()))
            db.execute("UPDATE runs SET state='local_queued' WHERE id=?", (run_id,))
        return job_id

    def claim_job(self, process):
        with self.db() as db:
            db.execute('BEGIN IMMEDIATE')
            paused = db.execute("SELECT value FROM settings WHERE key='paused'").fetchone()
            if paused and json.loads(paused[0]):
                return None
            if db.execute("SELECT 1 FROM jobs WHERE state='running'").fetchone():
                return None
            row = db.execute("SELECT j.* FROM jobs j JOIN runs r ON r.id=j.run_id WHERE j.state='queued' AND r.cancel_requested=0 ORDER BY j.created,j.id LIMIT 1").fetchone()
            if not row:
                return None
            attempt = str(uuid.uuid4())
            db.execute("UPDATE jobs SET state='running',attempt_id=?,process=?,started=? WHERE id=?",
                       (attempt, encode(process), self.clock(), row['id']))
            db.execute("UPDATE runs SET state='local_generation' WHERE id=?", (row['run_id'],))
        return self.job(row['id'])

    def job(self, job_id):
        with self.db() as db:
            row = db.execute('SELECT * FROM jobs WHERE id=?', (job_id,)).fetchone()
        if not row:
            raise ValueError('Unknown job')
        result = dict(row)
        for key in ('request', 'process', 'result'):
            result[key] = json.loads(result[key]) if result[key] else None
        return result

    def complete(self, job_id, attempt, result=None, error=None, state='succeeded'):
        if state not in ('succeeded', 'failed', 'cancelled', 'interrupted'):
            raise ValueError('Invalid completion state')
        with self.db() as db:
            db.execute('BEGIN IMMEDIATE')
            job = db.execute('SELECT * FROM jobs WHERE id=?', (job_id,)).fetchone()
            if not job or job['attempt_id'] != attempt:
                raise ValueError('Stale worker attempt')
            if job['state'] != 'running':
                return False
            if job['cancel_requested']:
                state = 'cancelled'
            db.execute('UPDATE jobs SET state=?,result=?,error=?,ended=? WHERE id=?',
                       (state, encode(result) if result is not None else None, error, self.clock(), job_id))
            # Result and outbox completion are committed together, by the worker.
            db.execute("INSERT INTO events(id,job_id,run_id,state,created) VALUES(?,?,?,'pending',?)",
                       (str(uuid.uuid4()), job_id, job['run_id'], self.clock()))
            db.execute("UPDATE runs SET state='waiting_for_codex' WHERE id=?", (job['run_id'],))
        return True

    def recovery_issue(self, job_id, detail):
        """Diagnostic only; never replace a recorded result, review or final decision."""
        with self.db() as db:
            db.execute('''INSERT INTO recoveries(job_id,disposition,detail,updated)
                VALUES(?,'intervention_required',?,?) ON CONFLICT(job_id) DO UPDATE SET
                detail=excluded.detail,updated=excluded.updated
                WHERE recoveries.receipt_digest IS NULL''',(job_id,detail,self.clock()))

    def apply_recovery(self, receipt, receipt_digest, current_version):
        from .workflow_recovery import digest
        if digest(receipt)!=receipt_digest:
            raise ValueError('Recovery receipt digest mismatch')
        job_id = receipt['job_id']
        with self.db() as db:
            db.execute('BEGIN IMMEDIATE')
            job = db.execute('SELECT * FROM jobs WHERE id=?',(job_id,)).fetchone()
            if not job or job['attempt_id']!=receipt['attempt_id'] or digest(json.loads(job['request']))!=receipt['request_digest']:
                raise ValueError('Stale recovery job/attempt/request identity')
            prior = db.execute('SELECT * FROM recoveries WHERE job_id=?',(job_id,)).fetchone()
            if prior and prior['receipt_digest']:
                if prior['receipt_digest']!=receipt_digest:
                    raise ValueError('Conflicting immutable recovery receipt')
                return prior['disposition']
            run = db.execute('SELECT * FROM runs WHERE id=?',(job['run_id'],)).fetchone()
            event = db.execute('SELECT * FROM events WHERE job_id=?',(job_id,)).fetchone()
            same = job['result'] is not None and json.loads(job['result'])==receipt['result']
            if run['finalized'] is not None:
                disposition = 'preserved_finalized'
            elif job['cancel_requested'] or run['cancel_requested'] or job['state']=='cancelled':
                disposition = 'preserved_cancelled'
            elif same and job['state']==receipt['state']:
                disposition = 'already_present'
            elif event and event['state'] not in ('pending','retry'):
                disposition = 'preserved_review'
            elif job['result'] is not None:
                disposition = 'conflicting_result'
            elif receipt['version']!=current_version:
                disposition = 'stale_workflow_version'
            else:
                disposition = 'applied'
                db.execute('UPDATE jobs SET state=?,result=?,error=?,ended=? WHERE id=?',
                    (receipt['state'],encode(receipt['result']),receipt['error'],self.clock(),job_id))
            if disposition in ('applied','already_present'):
                db.execute("INSERT OR IGNORE INTO events(id,job_id,run_id,state,created) VALUES(?,?,?,'pending',?)",
                    (str(uuid.uuid5(uuid.UUID(job_id),'completion-review')),job_id,job['run_id'],self.clock()))
                if event is None or event['state'] in ('pending','retry'):
                    db.execute("UPDATE runs SET state='waiting_for_codex' WHERE id=?",(job['run_id'],))
            elif job['state']=='running':
                # Leave committed output in the journal, without claiming success
                # or leaving a dead worker permanently running in the dock.
                db.execute('UPDATE jobs SET state=?,error=?,ended=? WHERE id=?',
                    ('cancelled' if disposition=='preserved_cancelled' else 'interrupted',
                     'Recovery requires inspection: '+disposition,self.clock(),job_id))
                db.execute("INSERT OR IGNORE INTO events(id,job_id,run_id,state,created) VALUES(?,?,?,'pending',?)",
                    (str(uuid.uuid5(uuid.UUID(job_id),'completion-review')),job_id,job['run_id'],self.clock()))
            db.execute('''INSERT INTO recoveries VALUES(?,?,?,?,?,?) ON CONFLICT(job_id) DO UPDATE SET
                attempt_id=excluded.attempt_id,receipt_digest=excluded.receipt_digest,
                disposition=excluded.disposition,detail=excluded.detail,updated=excluded.updated''',
                (job_id,receipt['attempt_id'],receipt_digest,disposition,
                 receipt['error'] or 'Durable workflow receipt; approval is a separate recorded decision',self.clock()))
            return disposition

    def repair_completion_event(self, job_id):
        """A legacy saved terminal result is already authoritative in this DB."""
        with self.db() as db:
            db.execute('BEGIN IMMEDIATE')
            job = db.execute('SELECT * FROM jobs WHERE id=?',(job_id,)).fetchone()
            run = db.execute('SELECT * FROM runs WHERE id=?',(job['run_id'],)).fetchone()
            if job['result'] is None or job['state'] not in ('succeeded','failed','interrupted','cancelled'):
                return False
            if run['finalized'] is not None:
                return False
            changed = db.execute("INSERT OR IGNORE INTO events(id,job_id,run_id,state,created) VALUES(?,?,?,'pending',?)",
                (str(uuid.uuid5(uuid.UUID(job_id),'completion-review')),job_id,job['run_id'],self.clock())).rowcount
            if changed and not run['cancel_requested']:
                db.execute("UPDATE runs SET state='waiting_for_codex' WHERE id=?",(job['run_id'],))
            return bool(changed)

    def cancel(self, run_id, job_id=None):
        with self.db() as db:
            db.execute('BEGIN IMMEDIATE')
            if job_id:
                rows = db.execute("SELECT * FROM jobs WHERE id=? AND run_id=? AND state IN ('queued','running')", (job_id, run_id)).fetchall()
            else:
                db.execute("UPDATE runs SET cancel_requested=1,state='cancelling' WHERE id=? AND finalized IS NULL", (run_id,))
                rows = db.execute("SELECT * FROM jobs WHERE run_id=? AND state IN ('queued','running')", (run_id,)).fetchall()
            for row in rows:
                db.execute('UPDATE jobs SET cancel_requested=1 WHERE id=?', (row['id'],))
                if row['state'] == 'queued':
                    db.execute("UPDATE jobs SET state='cancelled',ended=? WHERE id=?", (self.clock(), row['id']))
                    db.execute("INSERT INTO events(id,job_id,run_id,state,created) VALUES(?,?,?,'pending',?)",
                               (str(uuid.uuid4()), row['id'], run_id, self.clock()))

    def claim_event(self):
        with self.db() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('''SELECT e.*,r.session_id,r.repository,r.base_revision FROM events e
                JOIN runs r ON r.id=e.run_id WHERE e.state IN ('pending','retry')
                AND (e.retry_at IS NULL OR e.retry_at<=?) AND r.session_id IS NOT NULL
                AND NOT EXISTS (SELECT 1 FROM settings s WHERE s.key='session_init:'||r.id AND s.value!='"ready"')
                AND NOT EXISTS (SELECT 1 FROM events a JOIN runs b ON b.id=a.run_id
                    WHERE b.session_id=r.session_id AND a.state IN ('dispatching','uncertain','awaiting_decision'))
                ORDER BY e.created,e.id LIMIT 1''', (self.clock(),)).fetchone()
            if not row:
                return None
            attempt = str(uuid.uuid4())
            db.execute("UPDATE events SET state='dispatching',review_started=?,reason=NULL WHERE id=?", (self.clock(), row['id']))
            db.execute("UPDATE runs SET state='reviewing' WHERE id=?", (row['run_id'],))
            db.execute("INSERT INTO deliveries(id,event_id,state,created) VALUES(?,?,'claimed',?)", (attempt, row['id'], self.clock()))
        return dict(row) | {'delivery_id': attempt}

    def reconcile_session(self, run_id, evidence):
        if not evidence.strip():
            raise ValueError('Inspect initialization artifacts and process state before reconciliation')
        run = self.snapshot(run_id)['runs'][0]
        if not run['session_id'] or self.setting('session_init:'+run_id) != 'uncertain':
            raise ValueError('No uncertain managed session to reconcile')
        self.setting('session_reconciliation:'+run_id,evidence)
        self.setting('session_init:'+run_id,'ready')

    def delivery(self, event_id, attempt, state, reason='', retry_at=None, evidence=None, usage=None):
        if state not in ('retry', 'uncertain', 'awaiting_decision', 'blocked'):
            raise ValueError('Invalid delivery state')
        with self.db() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute("SELECT e.* FROM events e JOIN deliveries d ON d.event_id=e.id WHERE e.id=? AND d.id=? AND e.state='dispatching' AND d.state='claimed'", (event_id, attempt)).fetchone()
            if not row:
                raise ValueError('Stale delivery')
            db.execute('UPDATE events SET state=?,reason=?,retry_at=?,review_ended=?,review_usage=? WHERE id=?',
                       (state, reason, retry_at, self.clock(), encode(usage) if usage is not None else None, event_id))
            db.execute('UPDATE deliveries SET state=?,ended=?,evidence=? WHERE id=?',
                       (state, self.clock(), encode(evidence), attempt))
            db.execute("UPDATE runs SET state='blocked' WHERE id=?", (row['run_id'],))

    def reconcile(self, event_id, disposition, note):
        if disposition not in ('not_delivered', 'delivered') or not note.strip():
            raise ValueError('Reconciliation requires evidence and delivered/not_delivered')
        with self.db() as db:
            changed = db.execute("UPDATE events SET state=?,reason=?,retry_at=NULL WHERE id=? AND state IN ('uncertain','blocked')",
                                 ('pending' if disposition == 'not_delivered' else 'awaiting_decision', note, event_id)).rowcount
            if not changed:
                raise ValueError('Event does not need reconciliation')

    def decide(self, event_id, outcome, validation, local=False):
        if outcome not in ('accepted', 'corrected', 'rejected', 'further_work') or not validation.strip():
            raise ValueError('A review outcome and validation evidence are required')
        with self.db() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT * FROM events WHERE id=?', (event_id,)).fetchone()
            allowed = ('awaiting_decision','reviewed','pending','retry') if local else ('awaiting_decision','reviewed')
            if not row or row['state'] not in allowed:
                raise ValueError('Reconcile delivery before deciding')
            if row['state'] == 'reviewed':
                if row['decision'] != outcome or row['validation'] != validation:
                    raise ValueError('Decision already recorded')
                return
            db.execute("UPDATE events SET state='reviewed',decision=?,validation=? WHERE id=?", (outcome, validation, event_id))
            if local:
                db.execute("UPDATE events SET reason='supervisor_local_review' WHERE id=?",(event_id,))
            db.execute("UPDATE runs SET state='validating' WHERE id=?", (row['run_id'],))

    def finalize(self, run_id, summary, validation_passed):
        if not summary.strip() or type(validation_passed) is not bool:
            raise ValueError('Finalization needs a summary and validation result')
        from .companion_recovery import verification_guard, verify_final_workflows
        with verification_guard(self) as ledger, self.db() as db:
            db.execute('BEGIN IMMEDIATE')
            run = db.execute('SELECT * FROM runs WHERE id=?', (run_id,)).fetchone()
            if not run:
                raise ValueError('Unknown run')
            if run['finalized'] is not None:
                return run['state']
            jobs = db.execute('SELECT * FROM jobs WHERE run_id=?', (run_id,)).fetchall()
            events = db.execute('SELECT * FROM events WHERE run_id=?', (run_id,)).fetchall()
            resolved = jobs and len(events) == len(jobs) and all(e['state']=='reviewed' for e in events)
            if not resolved or any(j['state'] in ('queued','running') for j in jobs):
                raise ValueError('Unresolved jobs or reviews prevent finalization')
            workflows = {}
            for job in sorted(jobs,key=lambda j:j['created']):
                request = json.loads(job['request'])
                if request.get('execution')=='workflow':
                    result = json.loads(job['result']) if job['result'] else {}
                    workflows[request['workflow_task']['task_id']] = result.get('answer',{}).get('workflow',{}).get('state')
            if validation_passed and any(state!='codex_verified' for state in workflows.values()):
                raise ValueError('Unresolved workflow checkpoints prevent successful finalization')
            if validation_passed:
                verify_final_workflows(ledger,jobs)
            successful = validation_passed and all(j['state']=='succeeded' for j in jobs) and all(e['decision'] in ('accepted','corrected') for e in events)
            state = 'cancelled' if run['cancel_requested'] else 'completed' if successful else 'blocked'
            db.execute('UPDATE runs SET state=?,finalized=?,summary=? WHERE id=?', (state, self.clock(), summary, run_id))
        return state

    def recover_deliveries(self):
        """Call only with the controller lock held; never blindly redeliver."""
        with self.db() as db:
            db.execute("UPDATE deliveries SET state='uncertain' WHERE state='claimed'")
            db.execute("UPDATE runs SET state='blocked' WHERE id IN (SELECT run_id FROM events WHERE state='dispatching')")
            db.execute("UPDATE events SET state='uncertain',reason='Controller interrupted; inspect delivery artifacts before retry' WHERE state='dispatching'")

    def snapshot(self, run_id=None):
        with self.db() as db:
            clause, args = (' WHERE id=?', (run_id,)) if run_id else ('', ())
            runs = [dict(r) for r in db.execute('SELECT * FROM runs'+clause+' ORDER BY created DESC', args)]
            ids = {r['id'] for r in runs}
            jobs = [dict(r) for r in db.execute('SELECT * FROM jobs ORDER BY created') if r['run_id'] in ids]
            events = [dict(r) for r in db.execute('SELECT * FROM events ORDER BY created') if r['run_id'] in ids]
            recoveries = [dict(r) for r in db.execute('SELECT * FROM recoveries') if any(j['id']==r['job_id'] for j in jobs)]
        for row in jobs:
            for key in ('request','result','process'):
                row[key] = json.loads(row[key]) if row[key] else None
        return dict(runs=runs, jobs=jobs, events=events, recoveries=recoveries,
                    paused=self.setting('paused') or False, now=self.clock())
