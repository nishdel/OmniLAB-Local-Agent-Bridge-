"""Model-free qualification-harness checks; no live exclusivity claim."""
import copy

import pytest

from scripts.strata_session_gate import SessionGate, observe, install_dispatch_guard
from localagentbridge.companion_store import CompanionStore
from localagentbridge.task_store import TaskStore


def snapshot():
    return dict(time=100, diagnostics_complete=True, resident_models=[], engines=[],
                stores={label: dict(paused=True, pending_jobs=[], reservation=None)
                        for label in ('active', 'isolated')})


def engine(created=20):
    return dict(pid=42, created=created, exe='strata.exe')


def gate(tmp_path):
    return SessionGate(tmp_path/'halt.json', ['active', 'isolated'], clock=lambda: 100)


def test_quiet_observation_and_exact_owned_attempt(tmp_path):
    g = gate(tmp_path)
    s = snapshot()
    g.check(s)
    s['engines'] = [engine()]
    s['stores']['isolated'] = dict(paused=False,
        pending_jobs=[dict(id='job', attempt_id='attempt')],
        reservation=dict(job_id='job', attempt_id='attempt', state='active'))
    g.check(s, owned_engines=[engine()], owned_attempt=('isolated', 'job', 'attempt'))


@pytest.mark.parametrize('change', ['loading', 'resident', 'queued', 'unpaused',
                                  'diagnostics', 'stale', 'missing_store', 'uncertain'])
def test_prestart_or_dispatch_blocks_without_mutating_inputs(tmp_path, change):
    s = snapshot()
    if change == 'loading': s['engines'] = [engine()]
    if change == 'resident': s['resident_models'] = ['competitor']
    if change == 'queued': s['stores']['active']['pending_jobs'] = [dict(id='other', attempt_id=None)]
    if change == 'unpaused': s['stores']['active']['paused'] = False
    if change == 'diagnostics': s['diagnostics_complete'] = False
    if change == 'stale': s['time'] = 94
    if change == 'missing_store': del s['stores']['active']
    if change == 'uncertain': s['stores']['active']['reservation'] = dict(state='cancellation_pending')
    before = copy.deepcopy(s)
    with pytest.raises(ValueError, match='blocked'): gate(tmp_path).check(s)
    assert s == before


def test_competitor_after_admission_latches_across_supervisors(tmp_path):
    g = gate(tmp_path)
    g.check(snapshot())
    s = snapshot()
    s['engines'] = [engine()]
    with pytest.raises(ValueError, match='loading or running'): g.check(s)
    with pytest.raises(ValueError, match='halted'): gate(tmp_path).check(snapshot())


@pytest.mark.parametrize('rows', [[], [engine(created=21)], [dict(pid=42)]])
def test_missing_owned_identity_or_pid_reuse_blocks(tmp_path, rows):
    s = snapshot()
    s['engines'] = rows
    with pytest.raises(ValueError): gate(tmp_path).check(s, owned_engines=[engine()])


def test_two_stores_can_reserve_independently_and_gate_preserves_uncertainty(tmp_path):
    states, jobs = {}, {}
    for label in ('active', 'isolated'):
        store = CompanionStore(tmp_path/label)
        tasks = TaskStore(store)
        run = store.create_run(tmp_path, 'a'*40)
        job_id = store.submit(run, label, {'contract': {'backend': 'strata'}})
        job = store.job(job_id) | {'attempt_id': label+'-attempt'}
        tasks.reserve(job)
        states[label], jobs[label] = (store, tasks), job
    s = snapshot()
    for label, (store, _) in states.items():
        s['stores'][label]['reservation'] = store.snapshot()['inference_reservation']
    with pytest.raises(ValueError, match='reservation'):
        gate(tmp_path).check(s, owned_attempt=('isolated', jobs['isolated']['id'], 'isolated-attempt'))
    # Existing cleanup is used only for owned work; uncertain termination holds it.
    states['isolated'][1].release(jobs['isolated'], confirmed=False)
    assert states['isolated'][0].snapshot()['inference_reservation']['state'] == 'cancellation_pending'
    assert states['active'][0].snapshot()['inference_reservation']['state'] == 'active'
    states['isolated'][1].release(jobs['isolated'], confirmed=True)
    assert states['isolated'][0].snapshot()['inference_reservation'] is None
    assert states['active'][0].snapshot()['inference_reservation']['state'] == 'active'


def test_observer_sees_loading_runner_even_when_provider_is_empty(tmp_path, monkeypatch):
    import httpx
    import psutil
    from types import SimpleNamespace
    store = CompanionStore(tmp_path/'store')
    TaskStore(store)
    runner = SimpleNamespace(info={'name': 'llama-server.exe'}, pid=42,
                             create_time=lambda: 20, exe=lambda: 'llama-server.exe')
    monkeypatch.setattr(psutil, 'process_iter', lambda _: [runner])
    monkeypatch.setattr(httpx.Client, 'get', lambda self, url: httpx.Response(
        200, json={'models': []}, request=httpx.Request('GET', url)))
    path = store.directory/'companion.sqlite3'
    before = path.read_bytes()
    result = observe({'active': path}, 'http://127.0.0.1:11434')
    assert result['diagnostics_complete'] and result['resident_models'] == []
    assert result['engines'] == [dict(pid=42, created=20, exe='llama-server.exe')]
    assert result['stores']['active']['paused'] is False
    assert path.read_bytes() == before


def test_observer_missing_provider_is_unknown_not_idle(monkeypatch):
    import httpx
    import psutil
    monkeypatch.setattr(psutil, 'process_iter', lambda _: [])
    def unavailable(*_):
        raise httpx.ConnectError('metadata unavailable')
    monkeypatch.setattr(httpx.Client, 'get', unavailable)
    result = observe({}, 'http://127.0.0.1:11434')
    assert not result['diagnostics_complete']
    assert result['resident_models'] is None


def test_dispatch_hook_blocks_later_turn_and_restores_only_its_process(tmp_path, monkeypatch):
    import asyncio
    from localagentbridge.inference import ChatProvider
    calls = []
    async def fake_chat(*args, **kwargs):
        calls.append((args, kwargs))
        return 'synthetic success'
    monkeypatch.setattr(ChatProvider, 'chat', fake_chat)
    s = snapshot()
    restore = install_dispatch_guard(gate(tmp_path), lambda: s, lambda: {})
    try:
        assert asyncio.run(ChatProvider.chat(None)) == 'synthetic success'
        s['engines'] = [engine()]
        with pytest.raises(ValueError, match='blocked'):
            asyncio.run(ChatProvider.chat(None))
        s['engines'] = []
        with pytest.raises(ValueError, match='halted'):
            asyncio.run(ChatProvider.chat(None))
        assert len(calls) == 1
    finally:
        restore()
    assert ChatProvider.chat is fake_chat
