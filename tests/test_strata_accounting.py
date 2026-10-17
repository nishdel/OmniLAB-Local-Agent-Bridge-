"""Public synthetic admission coverage. No Strata assets/runtime attestation."""
import asyncio
import copy
import json
from pathlib import Path

import httpx
import pytest

from localagentbridge import strata_accounting as exact
from localagentbridge.inference import ChatProvider, ProviderError
from localagentbridge.local_profile import provider_settings
from localagentbridge.selective_config import validate_policy
from localagentbridge.task_contract import TaskLimits, digest


def observation():
    return dict(ready=True, identity_verified=True, identity='synthetic-test-only',
        context_tokens=16384, effective_context_tokens=16384, tools_advertised=True,
        template_sha256='synthetic', build_info='test-only', serving_model='fixture',
        model='fixture', backend='strata')


def provider(monkeypatch, count=100, *, enabled=True):
    posted = []
    settings = {'enabled': True, 'endpoint': 'http://127.0.0.1:8080'}
    if enabled:
        settings['exact_accounting'] = {'explicit_test_identity': True}
    p = ChatProvider('strata', settings, httpx.MockTransport(lambda r: posted.append(json.loads(r.content)) or
        httpx.Response(200, json={'choices': [{'message': {'content': 'mock'}, 'finish_reason': 'stop'}]})))
    async def inspect(self, model):
        return observation()
    async def counter(selection, settings, payload, observed):
        exact.validate_payload(payload)
        return {'input_tokens': count, 'request_sha256': digest(payload), 'server_context_reserve': 8}
    monkeypatch.setattr(ChatProvider, 'inspect', inspect)
    monkeypatch.setattr(exact, 'count_request', counter)
    return p, posted


@pytest.mark.parametrize('delta,admitted', [(-1, True), (0, True), (1, False)])
def test_exact_boundary(monkeypatch, delta, admitted):
    limits = TaskLimits(context_tokens=2048, output_tokens=64, context_safety_tokens=17, transport_retries=0)
    p, calls = provider(monkeypatch, 2048-64-17-8+delta)
    if admitted:
        result = asyncio.run(p.chat('fixture', [{'role': 'user', 'content': 'x'}], limits))
        assert result['usage']['input_tokens'] is None
        assert result['context_accounting']['actual_input_tokens'] is None
    else:
        with pytest.raises(ProviderError, match='Exact whole-prompt') as e:
            asyncio.run(p.chat('fixture', [{'role': 'user', 'content': 'x'}], limits))
        assert e.value.termination_confirmed
    assert len(calls) == int(admitted)
    assert p.last_accounting['reserved_output_tokens'] == 64
    assert p.last_accounting['safety_tokens'] == 17
    assert p.last_accounting['server_context_reserve'] == 8


@pytest.mark.parametrize('field', ['output_tokens', 'context_safety_tokens'])
def test_reserves_independently_reject(monkeypatch, field):
    p, calls = provider(monkeypatch, 1976)
    limits = TaskLimits(context_tokens=2048, output_tokens=64, transport_retries=0)
    limits = limits.model_copy(update={field: getattr(limits, field)+1})
    with pytest.raises(ProviderError):
        asyncio.run(p.chat('fixture', [{'role': 'user', 'content': 'x'}], limits))
    assert not calls


def test_frozen_payload_and_limits(monkeypatch):
    p, calls = provider(monkeypatch)
    messages = [{'role': 'user', 'content': 'before'}]
    limits = TaskLimits(output_tokens=64)
    async def counter(*args):
        messages[0]['content'] = 'after'
        limits.output_tokens = 1000
        # Even the diagnostic request view is not the dispatch snapshot.
        p.last_effective_request['messages'][0]['content'] = 'tampered'
        return {'input_tokens': 100, 'request_sha256': digest(args[2]), 'server_context_reserve': 8}
    monkeypatch.setattr(exact, 'count_request', counter)
    asyncio.run(p.chat('fixture', messages, limits))
    assert calls[0]['messages'][0]['content'] == 'before'
    assert calls[0]['max_tokens'] == 64


@pytest.mark.parametrize('failure', ['missing', 'settings', 'identity', 'count', 'stale'])
def test_unavailable_or_changed_count_fails_closed(monkeypatch, failure):
    p, calls = provider(monkeypatch)
    async def counter(*args):
        if failure == 'missing':
            raise FileNotFoundError('Missing tokenizer')
        if failure == 'count':
            raise ValueError('Tokenizer failed')
        if failure == 'settings':
            p.settings['temperature'] = 1
        if failure == 'identity':
            async def changed(_):
                return observation() | {'identity': 'changed'}
            p.inspect = changed
        return {'input_tokens': 100, 'request_sha256': 'stale' if failure == 'stale' else digest(args[2]), 'server_context_reserve': 8}
    monkeypatch.setattr(exact, 'count_request', counter)
    with pytest.raises(ProviderError) as e:
        asyncio.run(p.chat('fixture', [{'role': 'user', 'content': 'x'}], TaskLimits()))
    assert e.value.termination_confirmed and not calls
    assert p.last_accounting['classification'] == 'exact_counting_unavailable'


@pytest.mark.parametrize('change', ['message', 'tool', 'stream', 'bytes'])
def test_unsupported_and_independent_bytes(monkeypatch, change):
    p, calls = provider(monkeypatch)
    messages = [{'role': 'user', 'content': 'x'}]
    tools = []
    if change == 'message': messages[0]['audio'] = 'unsupported'
    if change == 'tool': tools = [{'type': 'function', 'function': {'name': 'f', 'strict': True}}]
    if change == 'bytes': messages[0]['content'] = 'x' * exact.MAX_REQUEST_BYTES
    with pytest.raises(ProviderError):
        asyncio.run(p.chat('fixture', messages, TaskLimits(), tools=tools, stream=change == 'stream'))
    assert not calls


def test_eight_full_turns_and_oversized_next_turn(monkeypatch):
    p, calls = provider(monkeypatch)
    counted = []
    async def counter(*args):
        payload = args[2]
        counted.append(copy.deepcopy(payload))
        return {'input_tokens': 100*len(payload['messages']), 'request_sha256': digest(payload), 'server_context_reserve': 8}
    monkeypatch.setattr(exact, 'count_request', counter)
    messages = [{'role': 'user', 'content': 'Unicode 漢😀 <|im_start|> </think> "\\n"'}]
    tools = [{'type': 'function', 'function': {'name': 'terminal', 'parameters': {'type': 'object'}}}]
    limits = TaskLimits(context_tokens=2048, output_tokens=64)
    for turn in range(8):
        asyncio.run(p.chat('fixture', messages, limits, tools=tools))
        messages += [{'role': 'assistant', 'content': None, 'tool_calls': [{'id': str(turn), 'type': 'function',
            'function': {'name': 'terminal', 'arguments': '{"command":"read"}'}}]},
            {'role': 'tool', 'tool_call_id': str(turn), 'content': 'result'}]
    assert [len(p['messages']) for p in counted] == list(range(1, 16, 2))
    assert len(calls) == 8 and all(p['tools'] == tools for p in calls)
    messages += [{'role': 'user', 'content': 'more'}]*3
    with pytest.raises(ProviderError):
        asyncio.run(p.chat('fixture', messages, limits, tools=tools))
    assert len(calls) == 8


def test_default_off_and_no_provider_substitution(monkeypatch):
    p, calls = provider(monkeypatch, enabled=False)
    async def forbidden(*args): raise AssertionError('Exact counter must not run')
    monkeypatch.setattr(exact, 'count_request', forbidden)
    with pytest.raises(ProviderError, match='Conservative'):
        asyncio.run(p.chat('fixture', [{'role': 'user', 'content': 'x'*17000}], TaskLimits()))
    assert not calls


def test_profile_only_schema_and_resolution(tmp_path):
    from types import SimpleNamespace
    selection = {'mode': exact.MODE, 'manifest_path': str(tmp_path/'manifest.json'), 'manifest_sha256': 'a'*64}
    profile = {'backend': 'strata', 'model': 'fixture', 'identity': 'synthetic-test-only',
               'limits': {'context_tokens': 16384}, 'context_accounting': selection}
    validate_policy({'model_profiles': [profile]})
    settings = provider_settings({'model_profiles': [profile]},
        SimpleNamespace(backend='strata', model='fixture', exact_identity='synthetic-test-only'))
    assert settings['exact_accounting'] == selection
    assert settings['_accounting_profile']['identity'] == 'synthetic-test-only'
    with pytest.raises(ValueError): validate_policy({'providers': {'strata': {'exact_accounting': selection}}})
    with pytest.raises(ValueError): validate_policy({'model_profiles': [profile | {'backend': 'ollama'}]})
    with pytest.raises(ValueError): exact.validate_selection(selection | {'input_tokens': 1})
    with pytest.raises(FileNotFoundError): exact.read_manifest(selection)
    Path(selection['manifest_path']).write_text('{}')
    with pytest.raises(ValueError, match='changed'): exact.read_manifest(selection)


@pytest.mark.parametrize('changed', ['profile', 'runtime', 'template', 'settings', 'tokenizer', 'source'])
def test_scope_identity_rejection(tmp_path, changed):
    source, tokenizer = tmp_path/'source', tmp_path/'tokenizer'
    paths = [source/n for n in ('serve/server.py', 'serve/frontend.py', 'tools/strata_tokenizer.py')]
    paths += [tokenizer/n for n in ('vocab.json', 'merges.txt', 'token_type.json', 'chat_template.jinja')]
    files = {str(p.resolve()): 'synthetic-sha' for p in paths}
    payload = {'model': 'fixture', 'messages': [], 'max_tokens': 1536}
    m = {'model': 'fixture', 'profile_identity': 'synthetic-test-only', 'template_sha256': 'synthetic',
         'upstream_commit': 'base', 'config_path': 'config', 'config_sha256': 'config-sha',
         'source': str(source), 'tokenizer': str(tokenizer), 'files': files,
         'request_settings_sha256': digest({k:v for k,v in payload.items() if k != 'messages'} | {'tool_choice': 'auto'})}
    settings = {'_accounting_profile': {'model': m['model'], 'identity': m['profile_identity']},
        'binding': {'identity': m['profile_identity'], 'source_commit': 'base', 'config_path': 'config',
                    'config_sha256': 'config-sha', 'artifacts': [{'path': p, 'sha256': h} for p,h in files.items()]}}
    observed = observation()
    exact.verify_scope(m, settings, payload, observed)
    if changed == 'profile': settings['_accounting_profile']['identity'] = 'caller-claim'
    if changed == 'runtime': observed['identity'] = 'unverified'
    if changed == 'template': observed['template_sha256'] = 'changed'
    if changed == 'settings': payload['max_tokens'] = 64
    if changed == 'tokenizer': settings['binding']['artifacts'][-1]['sha256'] = 'changed'
    if changed == 'source': settings['binding']['artifacts'][0]['sha256'] = 'changed'
    with pytest.raises(ValueError): exact.verify_scope(m, settings, payload, observed)


@pytest.mark.parametrize('kind', ['oversized', 'unsupported', 'count_failure'])
def test_mailbox_job_rejection_lifecycle(tmp_path, monkeypatch, kind):
    from localagentbridge.companion_store import CompanionStore
    from localagentbridge.task_store import TaskStore
    from localagentbridge import selective
    from test_selective_contracts import contract, request
    from test_selective_flows import FakeSandbox
    p, calls = provider(monkeypatch, 20000)
    if kind == 'count_failure':
        async def failed(*args): raise ValueError('Missing counting evidence')
        monkeypatch.setattr(exact, 'count_request', failed)
    class Mailbox(FakeSandbox):
        def read(self, *args):
            result = super().read(*args)
            if args[2] == '/exchange/request.json' and kind == 'unsupported':
                result['body']['response_format'] = {'type': 'json_object'}
            return result
    monkeypatch.setattr(selective, 'git_snapshot', lambda *a: {'subject.py': b'x=1\n', 'check.py': b'assert x==2\n'})
    c = contract(tmp_path, backend='strata', model='fixture', exact_identity='synthetic-test-only',
                 limits={'steps': 8, 'transport_retries': 0})
    r = request(c, 'local_implementation')
    r['policy'].update(providers={'strata': p.settings}, sandbox={},
        memory_plan={'supervisor_verified': True, 'os_and_apps_mb': 1, 'lab_mb': 1,
                     'runtime_mb': 1, 'context_cache_mb': 1, 'headroom_mb': 1})
    store = CompanionStore(tmp_path/'store')
    run = store.create_run(tmp_path, 'a'*40)
    jid = TaskStore(store).submit_many(run, [r])[0]
    job = store.claim_job({})
    sandbox = Mailbox()
    asyncio.run(selective.execute(store, job, p.transport, lambda _: sandbox))
    assert store.job(jid)['state'] == 'failed', store.job(jid)
    state = TaskStore(store).get(jid)
    assert state['execution_status'] == 'failed' and state['review_status'] == 'escalated'
    assert store.snapshot()['inference_reservation'] is None
    rejected = list(selective.artifact_dir(store, job).glob('rejected-*.json'))
    assert len(rejected) == 1 and not calls
    assert json.loads(rejected[0].read_text())['context_accounting']['admitted'] is False
    assert state['evidence']['usage'][0]['input_tokens'] is None
    assert all(not c['running'] for c in sandbox.containers.values())


@pytest.mark.skipif(__import__('os').name != 'nt', reason='Windows venv redirector containment')
def test_counter_cancellation_contains_python_descendants():
    import psutil
    import sys
    async def run():
        owner = exact.CounterContainment()
        process = await asyncio.create_subprocess_exec(sys.executable, '-I', '-B', '-c',
            'import time; time.sleep(30)', creationflags=owner.flags,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        owner.attach(process.pid)
        root = psutil.Process(process.pid)
        await asyncio.sleep(.3)
        identities = [root, *root.children(recursive=True)]
        await owner.close()
        await process.wait()
        assert all(not p.is_running() for p in identities)
    asyncio.run(run())


def test_cancel_during_count_never_dispatches(monkeypatch):
    p, calls = provider(monkeypatch)
    cleaned = []
    async def counter(*args):
        try: await asyncio.sleep(30)
        finally: cleaned.append(True)
    monkeypatch.setattr(exact, 'count_request', counter)
    async def run():
        task = asyncio.create_task(p.chat('fixture', [{'role': 'user', 'content': 'x'}], TaskLimits()))
        await asyncio.sleep(.01)
        task.cancel()
        with pytest.raises(asyncio.CancelledError) as error: await task
        assert error.value.termination_confirmed
    asyncio.run(run())
    assert cleaned and not calls
