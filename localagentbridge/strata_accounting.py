"""Opt-in, supervisor-bound admission for the pinned Strata text/tool profile.

Counts are preflight evidence, never provider usage or runtime qualification.
The helper is a short-lived Python process: no resident tokenizer/prompt cache,
no dependencies added to LAB, and no engine, network or model-file access.
"""
import asyncio
import hashlib
import json
import os
from pathlib import Path
import re

from .task_contract import digest

UPSTREAM = '7695859aa13afb248bdb4d36f9b2e95707db079d'
PATCH = '3a0ca878f80c66e26c26b429e00db71ccb3c9febcc34056728602ee996d05190'
SERVER = '670a36ec733fadfd0880035180e1345483ea21576a90b3501b807d68209d39f0'
TEMPLATE = '12827f24b742ea4e80cdc12dbcf9622227056b9f797252a3149263d4f9aaadce'
MAX_REQUEST_BYTES = 1_000_000  # Existing SDK mailbox bound, independently retained.
MODE = 'strata_pinned_exact_v1'


class CounterContainment:
    """Contain the Windows venv redirector AND its actual Python child."""
    def __init__(self):
        self.job = None
        self.flags = 0
        if os.name == 'nt':
            import win32api
            import win32job
            self.api, self.jobs = win32api, win32job
            self.job = win32job.CreateJobObject(None, '')
            info = win32job.QueryInformationJobObject(self.job, win32job.JobObjectExtendedLimitInformation)
            info['BasicLimitInformation']['LimitFlags'] = win32job.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
            win32job.SetInformationJobObject(self.job, win32job.JobObjectExtendedLimitInformation, info)
            self.flags = 0x08000000 | 0x00000004  # hidden, suspended until assigned

    def attach(self, pid):
        if self.job is None:
            return
        import psutil
        import win32process
        handle = self.api.OpenProcess(0x0100 | 0x0001, False, pid)
        try:
            self.jobs.AssignProcessToJobObject(self.job, handle)
            for thread in psutil.Process(pid).threads():
                h = self.api.OpenThread(0x0002, False, thread.id)
                try: win32process.ResumeThread(h)
                finally: self.api.CloseHandle(h)
        finally:
            self.api.CloseHandle(handle)

    async def close(self):
        if self.job is None:
            return
        try:
            self.jobs.TerminateJobObject(self.job, 1)
            for _ in range(100):
                info = self.jobs.QueryInformationJobObject(self.job, self.jobs.JobObjectBasicAccountingInformation)
                if info['ActiveProcesses'] == 0:
                    return
                await asyncio.sleep(.05)
            raise ValueError('Counter process cleanup remains unconfirmed')
        finally:
            self.api.CloseHandle(self.job)
            self.job = None


def validate_selection(value):
    if (not isinstance(value, dict) or set(value) != {'mode', 'manifest_path', 'manifest_sha256'}
            or value['mode'] != MODE or not Path(value['manifest_path']).is_absolute()
            or not re.fullmatch('[0-9a-f]{64}', value['manifest_sha256'])):
        raise ValueError('Exact accounting requires a trusted local manifest and hash')


def read_manifest(selection):
    validate_selection(selection)
    raw = Path(selection['manifest_path']).read_bytes()
    if len(raw) > 1_000_000 or hashlib.sha256(raw).hexdigest() != selection['manifest_sha256']:
        raise ValueError('Exact accounting manifest changed')
    m = json.loads(raw)
    if (m['mode'] != MODE or m['upstream_commit'] != UPSTREAM or m['patch_sha256'] != PATCH
            or m['server_sha256'] != SERVER or m['template_sha256'] != TEMPLATE
            or m['capabilities'] != ['text', 'tools', 'nonstreaming']):
        raise ValueError('Unsupported exact accounting provenance/capabilities')
    if (m['files'][str((Path(m['source'])/'serve/server.py').resolve())] != SERVER
            or m['files'][str((Path(m['tokenizer'])/'chat_template.jinja').resolve())] != TEMPLATE
            or m['dependencies'] != {'Jinja2': '3.1.6', 'regex': '2026.9.10', 'MarkupSafe': '3.0.3'}):
        raise ValueError('Pinned prompt preparation assets/dependencies differ')
    return m


def validate_payload(p):
    if (set(p) - {'model', 'messages', 'max_tokens', 'stream', 'temperature',
                  'chat_template_kwargs', 'strata_mcp', 'tools', 'tool_choice', 'reasoning_effort'}
            or p.get('stream') is not False or p.get('strata_mcp') is not False
            or p.get('tool_choice', 'auto') != 'auto'
            or set(p.get('chat_template_kwargs', {})) != {'enable_thinking'}
            or type(p['chat_template_kwargs']['enable_thinking']) is not bool):
        raise ValueError('Unsupported exact accounting request feature')
    for message in p['messages']:
        if (set(message) - {'role', 'content', 'reasoning_content', 'tool_calls', 'tool_call_id'}
                or message['role'] not in ('system', 'user', 'assistant', 'tool')
                or (message.get('content') is not None and not isinstance(message['content'], str))):
            raise ValueError('Unsupported exact accounting message feature')
        if 'reasoning_content' in message and not isinstance(message['reasoning_content'], str):
            raise ValueError('Unsupported reasoning content')
        for call in message.get('tool_calls', []):
            if (set(call) != {'id', 'type', 'function'} or call['type'] != 'function'
                    or set(call['function']) != {'name', 'arguments'}):
                raise ValueError('Unsupported exact accounting tool call')
    for tool in p.get('tools', []):
        if (set(tool) != {'type', 'function'} or tool['type'] != 'function'
                or set(tool['function']) - {'name', 'description', 'parameters'}):
            raise ValueError('Unsupported exact accounting tool definition')


def verify_scope(m, settings, payload, observed):
    profile = settings.get('_accounting_profile', {})
    binding = settings.get('binding', {})
    request_settings = {k:v for k,v in payload.items() if k not in ('messages', 'tools')}
    # With no tools, omitted tool_choice and "auto" prepare the same prompt.
    # Tools/messages themselves remain covered by the full request hash.
    request_settings.setdefault('tool_choice', 'auto')
    if (profile != {'model': m['model'], 'identity': m['profile_identity']}
            or payload['model'] != m['model'] or binding.get('identity') != m['profile_identity']
            or observed.get('identity') != m['profile_identity'] or not observed.get('identity_verified')
            or observed.get('template_sha256') != m['template_sha256']
            or binding.get('source_commit') != m['upstream_commit']
            or binding.get('config_sha256') != m['config_sha256']
            or digest(request_settings) != m['request_settings_sha256']):
        raise ValueError('Exact accounting profile/runtime/settings identity mismatch')
    for name in ('config_path', 'config_sha256'):
        if binding.get(name) != m[name]:
            raise ValueError('Exact accounting serving configuration mismatch')
    # The live binding verifier independently covers engine/weights/PIDs. These
    # artifacts must be the SAME prompt assets used by that verified runtime.
    bound = {str(Path(a['path']).resolve()): a['sha256'] for a in binding.get('artifacts', [])}
    for name in ('serve/server.py', 'serve/frontend.py', 'tools/strata_tokenizer.py'):
        path = str((Path(m['source']) / name).resolve())
        if bound.get(path) != m['files'][path]:
            raise ValueError('Counter source is not bound to the serving runtime')
    for name in ('vocab.json', 'merges.txt', 'token_type.json', 'chat_template.jinja'):
        path = str((Path(m['tokenizer']) / name).resolve())
        if bound.get(path) != m['files'][path]:
            raise ValueError('Counter tokenizer is not bound to the serving runtime')


async def count_request(selection, settings, payload, observed):
    """Never accepts a caller count. The verified helper counts the frozen payload."""
    validate_payload(payload)
    m = read_manifest(selection)
    verify_scope(m, settings, payload, observed)
    python = Path(m['python']).resolve(strict=True)
    if hashlib.sha256(python.read_bytes()).hexdigest() != m['python_sha256']:
        raise ValueError('Counter interpreter changed')
    body = json.dumps({'manifest': m, 'payload': payload}, ensure_ascii=False).encode()
    owner = CounterContainment()
    process = None
    try:
        process = await asyncio.create_subprocess_exec(str(python), '-I', '-B',
            str(Path(__file__).with_name('strata_count_worker.py')),
            stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
            limit=65536, creationflags=owner.flags)
        owner.attach(process.pid)
        async with asyncio.timeout(30):
            out, err = await process.communicate(body)
        if process.returncode or len(out) > 65536:
            raise ValueError('Pinned model-free counting failed (no generation dispatched)')
        result = json.loads(out)
        if (result.get('request_sha256') != digest(payload)
                or type(result.get('input_tokens')) is not int or result['input_tokens'] < 0
                or result.get('server_context_reserve') != 8):
            raise ValueError('Invalid or stale counting evidence')
        if read_manifest(selection) != m:
            raise ValueError('Counting identity changed during admission')
        return result | {'manifest_sha256': selection['manifest_sha256'],
                         'profile_identity': m['profile_identity'], 'upstream_commit': UPSTREAM,
                         'patch_sha256': PATCH, 'server_sha256': SERVER,
                         'template_sha256': TEMPLATE, 'dependencies': m['dependencies'],
                         'request_settings_sha256': m['request_settings_sha256'],
                         'counter_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                         'helper_sha256': hashlib.sha256(Path(__file__).with_name('strata_count_worker.py').read_bytes()).hexdigest()}
    finally:
        try:
            await owner.close()
        finally:
            if process is not None:
                if process.returncode is None:
                    process.kill()  # Unassigned suspended process, or POSIX helper.
                await process.wait()


def exact_accounting(base, evidence, limits, observed):
    if (evidence.get('request_sha256') != base['request_sha256']
            or type(evidence.get('input_tokens')) is not int or evidence['input_tokens'] < 0
            or evidence.get('server_context_reserve') != 8):
        raise ValueError('Unbound or stale counting evidence')
    context = min(limits.context_tokens, observed['context_tokens'],
                  observed.get('effective_context_tokens') or observed['context_tokens'], 16384)
    required = evidence['input_tokens'] + limits.output_tokens + limits.context_safety_tokens + 8
    return base | {'method': MODE, 'exact_tokenizer': True, 'input_token_upper_bound': None,
        'preflight_input_tokens': evidence['input_tokens'], 'server_context_reserve': 8,
        'required_capacity_bound': required, 'effective_context_tokens': context,
        'admitted': required <= context,
        'classification': 'admitted' if required <= context else 'exact_context_admission_rejection',
        'counting_evidence': evidence}
