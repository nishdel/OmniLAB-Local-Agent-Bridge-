"""Fixed container-side transport for the opt-in read-only/tmpfs profile."""
import errno
import io
import json
import os
from pathlib import Path, PurePosixPath
import stat
import signal
import time
import subprocess
import sys
import tarfile

CAP = 64 * 1024 * 1024
WRITABLE = {'/workspace': 64, '/tmp': 32, '/state': 32, '/exchange': 16, '/dev/shm': 8}


def safe(name):
    p = PurePosixPath(name)
    if p.is_absolute() or any(x in ('', '.', '..') for x in name.split('/')) or ':' in name or '\\' in name:
        raise ValueError('Unsafe archive name')
    return p


def entries(raw):
    if len(raw) > CAP:
        raise ValueError('Seed archive exceeds transport budget')
    result = []
    total = 0
    seen = set()
    with tarfile.open(fileobj=io.BytesIO(raw)) as archive:
        for item in archive:
            name = item.name.rstrip('/')
            safe(name)
            if name in seen or len(seen) >= 10000:
                raise ValueError('Duplicate or excessive seed entries')
            seen.add(name)
            if not (name == 'workspace' or name.startswith('workspace/') or name in ('exchange/task.json', 'exchange/skills.json')):
                raise ValueError('Seed outside fixed roots')
            if not (item.isdir() or item.isfile()) or item.uid not in (0, 10001) or item.gid != item.uid:
                raise ValueError('Unsafe seed entry')
            if item.uid == 10001 and not (item.isfile() and name.startswith('workspace/')):
                raise ValueError('Unsafe writable seed')
            total += item.size
            if total > CAP:
                raise ValueError('Seed contents exceed budget')
            result.append((name, item.isdir(), item.uid, archive.extractfile(item).read() if item.isfile() else b''))
    return result


def write_new(path, data, mode):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, mode)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(data)


def seed(stage, raw):
    if Path('/exchange/ready').exists():
        raise ValueError('Cannot seed a dispatched executor')
    rows = entries(raw)
    if stage == 'seed-root':
        if os.getuid() != 0:
            raise ValueError('Trusted initialization requires root')
        for name, directory, uid, data in rows:
            target = Path('/') / name
            if directory:
                target.mkdir(exist_ok=True)
                if target.is_symlink():
                    raise ValueError('Unexpected seed link')
                target.chmod(0o777)
            elif uid == 0:
                write_new(target, data, 0o444)
        Path('/tmp/lab').mkdir(mode=0o777, exist_ok=True)
        Path('/tmp/lab').chmod(0o777)
    elif stage == 'seed-worker':
        if os.getuid() != 10001:
            raise ValueError('Writable inputs require the worker UID')
        for name, directory, uid, data in rows:
            if not directory and uid == 10001:
                write_new(Path('/') / name, data, 0o644)
    else:
        raise ValueError('Unknown seed phase')


def ready():
    if os.getuid() != 0:
        raise ValueError('Trusted sealing requires root')
    if Path('/exchange/ready').exists():
        return
    for path, dirs, files in os.walk('/workspace', followlinks=False):
        for name in dirs + files:
            if (Path(path)/name).is_symlink():
                raise ValueError('Unexpected initialized link')
        Path(path).chmod(0o555)
    for name in ('task.json',):
        item = Path('/exchange')/name
        if item.stat().st_uid != 0 or stat.S_IMODE(item.stat().st_mode) != 0o444:
            raise ValueError('Immutable contract missing')
    write_new('/exchange/ready', b'1', 0o444)


def read_file(path, cap):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd, 'rb') as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_size > cap:
            raise ValueError('Special or excessive transport artifact')
        value = stream.read(cap+1)
        if len(value) > cap:
            raise ValueError('Growing artifact exceeds budget')
        return value


def collect(path, cap):
    if path not in ('/exchange/request.json', '/exchange/result.json', '/exchange/completion.json', '/exchange/commands.json', '/workspace/.'):
        raise ValueError('Unknown artifact path')
    if path != '/workspace/.':
        sys.stdout.buffer.write(read_file(path, cap))
        return
    out = io.BytesIO()
    total = count = 0
    with tarfile.open(fileobj=out, mode='w') as archive:
        for parent, dirs, files in os.walk('/workspace', followlinks=False):
            for name in dirs:
                if (Path(parent)/name).is_symlink():
                    raise ValueError('Candidate contains directory link')
            for name in sorted(files):
                file = Path(parent)/name
                data = read_file(file, cap-total)
                total += len(data)
                count += 1
                if count > 10000:
                    raise ValueError('Too many candidate files')
                info = tarfile.TarInfo(file.relative_to('/workspace').as_posix())
                safe(info.name)
                info.size = len(data)
                archive.addfile(info, io.BytesIO(data))
    sys.stdout.buffer.write(out.getvalue())


def supervise(mode):
    # Linux namespace init ignores in-namespace SIGSTOP. Keep a fixed, idle init
    # so the SDK is a normal child that can be quiesced before collection. This
    # is process lifecycle only; OpenHands still owns every agent-loop decision.
    if mode not in ('agent', 'verify', 'baseline') or os.getpid() != 1:
        raise ValueError('Invalid sandbox supervisor invocation')
    child = subprocess.Popen([sys.executable, '/opt/lab/runner.py', mode], stdin=subprocess.DEVNULL)
    def terminate(*_):
        if child.poll() is None:
            child.kill()
        raise SystemExit(1)
    signal.signal(signal.SIGTERM, terminate)
    while child.poll() is None:
        time.sleep(.1)
    raise SystemExit(child.returncode)


def freeze():
    # This runs only through the controller's fixed transport inside the owned
    # PID namespace. Stop all other worker processes before failure collection;
    # never inspect or signal host PIDs. The controller itself remains outside.
    if os.getuid() != 10001:
        raise ValueError('Freeze requires the worker UID')
    cmdline = Path('/proc/1/cmdline').read_bytes().split(b'\0')
    if b'/opt/lab/transport.py' not in cmdline or b'supervise' not in cmdline:
        raise ValueError('Collection requires the fixed PID1 supervisor')
    stopped = set()
    for _ in range(4):
        active = []
        for path in Path('/proc').iterdir():
            if not path.name.isdigit() or int(path.name) in (1, os.getpid()):
                continue
            try:
                fields = dict(line.split(':', 1) for line in (path/'status').read_text().splitlines() if ':' in line)
                if fields['State'].strip()[0] in ('T', 't', 'Z'):
                    continue
                if int(fields['Uid'].split()[0]) != 10001:
                    raise ValueError('Unexpected process owner inside sandbox')
                active.append(int(path.name))
            except FileNotFoundError:
                pass
        if not active:
            print(json.dumps({'quiesced': True, 'stopped': sorted(stopped)}))
            return
        for pid in sorted(active):
            try:
                os.kill(pid, signal.SIGSTOP)
                stopped.add(pid)
            except ProcessLookupError:
                pass
        time.sleep(.02)
    raise ValueError('Sandbox did not quiesce for collection')


def probe():
    result = {'allocation': {}, 'root_readonly': False, 'dev_creation_denied': False}
    for path, mib in WRITABLE.items():
        target = Path(path)/'lab-allocation-probe'
        written = 0
        try:
            with target.open('wb', buffering=0) as stream:
                while True:
                    written += stream.write(b'X' * 65536)
        except OSError as error:
            if error.errno != errno.ENOSPC:
                raise
        info = target.stat()
        result['allocation'][path] = {'written': written, 'apparent': info.st_size, 'allocated': info.st_blocks*512, 'capacity': mib*1024*1024}
        if not written == info.st_size == info.st_blocks*512 == mib*1024*1024:
            raise ValueError('Actual tmpfs allocation limit was not demonstrated')
        target.unlink()
    try:
        Path('/lab-root-write-probe').write_bytes(b'X')
    except OSError as error:
        result['root_readonly'] = error.errno == errno.EROFS
    try:
        Path('/dev/lab-write-probe').write_bytes(b'X')
    except PermissionError:
        result['dev_creation_denied'] = True
    if not all(result[k] for k in ('root_readonly', 'dev_creation_denied')):
        raise ValueError('Root/device write protection is unqualified')
    print(json.dumps(result))


if __name__ == '__main__':
    action = sys.argv[1]
    if action.startswith('seed-'):
        seed(action, sys.stdin.buffer.read(CAP+1))
    elif action == 'ready':
        ready()
    elif action == 'collect':
        cap = int(sys.argv[3])
        if not 0 < cap <= CAP:
            raise ValueError('Invalid collection budget')
        collect(sys.argv[2], cap)
    elif action == 'supervise':
        supervise(sys.argv[2])
    elif action == 'freeze':
        freeze()
    elif action == 'probe':
        probe()
    else:
        raise ValueError('Unknown fixed transport command')
