"""Read-only registration advice and small local diagnostics; no installer."""
import importlib.metadata
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import tomllib
from .routing import inventory, canonical, install_command


def config_path(value=None):
    value = value or os.getenv('LAB_CONFIG')
    return Path(value).resolve() if value else Path('config.toml').resolve()


def codex_config(config, path):
    # JSON strings are also valid TOML basic strings, including escaped Windows paths.
    quote = lambda value: json.dumps(str(value), ensure_ascii=True)
    timeout = int(config.timeout_seconds * max(config.adaptive.max_attempts, len(config.consensus_roles)) + 30)
    return ('[mcp_servers.localagentbridge]\n'
            f'command = {quote(sys.executable)}\n'
            f'args = ["-m", "localagentbridge", "--config", {quote(path)}, "server"]\n'
            'startup_timeout_sec = 20\n'
            f'tool_timeout_sec = {timeout}\n')


async def doctor(config, path, transport=None):
    checks = []
    def add(name, ok, detail):
        checks.append(dict(check=name, status='ok' if ok else 'error', detail=detail))
    add('Python', sys.version_info >= (3, 11), sys.version.split()[0])
    for module, package in [('mcp', 'mcp'), ('httpx', 'httpx'), ('pathspec', 'pathspec'), ('google.protobuf', 'protobuf')]:
        try:
            available = importlib.util.find_spec(module) is not None
            version = importlib.metadata.version(package)
        except (ImportError, importlib.metadata.PackageNotFoundError):
            available, version = False, 'missing; reinstall project dependencies'
        add(package, available, version)
    try:
        config.data_dir.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryFile(dir=config.data_dir) as probe:
            probe.write(b'local write probe')
        add('Data directory', True, 'Writable; SQLite is created locally, no bundled history')
    except OSError:
        add('Data directory', False, 'Not writable; set data_dir to a local writable folder')
    try:
        installed = await inventory(config, transport)
        add('Ollama endpoint', True, config.endpoint)
        names = {p.name for p in config.model_registry if p.enabled} | set(config.roles.values())
        if not names:
            names = {config.model}
        for name in sorted(names):
            info = installed.get(canonical(name))
            local = bool(info is not None and not info.get('remote_host') and not info.get('remote_model'))
            add('Model '+name, local, 'Installed local weights' if local else install_command(name)+' (no substitute)')
    except Exception:
        add('Ollama endpoint', False, 'Unavailable or invalid inventory; start Ollama and check endpoint')
    generated = tomllib.loads(codex_config(config, path))['mcp_servers']['localagentbridge']
    add('Generated MCP configuration', Path(generated['command']).is_file() and path.is_file(),
        'Valid TOML and executable/config paths' if path.is_file() else 'Copy config.example.toml to config.toml first')
    host_config = config.codex_home / 'config.toml'
    try:
        host = tomllib.loads(host_config.read_text(encoding='utf-8')) if host_config.exists() else {}
        registration = host.get('mcp_servers', {}).get('localagentbridge')
        if registration:
            valid = registration.get('command') == generated['command'] and registration.get('enabled', True) and (
                str(path) in registration.get('args', []) or registration.get('env', {}).get('LAB_CONFIG') == str(path))
            checks.append(dict(check='Codex registration', status='ok' if valid else 'warning', detail='Matches this installation' if valid else 'Review command/config path using codex-config; alternate valid launchers may differ'))
        else:
            checks.append(dict(check='Codex registration', status='warning', detail='Not registered in user config; run codex-config. Project/plugin registration may exist separately.'))
    except (OSError, ValueError):
        add('Codex registration', False, 'User config could not be read or parsed; contents omitted')
    return checks
