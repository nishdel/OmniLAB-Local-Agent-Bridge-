"""Companion-only durable evidence and receipts in the workflow database.

The journal does not execute workflow steps or checkpoints. A receipt is written
in the existing ledger transaction; delivery to the other database is repeatable.
No transaction spanning the two WAL databases is assumed to be atomic.
"""
import hashlib
import json

from .bridge import BridgeError
from .schemas import compact


def digest(value):
    return hashlib.sha256(compact(value).encode()).hexdigest()


class RecoveryJournal:
    def __init__(self, ledger, job=None):
        self.ledger = ledger
        self.job = job
        with ledger.store.connect() as db:
            if db.execute("SELECT 1 FROM sqlite_master WHERE name='companion_journal_meta'").fetchone():
                version = db.execute('SELECT version FROM companion_journal_meta WHERE slot=1').fetchone()
                if not version or version[0]!=1:
                    raise ValueError('Unsupported workflow recovery journal version')
            db.executescript('''
                CREATE TABLE IF NOT EXISTS companion_journal_meta (
                    slot INTEGER PRIMARY KEY CHECK(slot=1), version INTEGER NOT NULL);
                INSERT OR IGNORE INTO companion_journal_meta VALUES(1,1);
                CREATE TABLE IF NOT EXISTS companion_operations (
                    id TEXT PRIMARY KEY, attempt TEXT NOT NULL, request_digest TEXT NOT NULL,
                    request TEXT NOT NULL, started REAL NOT NULL, run_id TEXT,
                    base_version INTEGER, owner TEXT, phase TEXT NOT NULL,
                    receipt TEXT, receipt_digest TEXT, acknowledged INTEGER NOT NULL DEFAULT 0);
                CREATE TABLE IF NOT EXISTS companion_payloads (
                    operation_id TEXT NOT NULL, run_id TEXT NOT NULL, stage_id TEXT NOT NULL,
                    skill_id TEXT NOT NULL, version INTEGER NOT NULL, packet TEXT NOT NULL,
                    digest TEXT NOT NULL, snapshot TEXT NOT NULL,
                    PRIMARY KEY(operation_id,stage_id,skill_id,version));
            ''')
            if db.execute('SELECT version FROM companion_journal_meta').fetchone()[0] != 1:
                raise ValueError('Unsupported workflow recovery journal version')
            if job is not None:
                db.execute('BEGIN IMMEDIATE')
                old = db.execute('SELECT * FROM companion_operations WHERE id=?',(job['id'],)).fetchone()
                if old:
                    if old['attempt']!=job['attempt_id'] or old['request_digest']!=digest(job['request']):
                        raise ValueError('Recovery operation identity changed')
                    raise ValueError('Existing workflow operation must be reconciled, never re-executed')
                db.execute('''INSERT INTO companion_operations
                    (id,attempt,request_digest,request,started,phase) VALUES(?,?,?,?,?,'started')''',
                    (job['id'],job['attempt_id'],digest(job['request']),compact(job['request']),job['started']))

    def attach(self, db, run_id):
        op = self.operation(db,self.job['id'])
        expected = self.job['request']['version']
        expected = 0 if expected is None else expected
        if op['run_id'] is not None:
            if op['run_id']!=run_id or op['base_version']!=expected:
                raise BridgeError('Recovery operation scope changed')
            return
        row = db.execute('SELECT * FROM workflow_runs WHERE id=?',(run_id,)).fetchone()
        if row['version']!=expected:
            raise BridgeError('Recovery operation has a stale starting version')
        db.execute('UPDATE companion_operations SET run_id=?,base_version=? WHERE id=?',
                   (run_id,expected,op['id']))

    def claimed(self, db, owner):
        db.execute("UPDATE companion_operations SET owner=?,phase='running' WHERE id=?",
                   (owner,self.job['id']))

    def payload(self, db, packet, packet_digest, snapshot, run_id, version):
        if digest(packet)!=packet_digest:
            raise BridgeError('Recovery packet digest mismatch')
        db.execute('INSERT INTO companion_payloads VALUES(?,?,?,?,?,?,?,?)',
            (self.job['id'],run_id,packet['stage_id'],packet['skill_id'],version,
             compact(packet),packet_digest,snapshot))

    @staticmethod
    def operation(db, job_id):
        row = db.execute('SELECT * FROM companion_operations WHERE id=?',(job_id,)).fetchone()
        return dict(row) if row else None

    def packets(self, db, op, *, complete):
        request = json.loads(op['request'])
        available = {digest(p):p for p in request['handoffs']}
        for row in db.execute('SELECT * FROM companion_payloads WHERE operation_id=?',(op['id'],)):
            packet = json.loads(row['packet'])
            if digest(packet)!=row['digest']:
                raise ValueError('Corrupt saved recovery packet')
            available[row['digest']] = packet
        refs = db.execute('''SELECT r.* FROM workflow_results r WHERE run_id=? AND version=(
            SELECT MAX(x.version) FROM workflow_results x WHERE x.run_id=r.run_id
            AND x.stage_id=r.stage_id AND x.skill_id=r.skill_id)
            ORDER BY r.rowid''',(op['run_id'],)).fetchall()
        packets = []
        for ref in refs:
            packet = available.get(ref['digest'])
            if packet is None:
                if complete:
                    raise ValueError('Missing durable handoff content; digest alone is not recoverable')
                continue
            if (packet['stage_id'],packet['skill_id']) != (ref['stage_id'],ref['skill_id']):
                raise ValueError('Recovery packet identity mismatch')
            packets.append(packet)
        return packets

    def make_receipt(self, db, op, state, error=None, failure=None):
        workflow = self.ledger._status(db,op['run_id']) if op['run_id'] else None
        if workflow and op['owner']:
            workflow['evaluation'] = 'advisory_requires_codex' if workflow['state']=='ready' else 'codex_handoff'
        if workflow and failure:
            workflow['failure'] = failure
        packets = self.packets(db,op,complete=state=='succeeded') if op['run_id'] else []
        rows = [dict(r) for r in db.execute('''SELECT u.* FROM usage u JOIN workflow_attempts a
            ON a.request_id=u.id WHERE a.run_id=? AND a.created>=? ORDER BY a.created''',
            (op['run_id'],op['started']))] if op['run_id'] else []
        def total(field):
            return sum(r[field] for r in rows) if all(r[field] is not None for r in rows) else None
        result = {'answer':{'workflow':workflow,'handoffs':packets},'usage':{
            'input_tokens':total('input_tokens'),'output_tokens':total('output_tokens'),'attempts':rows}}
        if workflow is None:
            result['answer'].pop('workflow')
        receipt = {'job_id':op['id'],'attempt_id':op['attempt'],'request_digest':op['request_digest'],
            'run_id':op['run_id'],'version':workflow['version'] if workflow else None,
            'state':state,'error':error,'result':result}
        db.execute('UPDATE companion_operations SET phase=?,receipt=?,receipt_digest=? WHERE id=?',
                   ('committed' if state=='succeeded' else 'interrupted',compact(receipt),digest(receipt),op['id']))
        return receipt

    def committed(self, db, run_id, failure=None):
        op = self.operation(db,self.job['id'])
        if op['run_id']!=run_id or op['receipt'] is not None:
            raise BridgeError('Recovery transition identity mismatch')
        self.make_receipt(db,op,'succeeded',failure=failure)

    def prepare_interrupted(self, job):
        """Worker lock must prove the old owner is gone. Never finish a role here."""
        with self.ledger.store.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            op = self.operation(db,job['id'])
            if op is None:
                return None
            if op['attempt']!=job['attempt_id'] or op['request_digest']!=digest(job['request']):
                raise ValueError('Recovery operation identity changed')
            if op['receipt']:
                return self.read_receipt(op)
            if op['run_id']:
                row = db.execute('SELECT * FROM workflow_runs WHERE id=?',(op['run_id'],)).fetchone()
                lease = db.execute('SELECT * FROM workflow_lease WHERE owner=?',(op['owner'],)).fetchone()
                if (op['owner'] and row['state']=='running' and row['version']==op['base_version']+1
                        and lease and lease['run_id']==op['run_id']):
                    self.ledger._interrupt(db,lease)
                elif not ((row['version']==op['base_version'] and row['state']=='ready') or
                          (op['owner'] and row['version']==op['base_version']+2 and
                           row['state']=='handed_off' and row['reason']=='interrupted')):
                    raise ValueError('Stale recovery operation; newer ledger state requires inspection')
            # Full packets already committed are preserved, but without a terminal
            # transition receipt there is no proof that the whole step completed.
            return self.make_receipt(db,op,'interrupted',
                'Interrupted before the workflow transition committed; saved partial evidence retained; no automatic replay')

    @staticmethod
    def read_receipt(op):
        receipt = json.loads(op['receipt'])
        if digest(receipt)!=op['receipt_digest']:
            raise ValueError('Corrupt recovery receipt')
        return receipt

    def deliver(self, store, job_id):
        # Lock order is workflow DB, then companion DB. The first transaction is
        # read/check + acknowledgment; authoritative evidence was committed earlier.
        with self.ledger.store.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            op = self.operation(db,job_id)
            if not op or not op['receipt']:
                raise ValueError('No durable recovery receipt')
            receipt = self.read_receipt(op)
            if (op['attempt']!=receipt['attempt_id'] or op['id']!=receipt['job_id']
                    or op['request_digest']!=receipt['request_digest']
                    or op['request_digest']!=digest(json.loads(op['request']))
                    or op['run_id']!=receipt['run_id']):
                raise ValueError('Recovery receipt/header identity mismatch')
            current = db.execute('SELECT version FROM workflow_runs WHERE id=?',(receipt['run_id'],)).fetchone()
            current_version = current[0] if current else None
            disposition = store.apply_recovery(receipt,op['receipt_digest'],current_version)
            self.acknowledge(db,job_id)
            return disposition

    @staticmethod
    def acknowledge(db, job_id):
        db.execute('UPDATE companion_operations SET acknowledged=1 WHERE id=?',(job_id,))
