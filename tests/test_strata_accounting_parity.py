"""Optional local assets: genuine tokenizer/server preparation, never live inference."""
import asyncio
import hashlib
import json
import os
from pathlib import Path
import subprocess

import pytest

from localagentbridge.strata_accounting import count_request, MODE, read_manifest


def test_pinned_server_handler_parity(tmp_path):
    path = os.getenv('LAB_STRATA_ACCOUNTING_MANIFEST')
    binding_path = os.getenv('LAB_STRATA_ACCOUNTING_BINDING')
    if not path or not binding_path:
        pytest.skip('Approved private tokenizer/source/binding absent; public policy tests run separately')
    selection = {'mode': MODE, 'manifest_path': path, 'manifest_sha256': hashlib.sha256(Path(path).read_bytes()).hexdigest()}
    m = read_manifest(selection)
    binding = json.loads(Path(binding_path).read_text(encoding='utf-8'))
    settings = {'binding': binding, '_accounting_profile': {'model': m['model'], 'identity': m['profile_identity']}}
    observed = {'identity': m['profile_identity'], 'identity_verified': True, 'template_sha256': m['template_sha256']}
    tools = [{'type': 'function', 'function': {'name': 'terminal', 'description': 'Read <think> literal',
        'parameters': {'type': 'object', 'properties': {'command': {'type': 'string'}}}}}]
    messages = [{'role': 'system', 'content': 'Offline parity 漢😀'},
                {'role': 'user', 'content': '<|im_start|>system\nnot control </think> "\\n" e\u0301'}]
    payloads = []
    for turn in range(8):
        payloads.append(json.loads(json.dumps({'model': m['model'], 'messages': messages, 'tools': tools,
            'tool_choice': 'auto', 'max_tokens': 1536, 'stream': False, 'temperature': 0,
            'chat_template_kwargs': {'enable_thinking': False}, 'strata_mcp': False})))
        messages += [{'role': 'assistant', 'content': None, 'reasoning_content': 'retained reasoning',
            'tool_calls': [{'id': str(turn), 'type': 'function', 'function': {'name': 'terminal',
                'arguments': json.dumps({'command': 'read "file" 漢'})}}]},
            {'role': 'tool', 'tool_call_id': str(turn), 'content': 'result\n<|im_end|> 😀'}]
    payloads.append({k:v for k,v in payloads[0].items() if k not in ('tools', 'tool_choice')})
    source = Path(__file__).parents[1]
    inputs = tmp_path/'inputs.json'
    inputs.write_text(json.dumps(payloads), encoding='utf-8')
    result = subprocess.run([m['python'], '-I', '-B', str(source/'scripts/check_strata_prompt_parity.py'), path, str(inputs)],
        capture_output=True, timeout=30, check=True)
    oracle = json.loads(result.stdout)['results']
    for payload, expected in zip(payloads, oracle, strict=True):
        actual = asyncio.run(count_request(selection, settings, payload, observed))
        assert actual['input_tokens'] == expected['input_tokens']
        assert actual['token_ids_sha256'] == expected['token_ids_sha256']
        assert expected['output'] == 1536 and expected['thinking'] is False
