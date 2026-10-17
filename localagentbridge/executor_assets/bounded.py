"""Container command policy and bounded process capture; no agent loop or shell."""
import hashlib
import json
import os
from pathlib import Path
import shlex
import signal
import subprocess
import threading
import time


def run_bounded(argv, *, cwd, seconds, output_bytes, cancel=None):
    """Kill only the created process group on timeout, cancellation or overflow."""
    start = time.monotonic()
    env = {'PATH': os.environ['PATH'], 'HOME': '/state', 'TMPDIR': '/tmp/lab',
           'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONPATH': str(cwd), 'PYTHONUNBUFFERED': '1'}
    if os.name == 'nt':
        env['SystemRoot'] = os.environ['SystemRoot']
    process = subprocess.Popen(argv, cwd=cwd, env=env, stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, start_new_session=os.name == 'posix',
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
    output = bytearray()
    overflow, drained = threading.Event(), threading.Event()
    def read():
        try:
            while chunk := os.read(process.stdout.fileno(), 4096):
                remaining = output_bytes - len(output)
                output.extend(chunk[:remaining])
                if len(chunk) > remaining:
                    overflow.set()
                    break
        finally:
            drained.set()
    reader = threading.Thread(target=read, daemon=True)
    reader.start()
    timed_out = cancelled = False
    try:
        while process.poll() is None or not drained.is_set():
            cancelled = bool(cancel and cancel.is_set())
            timed_out = time.monotonic() - start >= seconds
            if cancelled or timed_out or overflow.is_set():
                break
            time.sleep(.01)
    finally:
        if os.name == 'posix':
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        elif process.poll() is None:
            process.kill()
        process.wait(timeout=5)
        reader.join(5)
        process.stdout.close()
    if not drained.is_set():
        raise RuntimeError('Command output collection did not finish')
    raw = bytes(output)
    return dict(argv=argv, exit_code=process.returncode, timed_out=timed_out,
        cancelled=cancelled, seconds=time.monotonic()-start,
        output=raw.decode(errors='replace'), output_sha256=hashlib.sha256(raw).hexdigest(),
        output_truncated=overflow.is_set())


class CommandPolicy:
    def __init__(self, contract, workspace='/workspace'):
        self.contract, self.workspace = contract, Path(workspace).resolve()
        self.readable = set(contract['context_files'] + contract['permitted_files'] + contract['acceptance_files'])
        self.checks = [c['argv'] for c in contract['checks']]

    def path(self, value):
        candidate = Path(value)
        path = candidate if candidate.is_absolute() else self.workspace/candidate
        if '..' in path.parts or path.resolve() != path or not path.is_file():
            raise ValueError('Path is outside the exact readable files')
        if path.relative_to(self.workspace).as_posix() not in self.readable:
            raise ValueError('Path is outside the exact readable files')
        return path

    def parse(self, command):
        if not isinstance(command, str) or not 0 < len(command) <= 4096 or any(x in command for x in '\n\r\x00'):
            raise ValueError('A single bounded command is required')
        args = shlex.split(command)
        if args in self.checks and 'test' in self.contract['operations']:
            return 'test', args
        if 'read' in self.contract['operations'] and len(args) > 1 and args[0] == 'cat':
            return 'read', [self.path(p) for p in args[1:]]
        raise ValueError('Only cat of listed files or an exact acceptance command is allowed; no shell, chaining or input')

    def execute(self, command, seconds=None):
        kind, values = self.parse(command)
        cap = self.contract['limits']['output_bytes']
        if kind == 'read':
            result = bytearray()
            for path in values:
                with path.open('rb') as stream:
                    result.extend(stream.read(cap-len(result)+1))
                if len(result) > cap:
                    raise ValueError('Read output exceeds the output budget')
            raw = bytes(result)
            return dict(argv=['cat']+[str(p) for p in values], exit_code=0, timed_out=False,
                cancelled=False, seconds=0, output=raw.decode(errors='replace'),
                output_sha256=hashlib.sha256(raw).hexdigest(), output_truncated=False)
        timeout = self.contract['limits']['test_seconds']
        if seconds is not None:
            timeout = min(timeout, max(.01, seconds))
        return run_bounded(values, cwd=self.workspace, seconds=timeout, output_bytes=cap)


def terminal_executor(contract, records):
    from openhands.sdk.tool import ToolExecutor
    from openhands.tools.terminal.definition import TerminalObservation
    policy = CommandPolicy(contract)
    def persist():
        data = json.dumps(records).encode()
        if len(data) > (contract['limits']['output_bytes'] + 8192) * contract['limits']['steps']:
            raise ValueError('Command audit exceeds its bounded allowance')
        temporary = Path('/exchange/commands.tmp')
        fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, 'wb') as output:
            output.write(data)
        temporary.replace('/exchange/commands.json')
    persist()
    class BoundedTerminal(ToolExecutor):
        def __call__(self, action, conversation=None):
            if len(records) >= contract['limits']['steps']:
                raise ValueError('Command step budget exhausted')
            try:
                if action.is_input or action.reset:
                    raise ValueError('Interactive input and resets are outside this contract')
                result = policy.execute(action.command, action.timeout)
                records.append(result)
                persist()
                failed = result['timed_out'] or result['cancelled'] or result['output_truncated']
                return TerminalObservation.from_text(text=result['output'] + ('\nCommand budget exceeded; result is incomplete.' if failed else ''),
                    command=action.command, exit_code=result['exit_code'], timeout=result['timed_out'],
                    is_error=failed or result['exit_code'] != 0)
            except ValueError as error:
                records.append({'command':action.command[:4096], 'denied':str(error)[:2000]})
                persist()
                return TerminalObservation.from_text(text=str(error), command=action.command, exit_code=None, is_error=True)
    return BoundedTerminal()
