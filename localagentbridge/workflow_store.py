"""Metadata-only workflow ledger in the existing usage database.

Reservations are durable before generation. Interrupted work is charged, never
automatically replayed. The lease serializes workflow calls sharing this store.
"""
import json
import time
import uuid

from .bridge import BridgeError
from .schemas import compact


class WorkflowStore:
    def __init__(self, store):
        self.store = store
        with store.connect() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS workflow_runs (
                    id TEXT PRIMARY KEY, task_key TEXT UNIQUE NOT NULL, identity TEXT NOT NULL,
                    catalog TEXT NOT NULL, snapshot TEXT NOT NULL, plan TEXT NOT NULL,
                    limits TEXT NOT NULL, position INTEGER NOT NULL DEFAULT 0,
                    version INTEGER NOT NULL DEFAULT 0, state TEXT NOT NULL DEFAULT 'ready',
                    reason TEXT NOT NULL DEFAULT '', attempts INTEGER NOT NULL DEFAULT 0,
                    corrections INTEGER NOT NULL DEFAULT 0, reserved_tokens INTEGER NOT NULL DEFAULT 0,
                    output_tokens_reserved INTEGER NOT NULL DEFAULT 0, input_chars INTEGER NOT NULL DEFAULT 0,
                    seconds REAL NOT NULL DEFAULT 0, created REAL NOT NULL, updated REAL NOT NULL);
                CREATE TABLE IF NOT EXISTS workflow_stages (
                    run_id TEXT, stage_id TEXT, state TEXT NOT NULL DEFAULT 'pending',
                    attempts INTEGER NOT NULL DEFAULT 0, seconds REAL NOT NULL DEFAULT 0,
                    PRIMARY KEY(run_id,stage_id));
                CREATE TABLE IF NOT EXISTS workflow_lease (
                    slot INTEGER PRIMARY KEY CHECK(slot=1), owner TEXT NOT NULL,
                    run_id TEXT NOT NULL, stage_id TEXT NOT NULL, expires REAL NOT NULL,
                    reserved_seconds REAL NOT NULL);
                CREATE TABLE IF NOT EXISTS workflow_results (
                    run_id TEXT, stage_id TEXT, skill_id TEXT, version INTEGER,
                    digest TEXT NOT NULL, snapshot TEXT NOT NULL,
                    PRIMARY KEY(run_id,stage_id,skill_id,version));
                CREATE TABLE IF NOT EXISTS workflow_attempts (
                    request_id TEXT PRIMARY KEY, run_id TEXT NOT NULL, stage_id TEXT NOT NULL,
                    skill_id TEXT NOT NULL, kind TEXT NOT NULL, model TEXT NOT NULL,
                    state TEXT NOT NULL, input_tokens INTEGER, output_tokens INTEGER,
                    output_bytes INTEGER, created REAL NOT NULL);
                CREATE TABLE IF NOT EXISTS workflow_events (
                    id INTEGER PRIMARY KEY, run_id TEXT NOT NULL, created REAL NOT NULL,
                    kind TEXT NOT NULL, stage_id TEXT, role TEXT, model TEXT, reason TEXT);
            ''')

    @staticmethod
    def event(db, run_id, kind, *, stage=None, role=None, model=None, reason=None):
        db.execute('INSERT INTO workflow_events(run_id,created,kind,stage_id,role,model,reason) VALUES(?,?,?,?,?,?,?)',
                   (run_id, time.time(), kind, stage, role, model, reason))

    def create(self, task_key, identity, catalog, snapshot, plan, limits):
        with self.store.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            old = db.execute('SELECT * FROM workflow_runs WHERE task_key=?', (task_key,)).fetchone()
            if old:
                if old['identity'] != identity or old['catalog'] != catalog:
                    raise BridgeError('This task ID already names another immutable workflow scope.')
                return old['id']
            if db.execute('SELECT COUNT(*) FROM workflow_runs').fetchone()[0] >= 5000:
                raise BridgeError('Workflow history capacity reached; retain or archive history before new work.')
            run_id = str(uuid.uuid4())
            now = time.time()
            db.execute('''INSERT INTO workflow_runs(id,task_key,identity,catalog,snapshot,plan,limits,created,updated)
                VALUES(?,?,?,?,?,?,?,?,?)''', (run_id,task_key,identity,catalog,snapshot,compact(plan),compact(limits),now,now))
            for stage in plan['stages']:
                db.execute('INSERT INTO workflow_stages(run_id,stage_id) VALUES(?,?)', (run_id,stage['id']))
            self.event(db, run_id, 'started')
            return run_id

    def read(self, run_id):
        with self.store.connect() as db:
            row = db.execute('SELECT * FROM workflow_runs WHERE id=?', (run_id,)).fetchone()
            if not row:
                raise BridgeError('Unknown workflow run.')
            return dict(row)

    def _expire(self, db):
        lease = db.execute('SELECT * FROM workflow_lease WHERE slot=1').fetchone()
        if lease and lease['expires'] <= time.time():
            db.execute("UPDATE workflow_runs SET state='handed_off',reason='interrupted',version=version+1,updated=? WHERE id=?",
                       (time.time(),lease['run_id']))
            db.execute("UPDATE workflow_stages SET state='handed_off' WHERE run_id=? AND stage_id=?",
                       (lease['run_id'],lease['stage_id']))
            self.event(db, lease['run_id'], 'handed_off', stage=lease['stage_id'], reason='interrupted')
            db.execute('DELETE FROM workflow_lease WHERE slot=1')

    def claim(self, run_id, version, stage, timeout):
        with self.store.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            self._expire(db)
            if db.execute('SELECT 1 FROM workflow_lease').fetchone():
                raise BridgeError('A workflow is busy in this data directory.')
            row = db.execute('SELECT * FROM workflow_runs WHERE id=?', (run_id,)).fetchone()
            if row['version'] != version or row['state'] != 'ready':
                raise BridgeError('Stale workflow version or stage is not ready; inspect status.')
            limits = json.loads(row['limits'])
            prior = db.execute('SELECT seconds FROM workflow_stages WHERE run_id=? AND stage_id=?',
                               (run_id,stage['id'])).fetchone()[0]
            available = min(timeout-prior, limits['max_seconds']-row['seconds'])
            if available <= 0:
                raise BridgeError('workflow_time_budget')
            owner = str(uuid.uuid4())
            db.execute('INSERT INTO workflow_lease VALUES(1,?,?,?,?,?)',
                       (owner,run_id,stage['id'],time.time()+available+2,available))
            db.execute("UPDATE workflow_runs SET state='running',seconds=seconds+?,version=version+1,updated=? WHERE id=?",
                       (available,time.time(),run_id))
            db.execute("UPDATE workflow_stages SET state='running',seconds=seconds+? WHERE run_id=? AND stage_id=?",
                       (available,run_id,stage['id']))
            self.event(db, run_id, 'role_started', stage=stage['id'], role=stage['role'])
            return owner, available

    @staticmethod
    def _owner(db, owner):
        lease = db.execute('SELECT * FROM workflow_lease WHERE owner=?', (owner,)).fetchone()
        if not lease or lease['expires'] <= time.time():
            raise BridgeError('Workflow lease expired; no late result can advance the workflow.')
        return lease

    def reserve(self, owner, request_id, skill, model, input_chars, context, output, maximum, retry):
        with self.store.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            lease = self._owner(db, owner)
            run = db.execute('SELECT * FROM workflow_runs WHERE id=?', (lease['run_id'],)).fetchone()
            stage = db.execute('SELECT * FROM workflow_stages WHERE run_id=? AND stage_id=?',
                               (lease['run_id'],lease['stage_id'])).fetchone()
            limits = json.loads(run['limits'])
            checks = [(run['attempts']+1,limits['max_attempts'],'workflow_attempt_budget'),
                      (stage['attempts']+1,maximum,'role_attempt_budget'),
                      (run['corrections']+int(retry),limits['max_corrections'],'workflow_correction_budget'),
                      (run['reserved_tokens']+context+output,limits['max_reserved_tokens'],'workflow_token_budget'),
                      (run['output_tokens_reserved']+output,limits['max_output_tokens'],'workflow_output_budget'),
                      (run['input_chars']+input_chars,limits['max_input_chars'],'workflow_input_budget')]
            for used, limit, reason in checks:
                if used > limit:
                    raise BridgeError(reason)
            db.execute('''UPDATE workflow_runs SET attempts=attempts+1,corrections=corrections+?,
                reserved_tokens=reserved_tokens+?,output_tokens_reserved=output_tokens_reserved+?,
                input_chars=input_chars+?,updated=? WHERE id=?''',
                (int(retry),context+output,output,input_chars,time.time(),run['id']))
            db.execute('UPDATE workflow_stages SET attempts=attempts+1 WHERE run_id=? AND stage_id=?',
                       (run['id'],stage['stage_id']))
            db.execute('''INSERT INTO workflow_attempts(request_id,run_id,stage_id,skill_id,kind,model,state,created)
                VALUES(?,?,?,?,?,?,?,?)''', (request_id,run['id'],stage['stage_id'],skill,
                'stronger_retry' if retry else 'initial',model,'reserved',time.time()))
            self.event(db, run['id'], 'attempt_reserved', stage=stage['stage_id'], model=model,
                       reason='stronger_retry' if retry else 'initial')

    def attempted(self, request_id, final, state, output_bytes):
        def count(key):
            value = final.get(key)
            return value if type(value) is int and value >= 0 else None
        with self.store.connect() as db:
            db.execute('''UPDATE workflow_attempts SET state=?,input_tokens=?,output_tokens=?,output_bytes=?
                WHERE request_id=?''', (state,count('prompt_eval_count'),count('eval_count'),output_bytes,request_id))

    def result(self, owner, packet, digest, snapshot):
        with self.store.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            lease = self._owner(db, owner)
            version = db.execute('SELECT version FROM workflow_runs WHERE id=?', (lease['run_id'],)).fetchone()[0]
            db.execute('INSERT INTO workflow_results VALUES(?,?,?,?,?,?)',
                       (lease['run_id'],packet['stage_id'],packet['skill_id'],version,digest,snapshot))

    def result_refs(self, run_id, stage_id):
        with self.store.connect() as db:
            return [dict(r) for r in db.execute('''SELECT r.* FROM workflow_results r WHERE run_id=? AND stage_id=?
                AND version=(SELECT MAX(x.version) FROM workflow_results x
                    WHERE x.run_id=r.run_id AND x.stage_id=r.stage_id AND x.skill_id=r.skill_id)''', (run_id,stage_id))]

    def finish(self, owner, elapsed, state, reason=''):
        with self.store.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            lease = self._owner(db, owner)
            refund = max(0, lease['reserved_seconds']-elapsed)
            db.execute('''UPDATE workflow_runs SET state=?,reason=?,seconds=seconds-?,position=position+?,
                version=version+1,updated=? WHERE id=?''',
                (state,reason,refund,int(state=='ready'),time.time(),lease['run_id']))
            db.execute('UPDATE workflow_stages SET state=?,seconds=seconds-? WHERE run_id=? AND stage_id=?',
                       ('advisory_complete' if state=='ready' else state,refund,lease['run_id'],lease['stage_id']))
            self.event(db, lease['run_id'], 'role_completed' if state=='ready' else state,
                       stage=lease['stage_id'], reason=reason)
            db.execute('DELETE FROM workflow_lease WHERE owner=?', (owner,))

    def wait_or_skip(self, run_id, version, stage, skip=False):
        with self.store.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT * FROM workflow_runs WHERE id=?', (run_id,)).fetchone()
            if row['state'] != 'ready' or row['version'] != version:
                raise BridgeError('Stale workflow version; inspect status.')
            db.execute('UPDATE workflow_runs SET state=?,position=position+?,version=version+1,updated=? WHERE id=?',
                       ('ready' if skip else 'waiting_for_codex',int(skip),time.time(),run_id))
            db.execute('UPDATE workflow_stages SET state=? WHERE run_id=? AND stage_id=?',
                       ('skipped' if skip else 'waiting_for_codex',run_id,stage['id']))
            self.event(db, run_id, 'skipped' if skip else 'checkpoint',stage=stage['id'], reason='not_relevant' if skip else stage['checkpoint'])

    def checkpoint(self, run_id, version, action, snapshot, note_digest, validation_status, rewind=None):
        with self.store.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            self._expire(db)
            row = db.execute('SELECT * FROM workflow_runs WHERE id=?', (run_id,)).fetchone()
            if row['version'] != version or row['state'] not in ('waiting_for_codex','handed_off','cancelled'):
                raise BridgeError('Checkpoint requires the current waiting/handoff version.')
            plan = json.loads(row['plan'])
            stages = plan['stages']
            current = stages[row['position']]
            if action in ('abort','reject'):
                state, position = ('aborted' if action=='abort' else 'rejected'), row['position']
            elif action == 'revise':
                limits = json.loads(row['limits'])
                if rewind is None or row['corrections'] >= limits['max_corrections']:
                    raise BridgeError('No remaining correction cycle or implementation checkpoint.')
                state, position = 'ready', rewind+1
                db.execute('UPDATE workflow_runs SET corrections=corrections+1 WHERE id=?', (run_id,))
                for stage in stages[position:]:
                    db.execute("UPDATE workflow_stages SET state='pending' WHERE run_id=? AND stage_id=?", (run_id,stage['id']))
                    # Old digest references are no longer evidence for this correction cycle.
                    # Attempt/event history and spent budgets remain intact.
                    db.execute('DELETE FROM workflow_results WHERE run_id=? AND stage_id=?', (run_id,stage['id']))
            else:
                position = row['position']+1
                state = 'codex_verified' if position == len(stages) else 'ready'
            plan['validation_status'] = validation_status
            db.execute('''UPDATE workflow_runs SET state=?,position=?,snapshot=?,plan=?,version=version+1,
                reason=?,updated=? WHERE id=?''', (state,position,snapshot,compact(plan),'codex_'+action,time.time(),run_id))
            if action != 'revise':
                db.execute("UPDATE workflow_stages SET state='codex_resolved' WHERE run_id=? AND stage_id=?", (run_id,current['id']))
            self.event(db, run_id, 'codex_'+action,stage=current['id'],reason=note_digest)

    def status(self, run_id):
        with self.store.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            self._expire(db)
        row = self.read(run_id)
        plan, limits = json.loads(row['plan']), json.loads(row['limits'])
        with self.store.connect() as db:
            stages = {r['stage_id']:dict(r) for r in db.execute('SELECT * FROM workflow_stages WHERE run_id=?', (run_id,))}
            attempts = [dict(r) for r in db.execute('''SELECT a.request_id,a.stage_id,a.skill_id,a.kind,a.model,a.state,
                a.input_tokens,a.output_tokens,a.output_bytes,u.duration,u.selection_reason,u.route_cap
                FROM workflow_attempts a LEFT JOIN usage u ON u.id=a.request_id WHERE a.run_id=? ORDER BY a.created''', (run_id,))]
        result = {'run_id':run_id,'workflow':plan['workflow'],'project_profile':plan['profile'],
                'version':row['version'],'state':row['state'],'reason':row['reason'],
                'next_stage':plan['stages'][row['position']]['id'] if row['position'] < len(plan['stages']) and row['state'] not in ('aborted','rejected') else None,
                'stages':[{'id':s['id'],'role':s.get('role'),'state':stages[s['id']]['state'],
                           'attempts':stages[s['id']]['attempts'],'seconds':round(stages[s['id']]['seconds'],3)} for s in plan['stages']],
                'budget':{'limits':limits, 'attempts':row['attempts'],'corrections':row['corrections'],
                          'reserved_tokens':row['reserved_tokens'],'output_tokens_reserved':row['output_tokens_reserved'],
                          'input_chars':row['input_chars'],'seconds':round(row['seconds'],3)},
                'attempts':attempts,'validation_status':plan['validation_status'],'codex_owns_decision':True}
        if 'delegation' in plan:
            result['delegation'] = plan['delegation']
            for stage in result['stages']:
                definition = next(s for s in plan['stages'] if s['id']==stage['id'])
                stage['execution'] = 'direct' if definition.get('direct') else 'role' if stage['role'] else 'codex'
        return result
