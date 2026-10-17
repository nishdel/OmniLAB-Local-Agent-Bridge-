"""Isolated model-free helper; executed by a supervisor-pinned Python, not as a server.

No third-party source is shipped. Import the locally approved Strata modules only
after hashing them. Audit guards forbid network, child processes, file writes and
reads outside the approved code/tokenizer/stdlib set. Never construct an Engine.
"""
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import sys
import time
from types import SimpleNamespace


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def main():
    start = time.perf_counter()
    data = json.loads(sys.stdin.buffer.read(2_100_001))
    m, payload = data['manifest'], data['payload']
    files = {str(Path(p).resolve()): h for p, h in m['files'].items()}
    def verify():
        for p, h in files.items():
            if Path(p).suffix.lower() in ('.gguf', '.bin', '.safetensors') or Path(p).stat().st_size > 64*1024*1024:
                raise ValueError('Model weights/oversized assets cannot be counting inputs')
            if hashlib.sha256(Path(p).read_bytes()).hexdigest() != h:
                raise ValueError('Counting asset changed')
    verify()
    source, tok_dir = Path(m['source']).resolve(), Path(m['tokenizer']).resolve()
    # All source imports and installed dependency files are explicitly hashed;
    # unlisted files cannot be read, even if placed beside an approved module.
    stdlib = Path(sys.base_prefix).resolve()
    def guard(event, args):
        if event.startswith(('socket.', 'subprocess.', 'os.spawn', 'os.exec')) or event in (
                'os.system', 'os.startfile', 'os.remove', 'os.rename', 'os.mkdir'):
            raise RuntimeError('Model-free counter forbids process/network/write activity')
        if event == 'open' and isinstance(args[0], (str, bytes, os.PathLike)):
            path = Path(os.fsdecode(args[0])).resolve()
            if path.suffix == '.pyc':
                raise FileNotFoundError('Counter imports verified source, never cached bytecode')
            mode, flags = args[1], args[2]
            if (isinstance(mode, str) and any(c in mode for c in 'wax+')) or flags & (os.O_WRONLY | os.O_RDWR):
                raise RuntimeError('Model-free counter forbids writes')
            if str(path) not in files and not (path.is_relative_to(stdlib) and 'site-packages' not in path.parts):
                raise RuntimeError('Unapproved counter read')
    sys.addaudithook(guard)
    for package, version in m['dependencies'].items():
        if importlib.metadata.version(package) != version:
            raise ValueError('Counter dependency changed')
    sys.path.insert(0, str(source))
    sys.path.insert(0, str(source / 'tools'))
    from serve.server import Service, CTX_SLACK
    from serve.frontend import ChatTemplate, openai_to_messages, forced_call
    import strata_tokenizer
    vocab = json.loads((tok_dir / 'vocab.json').read_text(encoding='utf-8'))
    tokens = [None] * len(vocab)
    for token, index in vocab.items():
        tokens[index] = token
    tokenizer = strata_tokenizer.Tokenizer(tokens,
        (tok_dir / 'merges.txt').read_text(encoding='utf-8').split('\n'),
        json.loads((tok_dir / 'token_type.json').read_text(encoding='utf-8')))
    svc = Service(SimpleNamespace(max_context=16384), tokenizer, ChatTemplate(tok_dir / 'chat_template.jinja'))
    config = json.loads(Path(m['config_path']).read_text(encoding='utf-8-sig'))
    if hashlib.sha256(Path(m['config_path']).read_bytes()).hexdigest() != m['config_sha256']:
        raise ValueError('Serving configuration changed')
    if any(config.get(k) for k in ('effort_position', 'reasoning_effort', 'vision', 'mcp_servers', 'fit_max_tokens',
                                   'codex_compaction_cache', 'codex_thread_titles')):
        raise ValueError('Unsupported prompt preparation settings')
    # Shared defaults cannot override explicit thinking/output in this profile.
    # No load(), serve(), threads, HTTP, engine or weight APIs are invoked.
    messages, tools, kwargs = openai_to_messages(svc.with_shared(payload, 'openai'))
    force = forced_call(payload.get('tool_choice'), tools)
    ids = svc.encode_prompt(messages, tools, kwargs)
    if force and kwargs.get('enable_thinking', True) is False:
        ids += tokenizer.encode(force, parse_special=True)
    # Execute the actual complete server preparation when it fits; for an
    # oversized input preserve its full count instead of truncating to fit.
    if len(ids) + payload['max_tokens'] + CTX_SLACK <= 16384:
        prepared, _, output = svc.prepare(messages, tools, kwargs, payload['max_tokens'], force=force, req=payload)
        if prepared != ids or output != payload['max_tokens']:
            raise ValueError('Server preparation differs from counting')
    verify()
    print(json.dumps({'request_sha256': digest(payload), 'input_tokens': len(ids),
        'token_ids_sha256': digest(ids), 'server_context_reserve': CTX_SLACK,
        'seconds': time.perf_counter() - start, 'model_free': True}))


if __name__ == '__main__':
    main()
