"""Optional bounded Chat Completions transport. No runtime tools, loading or fallback."""
import asyncio
import hashlib
import ipaddress
import json
import os
from pathlib import Path
from urllib.parse import urlsplit

import httpx


class ProviderError(ValueError):
    pass


def context_accounting(payload, limits):
    """Conservative fallback bound, never advertised as an actual tokenizer count.

    Retain the prior full UTF-8 JSON byte allowance (including serialization),
    reserve output separately, and add the explicitly requested safety margin.
    Actual template/token counts are provider observations after dispatch.
    """
    size = lambda value: len(json.dumps(value, ensure_ascii=False).encode())
    by_role = {}
    for message in payload.get('messages', []):
        role = message.get('role', 'unknown')
        by_role[role] = by_role.get(role, 0) + size(message)
    total = size(payload)
    required = total + limits.output_tokens + limits.context_safety_tokens
    return {'method': 'serialized_utf8_byte_upper_bound', 'exact_tokenizer': False,
        'serialized_bytes': total, 'message_bytes_by_role': by_role,
        'tool_definition_bytes': size(payload.get('tools', [])),
        'message_count': len(payload.get('messages', [])),
        'input_token_upper_bound': total, 'reserved_output_tokens': limits.output_tokens,
        'safety_tokens': limits.context_safety_tokens, 'required_capacity_bound': required,
        'effective_context_tokens': limits.context_tokens, 'admitted': required <= limits.context_tokens,
        'classification': 'admitted' if required <= limits.context_tokens else 'conservative_admission_rejection',
        'history_compacted': False, 'actual_input_tokens': None}


def local_origin(value):
    url = urlsplit(value)
    if (url.scheme not in ('http', 'https') or url.username or url.password or url.query or url.fragment
            or url.path not in ('', '/') or not url.hostname):
        raise ProviderError('Provider must be a loopback HTTP origin')
    host = '127.0.0.1' if url.hostname.lower() == 'localhost' else url.hostname
    try:
        if not ipaddress.ip_address(host).is_loopback:
            raise ValueError()
    except ValueError:
        raise ProviderError('Only loopback providers are supported; use the isolated mailbox, not a public listener') from None
    host = '[' + host + ']' if ':' in host else host
    return f'{url.scheme}://{host}:{url.port or (443 if url.scheme == "https" else 80)}'


def counter(value):
    return value if type(value) is int and value >= 0 else None


def validate_completion(raw, *, tools=(), max_bytes=65536):
    if not isinstance(raw, dict) or len(json.dumps(raw).encode()) > max_bytes:
        raise ProviderError('Malformed or oversized completion')
    choices = raw.get('choices')
    if not isinstance(choices, list) or len(choices) != 1 or not isinstance(choices[0], dict):
        raise ProviderError('Expected exactly one completion')
    choice = choices[0]
    msg = choice.get('message')
    if not isinstance(msg, dict) or choice.get('finish_reason') not in ('stop', 'tool_calls'):
        raise ProviderError('Incomplete, overflowed or malformed completion')
    text, reasoning = msg.get('content') or '', msg.get('reasoning_content', msg.get('reasoning')) or ''
    if not isinstance(text, str) or not isinstance(reasoning, str):
        raise ProviderError('Non-text content/reasoning')
    calls = msg.get('tool_calls') or []
    if not isinstance(calls, list) or len(calls) > 16:
        raise ProviderError('Malformed tool calls')
    allowed = {t['function']['name'] for t in tools}
    ids = set()
    for call in calls:
        if not isinstance(call, dict) or call.get('type') != 'function' or not isinstance(call.get('id'), str) or not call['id']:
            raise ProviderError('Malformed tool call')
        fn = call.get('function', {})
        if not isinstance(fn, dict) or call['id'] in ids or fn.get('name') not in allowed or not isinstance(fn.get('arguments'), str):
            raise ProviderError('Unknown/duplicate tool or invalid arguments')
        ids.add(call['id'])
        try:
            args = json.loads(fn['arguments'])
        except (ValueError, TypeError):
            raise ProviderError('Invalid tool arguments JSON') from None
        if not isinstance(args, dict):
            raise ProviderError('Tool arguments must be an object')
    if bool(calls) != (choice['finish_reason'] == 'tool_calls') or not (text.strip() or calls):
        raise ProviderError('Empty or inconsistent completion')
    usage = raw.get('usage') or {}
    if not isinstance(usage, dict) or not isinstance(usage.get('prompt_tokens_details') or {}, dict):
        raise ProviderError('Malformed usage counters')
    return dict(content=text, reasoning=reasoning, tool_calls=calls,
                usage={'input_tokens': counter(usage.get('prompt_tokens')),
                       'output_tokens': counter(usage.get('completion_tokens')),
                       'cached_input_tokens': counter((usage.get('prompt_tokens_details') or {}).get('cached_tokens'))},
                raw=raw)


class ChatProvider:
    def __init__(self, backend, settings, transport=None):
        if backend not in ('ollama', 'strata'):
            raise ProviderError('Unknown backend')
        self.backend, self.settings, self.transport = backend, settings, transport
        if not settings.get('enabled', backend == 'ollama'):
            raise ProviderError('Provider is disabled')
        self.origin = local_origin(settings['endpoint'])

    def client(self, deadline=15):
        # None means no inference wall-clock/read timeout, not disabled connect timeout.
        key_env = self.settings.get('api_key_env')
        if key_env and not os.getenv(key_env):
            raise ProviderError('Configured provider API key environment variable is missing')
        headers = {'Authorization': 'Bearer ' + os.environ[key_env]} if key_env else {}
        return httpx.AsyncClient(headers=headers, transport=self.transport, trust_env=False, follow_redirects=False,
                                 timeout=httpx.Timeout(deadline, connect=5))

    async def inspect(self, model):
        async with self.client() as client:
            if self.backend == 'ollama':
                tags = await client.get(self.origin + '/api/tags')
                tags.raise_for_status()
                inventory = tags.json()
                rows = inventory.get('models') if isinstance(inventory, dict) else None
                if not isinstance(rows, list) or not all(isinstance(r, dict) for r in rows):
                    raise ProviderError('Malformed Ollama inventory')
                row = next((r for r in rows if r.get('name') == model), None)
                if not row:
                    raise ProviderError('Exact Ollama model is missing')
                show = await client.post(self.origin + '/api/show', json={'model': model})
                show.raise_for_status()
                data = show.json()
                if not isinstance(data, dict) or not isinstance(data.get('model_info', {}), dict):
                    raise ProviderError('Malformed Ollama model metadata')
                binding = self.settings.get('runtime_binding')
                if binding:
                    from .runtime_profile import template_identity
                    version = await client.get(self.origin + '/api/version')
                    version.raise_for_status()
                    if (row.get('digest') != binding.get('identity') or
                            data.get('details',{}).get('quantization_level') != binding.get('quantization') or
                            template_identity(data.get('template','')) != binding.get('template_sha256') or
                            version.json().get('version') != binding.get('backend_version')):
                        raise ProviderError('Qualified model/backend/template identity changed')
                from .selection import remote_model
                if remote_model(row, data) or model.lower().endswith(':cloud'):
                    raise ProviderError('Cloud weights are forbidden')
                caps = data.get('capabilities', [])
                lengths = [v for k, v in data.get('model_info', {}).items()
                           if k.endswith('.context_length') and type(v) is int]
                return dict(ready='completion' in caps, identity=row.get('digest'),
                            identity_verified=bool(row.get('digest')), context_tokens=max(lengths, default=0),
                            tools_advertised='tools' in caps, cancellation='disconnect_unconfirmed',
                            protocol='chat_completions', usage='optional', model=model, backend=self.backend)
            health = await client.get(self.origin + '/health')
            health.raise_for_status()
            health = health.json()
            if not isinstance(health, dict) or health.get('service') != 'strata':
                raise ProviderError('Not the supported Strata health protocol')
            listing = await client.get(self.origin + '/v1/models')
            listing.raise_for_status()
            inventory = listing.json()
            rows = inventory.get('data') if isinstance(inventory, dict) else None
            if not isinstance(rows, list) or not all(isinstance(r, dict) for r in rows):
                raise ProviderError('Malformed Strata inventory')
            row = next((r for r in rows if r.get('id') == model), None)
            if not row:
                raise ProviderError('Requested Strata model/alias is not listed; no substitution')
            props = await client.get(self.origin + '/props')
            props.raise_for_status()
            props = props.json()
            if not isinstance(props, dict) or not isinstance(props.get('chat_template_caps', {}), dict):
                raise ProviderError('Malformed Strata serving metadata')
            binding = self.settings.get('binding', {})
            verified = self.verify_binding(binding, health, props)
            ctx = health.get('max_context')
            if type(ctx) is not int or ctx < 1:
                raise ProviderError('Strata context capacity unavailable')
            return dict(ready=health.get('loaded') is True, identity=binding.get('identity') if verified else None,
                        identity_verified=verified, identity_uncertainty=None if verified else 'Names/aliases do not identify weights; verified local serving binding required',
                        context_tokens=ctx, tools_advertised=bool(props.get('chat_template_caps', {}).get('supports_tool_calls')),
                        cancellation='disconnect_unconfirmed', protocol='chat_completions',
                        usage='optional', model=model, backend=self.backend, serving_model=health.get('model'))

    def verify_binding(self, binding, health, props):
        # Operator-provided binding is trusted controller configuration, never a request/model field.
        # Hash config/artifacts and compare the observed model path/build on every admission.
        if not binding or binding.get('family') != 'coder':
            return False
        required = ('identity', 'config_path', 'config_sha256', 'model_path', 'build_info', 'artifacts', 'process')
        if any(not binding.get(k) for k in required):
            return False
        if props.get('model_path') != binding['model_path'] or props.get('build_info') != binding['build_info']:
            return False
        from .process_control import alive
        import psutil
        process = binding['process']
        if not alive(process):
            return False
        running = psutil.Process(process['pid'])
        config_path = str(Path(binding['config_path']).resolve())
        if config_path not in [str(Path(arg).resolve()) for arg in running.cmdline() if arg.endswith('.json')]:
            return False
        listeners = [c for c in running.net_connections(kind='tcp') if c.status == psutil.CONN_LISTEN
                     and c.laddr.port == urlsplit(self.origin).port]
        if not listeners or any(not ipaddress.ip_address(c.laddr.ip).is_loopback for c in listeners):
            return False
        config_bytes = Path(binding['config_path']).read_bytes()
        if hashlib.sha256(config_bytes).hexdigest() != binding['config_sha256']:
            return False
        cfg = json.loads(config_bytes)
        host = str(cfg.get('host', '127.0.0.1'))
        if ':' in host and not host.startswith('['):
            host = '['+host+']'
        local_origin('http://' + host + ':' + str(urlsplit(self.origin).port))
        args = cfg.get('args', [])
        if (cfg.get('model_name') != health.get('model') or cfg.get('mcp_servers') or
                cfg.get('mcp') or cfg.get('api_monitor') or binding['model_path'] not in args):
            return False
        # Artifact hashes must have been independently checked by the operator, not inferred
        # from response model names. Recheck on-disk sizes/mtime against that signed-off record.
        for artifact in binding['artifacts']:
            path = Path(artifact['path'])
            stat = path.stat()
            if stat.st_size != artifact['size'] or stat.st_mtime_ns != artifact['mtime_ns']:
                return False
            if not artifact.get('sha256') or not artifact.get('verified_by_supervisor'):
                return False
        from .task_contract import digest
        expected = digest({'config_sha256': binding['config_sha256'],
                           'artifacts': [{k: a[k] for k in ('path', 'size', 'sha256')} for a in binding['artifacts']]})
        return binding['identity'] == expected

    async def chat(self, model, messages, limits, *, tools=(), stream=False):
        for attempt in range(limits.transport_retries + 1):
            try:
                return await self._chat(model, messages, limits, tools=tools, stream=stream)
            except httpx.ConnectError:
                if attempt >= limits.transport_retries:
                    raise
                await asyncio.sleep(.1)
        raise ProviderError('Transport retry budget exhausted')

    async def _chat(self, model, messages, limits, *, tools=(), stream=False):
        self.last_usage = None
        if self.backend == 'ollama':
            messages = json.loads(json.dumps(messages))
            for message in messages:
                if 'reasoning_content' in message:
                    reasoning = message.pop('reasoning_content')
                    if not isinstance(reasoning, str) or ('reasoning' in message and message['reasoning'] != reasoning):
                        raise ProviderError('Conflicting reasoning context')
                    message['reasoning'] = reasoning
        payload = dict(model=model, messages=messages, max_tokens=limits.output_tokens,
                       stream=stream, temperature=self.settings.get('temperature', 0))
        if self.settings.get('reasoning_effort') is not None:
            payload['reasoning_effort'] = self.settings['reasoning_effort']
        if tools:
            payload['tools'] = list(tools)
            payload['tool_choice'] = 'auto'
        native = self.backend == 'ollama' and self.settings.get('native_context', False)
        if native:
            # Ollama's OpenAI endpoint lacks per-request num_ctx. The native
            # endpoint allows a scoped budget on the existing service. SDK still
            # consumes standard Chat Completions at its isolated mailbox.
            converted = json.loads(json.dumps(messages))
            for message in converted:
                content = message.get('content')
                if isinstance(content, list):
                    if any(not isinstance(part, dict) or part.get('type') != 'text' or not isinstance(part.get('text'), str) for part in content):
                        raise ProviderError('Only SDK text content blocks are qualified for native Ollama')
                    message['content'] = '\n'.join(part['text'] for part in content)
                elif content is None:
                    message['content'] = ''
                elif not isinstance(content, str):
                    raise ProviderError('Invalid SDK content for native Ollama')
                if 'reasoning' in message:
                    message['thinking'] = message.pop('reasoning')
                for call in message.get('tool_calls', []):
                    arguments = call['function']['arguments']
                    if isinstance(arguments, str):
                        call['function']['arguments'] = json.loads(arguments)
            payload = {'model': model, 'messages': converted, 'stream': False,
                'think': False, 'options': {'num_ctx': limits.context_tokens,
                    'num_predict': limits.output_tokens, 'temperature': self.settings.get('temperature', 0)}}
            if 'num_gpu' in self.settings:
                payload['options']['num_gpu'] = self.settings['num_gpu']
            if 'draft_num_predict' in self.settings:
                payload['options']['draft_num_predict'] = self.settings['draft_num_predict']
            if 'keep_alive_seconds' in self.settings:
                payload['keep_alive'] = self.settings['keep_alive_seconds']
            if self.settings.get('strict_context'):
                payload.update(truncate=False, shift=False)
            if tools:
                payload['tools'] = list(tools)
            if stream:
                raise ProviderError('Native scoped context currently requires non-streaming')
        if self.settings.get('runtime_binding'):
            if not native or payload['think'] is not False:
                raise ProviderError('Qualified profile requires native non-thinking transport')
            binding = self.settings['runtime_binding']
            if limits.output_tokens > binding['maximum_output_tokens']:
                raise ProviderError('Output allowance exceeds the qualified profile')
            await self.inspect(model)
        self.last_effective_request = payload
        # Strata's MCP execution is never requested. OpenHands owns tool execution.
        accounting = context_accounting(payload, limits)
        self.last_accounting = accounting
        if not accounting['admitted']:
            error = ProviderError('Conservative whole-prompt context admission failed')
            error.context_accounting = accounting
            error.termination_confirmed = True  # No generation dispatched for this request.
            raise error
        async with self.client(limits.inference_deadline_seconds) as client:
            if not stream:
                async with client.stream('POST', self.origin + ('/api/chat' if native else '/v1/chat/completions'), json=payload) as response:
                    if native and response.is_error:
                        detail = bytearray()
                        async for chunk in response.aiter_bytes():
                            detail.extend(chunk[:4096-len(detail)])
                            if len(detail) >= 4096:
                                break
                        error = ProviderError('Provider HTTP ' + str(response.status_code) + ': ' + detail.decode(errors='replace'))
                        error.termination_confirmed = response.status_code in (400, 404, 413, 422)
                        raise error
                    response.raise_for_status()
                    raw = bytearray()
                    async for chunk in response.aiter_bytes():
                        raw.extend(chunk)
                        if len(raw) > limits.output_bytes:
                            raise ProviderError('Output byte budget exceeded')
                try:
                    result = json.loads(raw)
                except ValueError:
                    raise ProviderError('Malformed completion JSON') from None
            else:
                # Streaming is useful for advisory text. Agent tool exchanges use non-streaming.
                if tools:
                    raise ProviderError('Streaming tool calls are not qualified; use non-streaming')
                parts, reasoning, finish, usage, count, done = [], [], None, None, 0, False
                async with client.stream('POST', self.origin + '/v1/chat/completions', json=payload) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        count += len(line.encode())
                        if count > limits.output_bytes:
                            raise ProviderError('Output byte budget exceeded')
                        if not line or line.startswith(':'):
                            continue
                        if not line.startswith('data:'):
                            continue
                        value = line[5:].strip()
                        if value == '[DONE]':
                            done = True
                            break
                        try:
                            event = json.loads(value)
                            if not isinstance(event, dict):
                                raise ProviderError('Invalid streaming event')
                            if 'error' in event:
                                raise ProviderError('Provider streaming error')
                            usage = event.get('usage') or usage
                            choices = event.get('choices', [])
                            if not choices:
                                continue
                            if not isinstance(choices, list) or len(choices) != 1 or not isinstance(choices[0], dict):
                                raise ProviderError('Invalid stream choices')
                            choice = choices[0]
                            delta = choice.get('delta', {})
                            if not isinstance(delta, dict):
                                raise ProviderError('Invalid stream delta')
                            if delta.get('tool_calls'):
                                raise ProviderError('Unexpected advisory tool call')
                            for key, dest in (('content', parts), ('reasoning_content', reasoning)):
                                value = delta.get(key) or ''
                                if not isinstance(value, str):
                                    raise ProviderError('Malformed stream text')
                                dest.append(value)
                            finish = choice.get('finish_reason') or finish
                        except (ValueError, TypeError, KeyError) as error:
                            raise ProviderError('Malformed completion stream: ' + str(error)) from None
                if not done:
                    raise ProviderError('Stream disconnected before completion')
                result = {'choices': [{'message': {'content': ''.join(parts),
                    'reasoning_content': ''.join(reasoning)}, 'finish_reason': finish}], 'usage': usage}
        if isinstance(result, dict):
            u = result if native else result.get('usage') or {}
            self.last_usage = {'input_tokens':counter(u.get('prompt_eval_count' if native else 'prompt_tokens')),
                               'output_tokens':counter(u.get('eval_count' if native else 'completion_tokens')),
                               'cached_input_tokens':None}
        provider_timing = {k: result.get(k) for k in ('total_duration', 'load_duration', 'prompt_eval_duration', 'eval_duration')} if native and isinstance(result, dict) else None
        if native:
            if not isinstance(result, dict) or result.get('done') is not True or not isinstance(result.get('message'), dict):
                raise ProviderError('Malformed or incomplete native Ollama completion')
            message = result['message']
            calls = message.get('tool_calls') or []
            if not isinstance(calls, list):
                raise ProviderError('Malformed native tool calls')
            for index, call in enumerate(calls):
                if not isinstance(call, dict) or not isinstance(call.get('function'), dict) or not isinstance(call['function'].get('arguments'), dict):
                    raise ProviderError('Malformed native tool arguments')
                call['id'] = 'call_' + hashlib.sha256(json.dumps(result, sort_keys=True).encode()).hexdigest()[:20] + '_' + str(index)
                call['type'] = 'function'
                call['function']['arguments'] = json.dumps(call['function']['arguments'])
            if 'thinking' in message:
                message['reasoning_content'] = message.pop('thinking')
            reason = result.get('done_reason')
            result = {'id': 'chatcmpl-local', 'object': 'chat.completion', 'created': 0, 'model': model,
                'choices': [{'index': 0, 'message': message, 'finish_reason': 'tool_calls' if calls and reason == 'stop' else reason}],
                'usage': {'prompt_tokens': result.get('prompt_eval_count'), 'completion_tokens': result.get('eval_count')}}
        try:
            answer = validate_completion(result, tools=tools, max_bytes=limits.output_bytes)
            answer['context_accounting'] = accounting | {'actual_input_tokens': answer['usage']['input_tokens']}
            answer['provider_timing_ns'] = provider_timing
            if self.backend == 'ollama' and self.settings.get('verify_loaded_context'):
                # Inspect after the completed inference, before forwarding any tool
                # call to the SDK. Advertised maximum context is not loaded context.
                async with self.client(5) as inspector:
                    response = await inspector.get(self.origin + '/api/ps')
                    response.raise_for_status()
                    rows = response.json().get('models', [])
                matches = [r for r in rows if r.get('name') == model]
                if len(matches) != 1 or matches[0].get('context_length') != limits.context_tokens:
                    raise ProviderError('Effective loaded context differs from the approved contract')
                answer['loaded_context_tokens'] = matches[0]['context_length']
                binding = self.settings.get('runtime_binding')
                if binding:
                    if matches[0].get('digest') != binding['identity']:
                        raise ProviderError('Loaded model digest differs from qualified identity')
                    loaded_vram = counter(matches[0].get('size_vram'))
                    if self.settings.get('num_gpu', 0) > 0 and not loaded_vram:
                        raise ProviderError('Qualified GPU profile has no verified loaded VRAM; CPU fallback forbidden')
                    from .runtime_profile import runner_evidence
                    try:
                        runner = runner_evidence(binding, limits)
                    except ValueError as failure:
                        raise ProviderError(str(failure)) from failure
                    answer['effective_runtime'] = {'backend':self.backend,
                        'backend_version':binding['backend_version'],'identity':binding['identity'],
                        'template_sha256':binding['template_sha256'],'runner':runner,'loaded_vram_bytes':loaded_vram,
                        'request_options':payload['options'],'think':payload['think'],
                        'truncate':payload.get('truncate'),'shift':payload.get('shift'),
                        'keep_alive':payload.get('keep_alive')}
                    if answer['usage']['output_tokens'] is not None and answer['usage']['output_tokens'] > limits.output_tokens:
                        raise ProviderError('Provider exceeded response output limit')
            return answer
        except ProviderError as error:
            error.termination_confirmed = True  # Complete HTTP response, including length stop.
            raise
