"""Recovery races, interrupted reconciliation, legacy evidence and migration."""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import time

import pytest

from test_companion_acceptance import candidate  # noqa: F401
from localagentbridge.companion_recovery import recover
from localagentbridge.companion_store import CompanionStore
from localagentbridge.companion_workflows import follow_workflow, service_for
from localagentbridge.workflow_recovery import RecoveryJournal, digest


def test_future_journal_schema_is_rejected_without_creating_current_tables(tmp_path):
    from localagentbridge.telemetry import Store
    from localagentbridge.workflow_store import WorkflowStore
    ledger=WorkflowStore(Store(tmp_path))
    with ledger.store.connect() as db:
        db.execute('CREATE TABLE companion_journal_meta(slot INTEGER PRIMARY KEY,version INTEGER)')
        db.execute('INSERT INTO companion_journal_meta VALUES(1,99)')
        before=db.execute('SELECT name,sql FROM sqlite_master ORDER BY name').fetchall()
    with pytest.raises(ValueError,match='Unsupported workflow recovery journal version'):
        RecoveryJournal(ledger)
    with ledger.store.connect() as db:
        assert db.execute('SELECT name,sql FROM sqlite_master ORDER BY name').fetchall()==before


def journal_for(store, jid):
    return RecoveryJournal(service_for(store,store.job(jid)).workflows.ledger)


def recorded(journal, jid):
    with journal.ledger.store.connect() as db:
        return journal.operation(db,jid)


def assert_one_review(store, run, count=1):
    snap=store.snapshot(run)
    assert len(snap['jobs'])==len(snap['events'])==count
    assert len({e['job_id'] for e in snap['events']})==count
    return snap


@pytest.mark.parametrize('point',[
    'journal:prepare_interrupted:before','journal:prepare_interrupted:after',
    'companion:apply_recovery:before','companion:apply_recovery:inside',
    'companion:apply_recovery:after','journal:acknowledge:before','journal:acknowledge:after',
])
def test_second_crash_during_reconciliation_retains_original_saved_payload(candidate,point):
    store,run,jid,worker,cli,chats,tmp_path,_=candidate
    worker('workflow:result:after')
    journal=journal_for(store,jid)
    with journal.ledger.store.connect() as db:
        original=db.execute('SELECT packet FROM companion_payloads WHERE operation_id=?',(jid,)).fetchone()[0]
    worker(point)
    worker()
    worker()
    assert len(chats)==1
    job=store.job(jid)
    assert job['state']=='interrupted'  # No committed end-of-step proof.
    assert job['result']['answer']['handoffs']==[json.loads(original)]
    assert job['result']['answer']['workflow']['state']=='handed_off'
    assert recorded(journal,jid)['acknowledged']==1
    assert_one_review(store,run)


def test_owned_process_termination_after_commit_recovers_exact_receipt(candidate):
    store,run,jid,worker,cli,chats,tmp_path,_=candidate
    sentinel=tmp_path/'committed'
    code='''
import sys,time
from pathlib import Path
from localagentbridge.workflow_store import WorkflowStore
from localagentbridge.companion import worker
original=WorkflowStore.finish
def paused(*args,**kwargs):
    result=original(*args,**kwargs)
    Path(sys.argv[2]).write_text('committed')
    time.sleep(120)
    return result
WorkflowStore.finish=paused
worker(sys.argv[1])
'''
    process=subprocess.Popen([sys.executable,'-B','-c',code,str(store.directory),str(sentinel)],
        cwd=tmp_path,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    try:
        until=time.monotonic()+20
        while not sentinel.exists() and process.poll() is None and time.monotonic()<until:
            time.sleep(.05)
        assert sentinel.exists()
        journal=journal_for(store,jid)
        original=json.loads(recorded(journal,jid)['receipt'])
        process.terminate()  # Terminate only this owned handle, never a name/PID scan.
        process.wait(timeout=10)
        worker()
        assert store.job(jid)['result']==original['result']
        assert store.job(jid)['state']=='succeeded'
        assert len(chats)==1
        assert_one_review(store,run)
    finally:
        if process.poll() is None:
            process.terminate()
        process.communicate(timeout=10)


def test_competing_and_repeated_receipt_delivery_is_idempotent(candidate):
    store,run,jid,worker,cli,chats,tmp_path,_=candidate
    worker('workflow:finish:after')
    journal=journal_for(store,jid)
    original=json.loads(recorded(journal,jid)['receipt'])['result']
    # Independent connections compete at the SQLite transaction boundary.
    with ThreadPoolExecutor(max_workers=4) as pool:
        outcomes=list(pool.map(lambda _:journal_for(store,jid).deliver(store,jid),range(12)))
    assert set(outcomes)=={'applied'}
    assert store.job(jid)['result']==original
    assert_one_review(store,run)
    # Separate recovering processes also compete for the existing kernel lock.
    code='''
import sys,time
from localagentbridge.companion_store import CompanionStore
from localagentbridge.companion_recovery import recover_locked
from localagentbridge.process_control import Lock
try:
    with Lock(__import__('pathlib').Path(sys.argv[1])/'worker.lock'):
        time.sleep(.2)
        recover_locked(CompanionStore(sys.argv[1]))
except RuntimeError:
    pass
'''
    processes=[subprocess.Popen([sys.executable,'-B','-c',code,str(store.directory)],cwd=tmp_path) for _ in range(2)]
    assert all(p.wait(timeout=20)==0 for p in processes)
    assert_one_review(store,run)
    assert store.job(jid)['result']==original and len(chats)==1


@pytest.mark.parametrize('protected',['cancelled','reviewed','finalized'])
def test_recovery_preserves_cancellation_reviews_and_final_decisions(candidate,protected):
    store,run,jid,worker,cli,chats,tmp_path,_=candidate
    worker('workflow:finish:after')
    journal=journal_for(store,jid)
    receipt=recorded(journal,jid)['receipt']
    if protected=='cancelled':
        store.cancel(run,jid)
    else:
        store.complete(jid,store.job(jid)['attempt_id'],state='interrupted',error='Supervisor inspected original incident')
        event=store.snapshot(run)['events'][0]
        store.decide(event['id'],'rejected','Preserve this real supervisor decision',local=True)
        if protected=='finalized':
            assert store.finalize(run,'Explicit blocked decision',False)=='blocked'
    before=store.snapshot(run)
    worker()
    worker()
    after=assert_one_review(store,run)
    assert len(chats)==1 and recorded(journal,jid)['receipt']==receipt
    assert after['jobs'][0]['state']==('cancelled' if protected=='cancelled' else 'interrupted')
    assert after['jobs'][0]['result'] is None
    if protected!='cancelled':
        assert after['events']==before['events']
        assert after['runs']==before['runs']
    assert after['recoveries'][0]['disposition']=='preserved_'+('review' if protected=='reviewed' else protected)


def test_stale_receipt_cannot_overwrite_newer_workflow_version(candidate):
    store,run,jid,worker,cli,chats,tmp_path,_=candidate
    worker('workflow:finish:after')
    engine=service_for(store,store.job(jid)).workflows
    journal=RecoveryJournal(engine.ledger)
    receipt=json.loads(recorded(journal,jid)['receipt'])
    prior=receipt['result']['answer']['workflow']
    row=engine.ledger.read(prior['run_id'])
    stage=json.loads(row['plan'])['stages'][row['position']]
    engine.ledger.wait_or_skip(prior['run_id'],prior['version'],stage)
    newer=engine.status(prior['run_id'])
    worker()
    assert engine.status(prior['run_id'])==newer
    assert store.job(jid)['state']=='interrupted' and store.job(jid)['result'] is None
    assert store.snapshot(run)['recoveries'][0]['disposition']=='stale_workflow_version'
    assert_one_review(store,run)
    assert len(chats)==1


@pytest.mark.parametrize('mutation',['receipt','attempt','request'])
def test_corrupt_or_mismatched_evidence_is_not_success(candidate,mutation):
    store,run,jid,worker,cli,chats,tmp_path,_=candidate
    worker('workflow:finish:after')
    journal=journal_for(store,jid)
    with journal.ledger.store.connect() as db:
        if mutation=='receipt':
            value=json.loads(recorded(journal,jid)['receipt'])
            value['result']['answer']['handoffs'][0]['payload']['possible_bugs']=['corrupt']
            db.execute('UPDATE companion_operations SET receipt=? WHERE id=?',(json.dumps(value),jid))
        else:
            db.execute('UPDATE companion_operations SET '+('attempt' if mutation=='attempt' else 'request_digest')+'=? WHERE id=?',('wrong',jid))
    worker()
    assert store.job(jid)['state']=='interrupted'
    assert store.job(jid)['result'] is None
    assert store.snapshot(run)['recoveries'][0]['disposition']=='intervention_required'
    assert len(chats)==1


def strip_journal(store):
    # Reproduce the exact old metadata-only schema in isolated test data; retain
    # all old usage, workflow, job and review rows for migration verification.
    with sqlite3.connect(store.directory/'usage/usage.sqlite3') as db:
        for table in ('companion_payloads','companion_operations','companion_journal_meta'):
            db.execute('DROP TABLE '+table)
    with store.db() as db:
        db.execute('DROP TABLE recoveries')
        db.execute('PRAGMA user_version=1')
    return CompanionStore(store.directory)


def test_legacy_missing_content_remains_unrecoverable_without_invention(candidate):
    store,run,jid,worker,cli,chats,tmp_path,_=candidate
    worker('workflow:finish:after')
    store=strip_journal(store)
    worker()
    assert store.job(jid)['state']=='interrupted' and store.job(jid)['result'] is None
    assert 'hashes cannot reconstruct' in store.snapshot(run)['recoveries'][0]['detail']
    assert len(chats)==1


def test_legacy_saved_result_restores_missing_event_without_changing_payload(candidate):
    store,run,jid,worker,cli,chats,tmp_path,_=candidate
    worker()
    before=store.job(jid)
    with store.db() as db:
        db.execute('DELETE FROM events WHERE job_id=?',(jid,))
    store=strip_journal(store)
    assert recover(store)[0]['disposition']=='legacy_event_repaired'
    recover(store)
    assert store.job(jid)==before
    assert_one_review(store,run)
    assert len(chats)==1


@pytest.mark.parametrize('decision',['accept','reject'])
def test_legacy_checkpoint_requires_and_preserves_exact_decision_proof(candidate,decision):
    store,run,jid,worker,cli,chats,tmp_path,_=candidate
    worker()
    waiting=follow_workflow(store,jid)
    worker()
    final=follow_workflow(store,waiting,checkpoint={'action':decision,'note':'Exact saved supervisor intent'})
    worker('workflow:checkpoint:after')
    journal=journal_for(store,final)
    expected=json.loads(recorded(journal,final)['receipt'])['result']
    store=strip_journal(store)
    worker()
    worker()
    assert store.job(final)['state']=='succeeded'
    assert store.job(final)['result']==expected
    assert store.job(final)['result']['answer']['workflow']['state']==('codex_verified' if decision=='accept' else 'rejected')
    assert all(e['state']=='pending' for e in assert_one_review(store,run,3)['events'])
    assert len(chats)==1


def test_legacy_checkpoint_with_different_note_is_not_inferred_approval(candidate):
    store,run,jid,worker,cli,chats,tmp_path,_=candidate
    worker()
    waiting=follow_workflow(store,jid)
    worker()
    final=follow_workflow(store,waiting,checkpoint={'action':'accept','note':'Actual intent'})
    worker('workflow:checkpoint:after')
    store=strip_journal(store)
    with store.db() as db:
        req=store.job(final)['request']
        req['checkpoint']['note']='Different intent'
        db.execute('UPDATE jobs SET request=? WHERE id=?',(json.dumps(req),final))
    worker()
    assert store.job(final)['state']=='interrupted' and store.job(final)['result'] is None
    assert len(chats)==1


@pytest.mark.parametrize('boundary',['before','inside','after'])
def test_review_decision_transaction_crash_is_atomic(candidate,boundary):
    store,run,jid,worker,cli,chats,tmp_path,_=candidate
    worker()
    event=store.snapshot(run)['events'][0]
    code='''
import sys,os
from contextlib import contextmanager
from localagentbridge.companion_store import CompanionStore
store=CompanionStore(sys.argv[1])
if sys.argv[3]=='before': os._exit(91)
original=store.db
@contextmanager
def db():
    with original() as connection:
        def trace(sql):
            if sys.argv[3]=='inside' and sql.startswith("UPDATE runs SET state='validating'"):
                os._exit(91)
        connection.set_trace_callback(trace)
        yield connection
store.db=db
store.decide(sys.argv[2],'accepted','Recorded supervisor validation',local=True)
os._exit(91)
'''
    result=subprocess.run([sys.executable,'-B','-c',code,str(store.directory),event['id'],boundary],cwd=tmp_path,timeout=20)
    assert result.returncode==91
    recover(store)
    after=assert_one_review(store,run)
    assert after['events'][0]['state']==('reviewed' if boundary=='after' else 'pending')
    assert after['runs'][0]['state']==('validating' if boundary=='after' else 'waiting_for_codex')


def test_additive_schema_migration_retains_all_existing_data(candidate):
    store,run,jid,worker,cli,chats,tmp_path,_=candidate
    worker()
    event=store.snapshot(run)['events'][0]
    store.decide(event['id'],'corrected','Historical validation evidence',local=True)
    job=store.job(jid)
    store=strip_journal(store)
    def dump(path,exclude):
        with sqlite3.connect(path) as db:
            tables=[r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'") if r[0] not in exclude]
            return {t:db.execute('SELECT * FROM '+t).fetchall() for t in tables}
    old_companion=dump(store.path,{'recoveries'})
    old_usage=dump(store.directory/'usage/usage.sqlite3',set())
    recover(store)
    assert dump(store.path,{'recoveries'})==old_companion
    assert dump(store.directory/'usage/usage.sqlite3',{'companion_operations','companion_payloads','companion_journal_meta'})==old_usage
    assert store.job(jid)==job
    with store.db() as db:
        assert db.execute('PRAGMA user_version').fetchone()[0]==2
        assert db.execute('PRAGMA journal_mode').fetchone()[0]=='wal'
        assert db.execute('PRAGMA synchronous').fetchone()[0]==2


def test_finalization_rejects_newer_ledger_and_requires_actual_checkpoint(candidate):
    store,run,jid,worker,cli,chats,tmp_path,_=candidate
    worker()
    waiting=follow_workflow(store,jid)
    worker()
    final=follow_workflow(store,waiting,checkpoint={'action':'accept','note':'Validated fixture'})
    worker()
    for event in store.snapshot(run)['events']:
        store.decide(event['id'],'accepted','Synthetic review evidence',local=True)
    journal=journal_for(store,final)
    with journal.ledger.store.connect() as db:
        db.execute('UPDATE workflow_runs SET version=version+1')
    with pytest.raises(ValueError,match='current committed supervisor checkpoint'):
        store.finalize(run,'Must not use stale verification',True)
    assert store.snapshot(run)['runs'][0]['finalized'] is None
