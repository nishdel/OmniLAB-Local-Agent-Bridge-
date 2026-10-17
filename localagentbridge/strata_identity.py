"""Trusted Strata serving binding; aliases and API echoes are never weight identity.

The supervisor hashes the complete runtime/weight manifest once. Admission checks
process ownership, exact argv, configuration, template and unchanged file metadata.
Small executable/source/tokenizer artifacts are rehashed. This is a local trust
binding, not remote attestation or protection against a hostile host administrator.
"""
import hashlib
import ipaddress
import json
from pathlib import Path
import re
from urllib.parse import urlsplit

import psutil

from .process_control import alive
from .task_contract import digest


def verify_binding(binding, health, props, origin):
    try:
        return _verify(binding, health, props, origin)
    except (OSError, ValueError, TypeError, KeyError, IndexError, psutil.Error):
        return False


def _verify(b, health, props, origin):
    required = ('identity', 'config_path', 'config_sha256', 'model_path', 'build_info',
                'artifacts', 'process', 'engine_process', 'server_argv', 'engine_argv',
                'source_commit', 'template_sha256', 'context_tokens', 'model_metadata')
    if not isinstance(b, dict) or b.get('family') != 'coder' or any(not b.get(k) for k in required):
        return False
    if not re.fullmatch(r'[0-9a-f]{40}', b['source_commit']):
        return False
    if props.get('build_info') != b['build_info'] or health.get('max_context') != b['context_tokens']:
        return False
    generation = props.get('default_generation_settings', {})
    if generation.get('n_ctx') != b['context_tokens'] or props.get('total_slots') != 1:
        return False
    template = props.get('chat_template')
    if not isinstance(template, str) or hashlib.sha256(template.encode()).hexdigest() != b['template_sha256']:
        return False
    if not alive(b['process']) or not alive(b['engine_process']):
        return False
    server = psutil.Process(b['process']['pid'])
    engine = psutil.Process(b['engine_process']['pid'])
    if engine.ppid() != server.pid or server.cmdline() != b['server_argv'] or engine.cmdline() != b['engine_argv']:
        return False
    # Overrides and autonomous host-side actions must not evade the pinned JSON.
    unsafe = ('--mcp-config', '--api-monitor', '--before-load', '--fit-max-tokens', '--replicas', '--lazy')
    if any(a.split('=')[0] in unsafe for a in b['server_argv']):
        return False
    cfg_path = Path(b['config_path']).resolve(strict=True)
    args = b['server_argv']
    if '--config' not in args or Path(args[args.index('--config')+1]).resolve() != cfg_path:
        return False
    listeners = [c for c in server.net_connections(kind='tcp') if c.status == psutil.CONN_LISTEN]
    endpoint = urlsplit(origin)
    if not any(c.laddr.port == endpoint.port and c.laddr.ip == endpoint.hostname for c in listeners):
        return False
    if any(not ipaddress.ip_address(c.laddr.ip).is_loopback for c in listeners):
        return False
    raw = cfg_path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != b['config_sha256']:
        return False
    cfg = json.loads(raw.decode('utf-8-sig'))
    if cfg.get('model_name') != health.get('model') or props.get('model_alias') != health.get('model'):
        return False
    if any(cfg.get(k) for k in ('mcp_servers', 'mcp', 'api_monitor', 'before_load',
                               'fit_max_tokens', 'replicas', 'vision', 'lazy_load')):
        return False
    if not ipaddress.ip_address(cfg.get('host', '127.0.0.1')).is_loopback:
        return False
    cwd = Path(cfg.get('cwd') or server.cwd()).resolve()
    def absolute(value):
        p = Path(value)
        return (cwd/p).resolve() if not p.is_absolute() else p.resolve()
    if absolute(props.get('model_path', '')) != absolute(b['model_path']):
        return False
    engine_args = cfg.get('args', [])
    flag = '--native' if '--native' in engine_args else '--pack'
    if flag not in engine_args or absolute(engine_args[engine_args.index(flag)+1]) != absolute(b['model_path']):
        return False
    if absolute(cfg['exe']) != Path(engine.exe()).resolve():
        return False
    if engine.cmdline()[1:] != ['--serve', *engine_args]:
        return False
    metadata = b['model_metadata']
    # This explicitly inspected family is the initial supported binding. An Ollama
    # tag or arbitrary GGUF filename cannot establish engine compatibility.
    if metadata.get('model') != 'Qwen3.8-Flash-Next-GSQ-RCO-Coder' or metadata.get('format') not in ('GGUF', 'Strata pack'):
        return False
    if metadata.get('quantization') != 'IQ1_M' or metadata.get('expert_count') != 256:
        return False
    artifacts = b['artifacts']
    roles = set()
    paths = set()
    for artifact in artifacts:
        path = Path(artifact['path']).resolve(strict=True)
        stat = path.stat()
        if path in paths or not path.is_file() or stat.st_size != artifact['size'] or stat.st_mtime_ns != artifact['mtime_ns']:
            return False
        paths.add(path)
        if not re.fullmatch(r'[0-9a-f]{64}', artifact.get('sha256', '')) or artifact.get('verified_by_supervisor') is not True:
            return False
        roles.add(artifact.get('role'))
        if artifact.get('role') != 'weights':
            with path.open('rb') as source:
                if hashlib.file_digest(source, 'sha256').hexdigest() != artifact['sha256']:
                    return False
    if not {'weights', 'engine', 'server', 'tokenizer', 'template'} <= roles or Path(engine.exe()).resolve() not in paths:
        return False
    model_path = absolute(b['model_path'])
    if not any(a.get('role') == 'weights' and (Path(a['path']).resolve() == model_path or
              Path(a['path']).resolve().is_relative_to(model_path)) for a in artifacts):
        return False
    server_sources = {Path(a['path']).resolve() for a in artifacts if a.get('role') == 'server'}
    if '-m' in args:
        if args[args.index('-m')+1] != 'serve.server' or Path(server.cwd()).resolve()/'serve/server.py' not in server_sources:
            return False
    elif not any(Path(a).resolve() in server_sources for a in args if a.endswith('.py')):
        return False
    # Include semantic metadata in the binding so a model label cannot be changed
    # without changing the exact identity used by contracts and qualification.
    expected = digest({k:b[k] for k in ('config_sha256', 'source_commit', 'template_sha256', 'model_metadata')} |
                      {'artifacts':[{k:a[k] for k in ('path','size','sha256','role')} for a in artifacts]})
    return b['identity'] == expected
