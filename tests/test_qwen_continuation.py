"""Deterministic orchestration regressions plus explicit harmless Windows process checks."""
import asyncio
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import httpx
import psutil
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import qwen_benchmark as qb
import qwen_benchmark_io as io
import qwen_benchmark_guard as guard
from qwen_benchmark_notify import Notifier


def row(pid,created=10,ppid=0):
    return dict(pid=pid,created=created,ppid=ppid,name='llama-server.exe',exe='same/runtime/llama-server.exe')


class Membership:
    def __init__(self,*members): self.members=set(members)
    def contains(self,p): return (p['pid'],p['created']) in self.members


def test_child_created_after_old_descendant_snapshot(tmp_path):
    old_permitted={1}
    table={1:row(1,1)}
    def enumerate_processes():
        table[2]=row(2,10,1)  # Appears after the old guard took its permitted PID snapshot.
        return [table[2]]
    assert 2 not in old_permitted  # Old algorithm would flag this child.
    evidence=tmp_path/'ownership.jsonl'
    assert guard.workloads(Membership((1,1),(2,10)),evidence,enumerate_processes,table.__getitem__)==[]
    record=json.loads(evidence.read_text())
    assert record['classification']=='owned' and record['ancestry'][0]['created']==1


def test_runner_replaced_between_requests():
    table={1:row(1,1),2:row(2,10,1)}
    membership=Membership((1,1),(2,10))
    assert not guard.workloads(membership,enumerate_processes=lambda:[table[2]],probe=table.__getitem__)
    del table[2];table[3]=row(3,11,1);membership.members.add((3,11))
    assert not guard.workloads(membership,enumerate_processes=lambda:[table[3]],probe=table.__getitem__)


def test_external_same_binary_is_revalidated_and_blocked():
    seen=[]
    def probe(pid): seen.append(pid); return row(pid)
    found=guard.workloads(Membership((1,1)),enumerate_processes=lambda:[row(2)],probe=probe)
    assert found[0]['classification']=='external' and found[0]['revalidated']
    assert len(seen)>=4


def test_pid_reuse_never_grants_old_ownership():
    assert guard.inspect_candidate(2,Membership((2,10)),lambda _:row(2,20))['classification']=='external'
    calls=iter([row(2,10),row(2,20),row(2,20),row(2,20)])
    found=guard.workloads(Membership(),enumerate_processes=lambda:[row(2)],probe=lambda _:next(calls))
    assert found[0]['first_observation']['classification']=='unresolved'
    class ReplacedHandle:
        def contains(self,p): raise RuntimeError('PID identity changed before opening handle')
    assert guard.inspect_candidate(2,ReplacedHandle(),lambda _:row(2))['classification']=='unresolved'


def test_disappeared_process_is_not_a_conflict():
    def gone(_): raise psutil.NoSuchProcess(2)
    assert guard.inspect_candidate(2,Membership(),gone)['classification']=='vanished'
    assert not guard.workloads(Membership(),enumerate_processes=lambda:[row(2)],probe=gone)


def test_access_denied_is_unresolved_and_ancestry_is_explicit():
    def denied(_): raise psutil.AccessDenied(2)
    found=guard.workloads(Membership(),enumerate_processes=lambda:[row(2)],probe=denied)
    assert found[0]['classification']=='unresolved' and found[0]['revalidated']
    def partial(pid):
        if pid==1: raise psutil.AccessDenied(1)
        return row(2,10,1)
    owned=guard.inspect_candidate(2,Membership((2,10)),partial)
    assert owned['classification']=='owned' and owned['ancestry_note']=='parent access denied'


def test_unknown_enumeration_name_is_rechecked_not_silently_allowed():
    found=guard.workloads(Membership(),enumerate_processes=lambda:[{'pid':2,'name':None}],probe=lambda _:row(2))
    assert found[0]['classification']=='external' and found[0]['revalidated']


def fixture_parent(tmp_path,monkeypatch):
    monkeypatch.setattr(qb,'OUT',tmp_path/'experiments')
    job=qb.freeze(fixture=True)
    state=io.read(job/'state.json')
    # Harmless evidence, one completed case and one failed case; never call a model.
    state.update(state='failed',worker=None)
    state['cases'][0].update(state='completed',attempts=[])
    state['cases'][1].update(state='failed',attempts=[])
    io.atomic(job/'state.json',state)
    qb.finalize(job)
    return job


def fake_cli(monkeypatch):
    calls=[]
    class Process:
        pid=os.getpid()
        def wait(self): return 0
    def complete(argv,**kwargs):
        calls.append(argv)
        assert '--last' not in argv and 'read-only' in argv and '--ignore-user-config' in argv
        io.atomic(Path(argv[argv.index('--output-last-message')+1]),
                  {'review_status':'completed','report_markdown':'CALLBACK_FIXTURE_OK'})
        return Process()
    monkeypatch.setattr(qb.subprocess,'Popen',complete)
    monkeypatch.setattr(qb,'alive',lambda _:False)
    return calls


def test_failed_parent_review_then_continuation_has_own_review(tmp_path,monkeypatch):
    parent=fixture_parent(tmp_path,monkeypatch)
    calls=fake_cli(monkeypatch)
    assert qb.review(parent,fixture_prompt=True)['state']=='completed'
    before={p.relative_to(parent):io.sha(p) for p in parent.rglob('*') if p.is_file()}
    child=qb.continue_job(parent)
    state=io.read(child/'state.json');config=io.read(child/'experiment.json')
    assert state['cases'][0]['inherited_from']=={'job':str(parent),'case_id':'fixture/one'}
    assert state['cases'][0]['attempts']==[] and state['cases'][1]['state']=='queued'
    assert config['settings']==io.read(parent/'experiment.json')['settings']
    assert io.read(child/'continuation.json')['runner_hashes']['scripts/qwen_benchmark_guard.py']==io.sha(ROOT/'scripts/qwen_benchmark_guard.py')
    async def instant(job,config,case,attempt,progress):
        assert case['id']=='fixture/two'
        return {'fixture':True}
    monkeypatch.setattr(qb,'execute_case',instant)
    asyncio.run(qb.batch(child,state,config))
    manifest=qb.finalize(child)
    assert manifest['new_completed_count']==1 and len(manifest['inherited_completed'])==1
    assert qb.review(child,fixture_prompt=True)['state']=='completed'
    qb.review(child,fixture_prompt=True);qb.review(parent,fixture_prompt=True)
    assert len(calls)==2
    assert all(io.sha(parent/p)==digest for p,digest in before.items())


def test_ambiguous_review_does_not_spawn_again(tmp_path,monkeypatch):
    parent=fixture_parent(tmp_path,monkeypatch)
    calls=fake_cli(monkeypatch)
    io.atomic(parent/'review-state.json',{'state':'started','automatic_attempt_claimed':True})
    assert qb.review(parent,manual=True)['state']=='interrupted-review'
    assert not calls
    with pytest.raises(RuntimeError,match='ambiguous'):
        qb.continue_job(parent)


def test_continuation_duplicate_queue_and_launch_snapshot(tmp_path,monkeypatch):
    parent=fixture_parent(tmp_path,monkeypatch)
    child=qb.continue_job(parent)
    with pytest.raises(RuntimeError,match='existing continuation'):
        qb.continue_job(parent)
    observed=[]
    class Process: pid=os.getpid()
    def detached(argv,*args): observed.append(argv);return Process()
    monkeypatch.setattr(qb,'detached',detached)
    result=qb.launch(child)
    assert observed[0][1]==str(child/'snapshot/scripts/qwen_benchmark.py')
    assert io.sha(Path(observed[0][1]))==io.sha(ROOT/'scripts/qwen_benchmark.py')
    assert result['job_id']==child.name


def notification_job(tmp_path):
    io.atomic(tmp_path/'state.json',{'job_id':'fixture-notify','execution_id':'epoch-1','state':'running',
        'cases':[{'id':'one','state':'completed','inherited_from':{}},{'id':'two','state':'queued'}]})
    return tmp_path


def notify_config(monkeypatch):
    monkeypatch.setenv('TEST_NTFY_TOKEN','fixture-not-a-secret')
    return dict(enabled=True,private_destination_verified=True,server_url='https://notify.invalid',
                topic='fixture-private',token_env='TEST_NTFY_TOKEN')


def test_notifications_disabled_without_private_configuration(tmp_path):
    n=Notifier(notification_job(tmp_path))
    n.start();n.emit('launched');n.drain()
    assert io.read(next((tmp_path/'notifications').glob('*.json')))['delivery']=='disabled'
    assert io.read(tmp_path/'notification-state.json')['state']=='disabled'


@pytest.mark.parametrize('config',[[],{'enabled':True,'server_url':42},
                                  {'enabled':True,'server_url':'https://unverified.invalid'}])
def test_invalid_optional_notification_config_is_disabled(tmp_path,config):
    n=Notifier(notification_job(tmp_path),config)
    n.start();n.emit('launched');n.close()
    assert not n.valid() and io.read(tmp_path/'notification-state.json')['state']=='disabled'


def test_notifications_minimal_bounded_and_deduplicated(tmp_path,monkeypatch):
    calls=[]
    def handle(request):
        calls.append(request)
        assert request.extensions['timeout']=={'connect':2,'read':5,'write':5,'pool':5}
        assert 'fixture-not-a-secret' not in request.content.decode()
        return httpx.Response(200,json={'id':'server-acceptance-only'})
    n=Notifier(notification_job(tmp_path),notify_config(monkeypatch),httpx.MockTransport(handle))
    for kind in ('launched','case-completed','terminal','review-ready','review-failed','progress'):
        n.emit(kind,case='one' if kind=='case-completed' else None)
        n.emit(kind,case='one' if kind=='case-completed' else None)
    n.drain();n.drain()
    assert len(calls)==6
    for path in (tmp_path/'notifications').glob('*.json'):
        assert io.read(path)['delivery']=='server-accepted'
        assert 'fixture-not-a-secret' not in path.read_text()


@pytest.mark.parametrize('failure',['network','auth','interrupted'])
def test_notification_failure_cannot_change_benchmark(tmp_path,monkeypatch,failure):
    job=notification_job(tmp_path);before=io.sha(job/'state.json')
    calls=[]
    def handle(request):
        calls.append(request)
        if failure=='network':raise httpx.ReadTimeout('secret URL must not be logged')
        return httpx.Response(401)
    n=Notifier(job,notify_config(monkeypatch),httpx.MockTransport(handle));n.emit('terminal')
    path=next((job/'notifications').glob('*.json'))
    if failure=='interrupted':
        event=io.read(path);event['delivery']='sending';io.atomic(path,event)
    n.drain();n.drain()
    assert io.sha(job/'state.json')==before
    assert io.read(path)['delivery']==('failed' if failure=='auth' else 'ambiguous')
    assert len(calls)==(0 if failure=='interrupted' else 1)
    assert 'secret URL' not in path.read_text()


@pytest.mark.skipif(os.name!='nt',reason='Real Windows job membership/lifecycle')
def test_real_windows_owned_children_replacement_and_external_same_executable(tmp_path):
    script=tmp_path/'harmless.py'
    script.write_text('import subprocess,sys,time,json,psutil\nfrom pathlib import Path\n'
        'sys.path.insert(0,'+repr(str(ROOT/'scripts'))+')\nfrom qwen_benchmark_io import identity\n'
        'p=Path('+repr(str(tmp_path))+')\n'
        'for i in range(2):\n'
        ' child=subprocess.Popen([sys.executable,"-c","import time;time.sleep(20)"],stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)\n'
        ' q=psutil.Process(child.pid)\n'
        ' (p/(str(i)+".json")).write_text(json.dumps(identity(q.pid)))\n'
        ' while not (p/(str(i)+".release")).exists(): time.sleep(.02)\n'
        ' child.terminate();child.wait()\n'
        'time.sleep(20)\n')
    runtime=io.OwnedRuntime([sys.executable,str(script)],tmp_path,os.environ.copy(),tmp_path)
    external=subprocess.Popen([sys.executable,'-c','import time;time.sleep(20)'],stdin=subprocess.DEVNULL,
                              stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=subprocess.CREATE_NO_WINDOW)
    try:
        for index in range(2):
            end=time.monotonic()+8
            while not (tmp_path/f'{index}.json').exists() and time.monotonic()<end:time.sleep(.02)
            child=io.read(tmp_path/f'{index}.json')
            assert runtime.contains(child)
            with pytest.raises(RuntimeError,match='creation identity'):
                runtime.contains(child | {'created_filetime':child['created_filetime']+1})
            assert not runtime.contains(io.identity(external.pid))
            if index==0:(tmp_path/'0.release').touch()
        runtime.close()
        assert not io.alive(child) and external.poll() is None
    finally:
        if runtime.process.poll() is None:runtime.close()
        external.terminate();external.wait(timeout=5)
