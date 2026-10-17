"""Owned Docker sandboxes, snapshots and trusted artifact collection. No host execution fallback."""
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import tarfile
import uuid

from .task_contract import safe_path

SDK_VERSION = '1.53.0'
TMPFS_MIB = {'/workspace': 64, '/tmp': 32, '/state': 32, '/exchange': 16}
READONLY_PROFILE = 'readonly_tmpfs_v1'


def command(argv, *, input=None, timeout=30, max_output=64000000):
    # Read bounded output concurrently; terminate only this owned CLI process if
    # transport/artifact output exceeds its allowance. Never signal the daemon.
    import threading
    process = subprocess.Popen(argv, stdin=subprocess.PIPE if input is not None else subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
    outputs = [bytearray(), bytearray()]
    overflow = threading.Event()
    def read(pipe, index, limit):
        while True:
            chunk = pipe.read(4096)
            if not chunk:
                return
            outputs[index].extend(chunk)
            if len(outputs[index]) > limit:
                overflow.set()
                process.terminate()
                return
    threads = [threading.Thread(target=read,args=(process.stdout,0,max_output),daemon=True),
               threading.Thread(target=read,args=(process.stderr,1,16000),daemon=True)]
    for thread in threads:
        thread.start()
    def write():
        try:
            process.stdin.write(input)
            process.stdin.close()
        except (BrokenPipeError, OSError):
            pass
    writer = threading.Thread(target=write,daemon=True) if input is not None else None
    if writer:
        writer.start()
    try:
        process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)
        raise
    finally:
        for thread in threads:
            thread.join(2)
    if overflow.is_set():
        raise ValueError('Command/artifact output exceeds budget')
    if process.returncode:
        raise RuntimeError(bytes(outputs[1]).decode(errors='replace')[:2000] or 'Command failed')
    return bytes(outputs[0])


def git_snapshot(repository, revision, max_bytes):
    raw = command(['git', '-C', str(repository), 'archive', '--format=tar', revision])
    if len(raw) > max_bytes:
        raise ValueError('Repository snapshot exceeds byte budget; narrow/split the task')
    return unpack(raw, max_bytes)


def unpack(raw, max_bytes):
    files = {}
    total = 0
    with tarfile.open(fileobj=io.BytesIO(raw)) as tar:
        for entry in tar:
            name = entry.name.rstrip('/')
            safe_path(name)
            if entry.isdir():
                continue
            if not entry.isfile() or entry.size > max_bytes:
                raise ValueError('Snapshot contains link/special/oversized file')
            total += entry.size
            if total > max_bytes or len(files) >= 10000:
                raise ValueError('Snapshot exceeds budget')
            files[name] = tar.extractfile(entry).read()
    return files


def tree_hash(files):
    return hashlib.sha256(b''.join(k.encode() + b'\0' + hashlib.sha256(v).digest()
                                   for k, v in sorted(files.items()))).hexdigest()


def bundle(files, contract, *, implementation=True):
    out = io.BytesIO()
    files = dict(files)
    # Exact new paths are precreated; directories stay root-owned and non-writable.
    if implementation:
        for path in contract.permitted_files:
            files.setdefault(path, b'')
    with tarfile.open(fileobj=out, mode='w') as tar:
        directories = {'workspace'}
        for path in files:
            safe_path(path)
            directories.update('workspace/' + str(p) for p in Path(path).parents if str(p) != '.')
        for path in sorted(directories, key=lambda x: (x.count('/'), x)):
            item = tarfile.TarInfo(path.replace('\\', '/'))
            item.type, item.mode, item.uid, item.gid = tarfile.DIRTYPE, 0o555, 0, 0
            tar.addfile(item)
        for path, content in files.items():
            item = tarfile.TarInfo('workspace/' + path)
            writable = implementation and path in contract.permitted_files
            item.uid = item.gid = 10001 if writable else 0
            item.mode, item.size = (0o644 if writable else 0o444), len(content)
            tar.addfile(item, io.BytesIO(content))
        task = json.dumps(contract.model_dump()).encode()
        item = tarfile.TarInfo('exchange/task.json')
        item.mode, item.size = 0o444, len(task)
        tar.addfile(item, io.BytesIO(task))
    return out.getvalue()


class DockerSandbox:
    def __init__(self, settings, run_command=command):
        self.settings, self.run_command = settings, run_command
        self.docker = settings.get('docker', 'docker')
        self.image = settings.get('image', '')
        self.readonly = settings.get('storage_profile') == READONLY_PROFILE
        if settings.get('storage_profile', 'quota') not in ('quota', READONLY_PROFILE):
            raise ValueError('Unknown sandbox storage profile')
        self.probe_evidence = None
        if not re.fullmatch(r'sha256:[a-f0-9]{64}', self.image):
            raise ValueError('Configure an existing exact sandbox image ID, never a mutable tag')

    def call(self, *args, input=None, timeout=30, max_output=64000000):
        return self.run_command([self.docker, *args], input=input, timeout=timeout, max_output=max_output)

    def preflight(self):
        info = json.loads(self.call('info', '--format', '{{json .}}'))
        if info.get('OSType') != 'linux':
            raise ValueError('A Linux Docker sandbox is required')
        # Docker Desktop's containerd overlayfs snapshotter accepted size=2G
        # but allowed 2 GiB + 64 MiB in the live qualification probe. Inspecting
        # HostConfig.StorageOpt alone is not evidence of enforced storage limits.
        status = dict(info.get('DriverStatus') or [])
        if not self.readonly and (info.get('Driver') != 'overlay2' or status.get('Backing Filesystem') != 'xfs'):
            raise ValueError('Writable-layer quota is unqualified: require overlay2 on XFS with project quotas and an actual enforcement check')
        image = json.loads(self.call('image', 'inspect', self.image))[0]
        if image['Id'] != self.image or image.get('Config', {}).get('Labels', {}).get('org.omnilab.sdk') != SDK_VERSION:
            raise ValueError('Unverified OpenHands SDK sandbox image')
        if self.readonly:
            if image.get('Config', {}).get('Labels', {}).get('org.omnilab.transport') != READONLY_PROFILE:
                raise ValueError('Read-only transport image is unverified')
            if image.get('Config', {}).get('Labels', {}).get('org.omnilab.commands') != 'bounded_v3':
                raise ValueError('Bounded command executor image is unverified')
            self.probe_evidence = self.probe_storage()
        return True

    def profile_args(self, probe=False):
        args = ['--read-only', '--shm-size', '8m', '--log-driver', 'none',
                '--ulimit', 'nofile=1024:1024', '--ulimit', 'msgqueue=8192:8192']
        for path, mib in TMPFS_MIB.items():
            mode = '0755' if probe else ('1777' if path in ('/tmp', '/exchange') else '0777')
            uid = '10001' if probe or path == '/state' else '0'
            args += ['--tmpfs', f'{path}:rw,nosuid,nodev,size={mib*1024*1024},uid={uid},gid={uid},mode={mode}']
        return args

    def probe_storage(self):
        name = 'lab-storage-' + str(uuid.uuid4())
        raw = self.call('run', '--rm', '--pull=never', '--name', name, '--network', 'none',
            '--user', '10001:10001', '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges:true',
            '--memory', '512m', '--memory-swap', '512m', '--cpus', '1', '--pids-limit', '32',
            *self.profile_args(probe=True), '--entrypoint', 'python', self.image,
            '/opt/lab/transport.py', 'probe', timeout=60, max_output=65536)
        result = json.loads(raw)
        expected = TMPFS_MIB | {'/dev/shm': 8}
        if (not result.get('root_readonly') or not result.get('dev_creation_denied') or
                set(result.get('allocation', {})) != set(expected) or any(
                any(result['allocation'][path].get(k) != mib*1024*1024 for k in ('written', 'apparent', 'allocated', 'capacity'))
                for path, mib in expected.items())):
            raise ValueError('Actual read-only storage enforcement failed')
        return result

    def create(self, name, owner, contract, mode='agent'):
        if not re.fullmatch(r'lab-[a-f0-9-]{36}(-verify|-baseline)?', name):
            raise ValueError('Invalid owned sandbox name')
        if mode not in ('agent', 'verify', 'baseline'):
            raise ValueError('Unknown sandbox mode')
        if self.readonly and (contract.limits.memory_mb > 2048 or contract.limits.cpus > 2):
            raise ValueError('Read-only qualification resource ceiling exceeded')
        # Storage quota must be supported by the installed Docker storage driver.
        # Unsupported quota is a hard failure, never a retry without the restriction.
        args = ['create', '--name', name, '--label', 'org.omnilab.owner=' + owner,
                '--label', 'org.omnilab.mode=' + mode, '--network', 'none',
                '--user', '10001:10001', '--cap-drop', 'ALL',
                '--security-opt', 'no-new-privileges:true', '--pids-limit', '128',
                '--memory', str(contract.limits.memory_mb) + 'm',
                '--memory-swap', str(contract.limits.memory_mb) + 'm',
                '--cpus', str(contract.limits.cpus),
                '--ulimit', 'fsize=67108864:67108864',
                ]
        args += (self.profile_args() + ['--env', 'LAB_HOLD_FOR_COLLECTION=1'] if self.readonly else
                 ['--storage-opt', 'size=2G', '--log-opt', 'max-size=1m', '--log-opt', 'max-file=2'])
        args += ['--env', 'LAB_CONVERSATION_ID=' + owner, '--workdir', '/workspace', '--entrypoint', 'python', self.image]
        args += ['/opt/lab/transport.py', 'supervise', mode] if self.readonly else ['/opt/lab/runner.py', mode]
        self.call(*args)
        self.inspect(name, owner)
        return name

    def inspect(self, name, owner):
        rows = json.loads(self.call('inspect', name))
        if len(rows) != 1:
            raise ValueError('Uncertain executor identity')
        row = rows[0]
        cfg, host = row['Config'], row['HostConfig']
        if (cfg.get('Labels', {}).get('org.omnilab.owner') != owner or row.get('Image') != self.image
                or cfg.get('User') != '10001:10001' or host.get('NetworkMode') != 'none'
                or host.get('Privileged') or host.get('Binds') or (row.get('Mounts') and not self.readonly)
                or host.get('CapAdd') or 'ALL' not in host.get('CapDrop', [])
                or not set(host.get('SecurityOpt', [])) <= {'no-new-privileges','no-new-privileges:true','no-new-privileges=true'}
                or not host.get('SecurityOpt')
                or host.get('PidMode') not in (None,'','private') or host.get('IpcMode') not in (None,'','private')
                or host.get('UTSMode') not in (None,'','private') or host.get('Devices') or host.get('DeviceRequests')
                or set(row.get('NetworkSettings', {}).get('Networks', {'none':{}})) != {'none'}
                or host.get('Memory', 0) <= 0 or host.get('MemorySwap') != host.get('Memory')
                or host.get('PidsLimit', 0) <= 0 or (not self.readonly and host.get('StorageOpt', {}).get('size') != '2G')):
            raise ValueError('Owned sandbox security configuration changed or is insufficient')
        if self.readonly:
            tmpfs = host.get('Tmpfs', {})
            if (not host.get('ReadonlyRootfs') or set(tmpfs) != set(TMPFS_MIB)
                    or host.get('ShmSize') != 8*1024*1024 or host.get('LogConfig', {}).get('Type') != 'none'
                    or not 0 < host.get('NanoCpus', 0) <= 2*10**9 or host['Memory'] > 2048*1024*1024
                    or host['PidsLimit'] > 128 or host.get('StorageOpt')
                    or any(m.get('Type') != 'tmpfs' or m.get('Destination') not in TMPFS_MIB for m in row.get('Mounts', []))
                    or any(f'size={mib*1024*1024}' not in tmpfs[path].split(',') or
                           not {'rw', 'nosuid', 'nodev'} <= set(tmpfs[path].split(',')) for path, mib in TMPFS_MIB.items())):
                raise ValueError('Read-only sandbox security configuration changed')
        return row

    def put(self, name, owner, archive):
        self.inspect(name, owner)
        if self.readonly:
            row = self.inspect(name, owner)
            if row['State']['Status'] != 'created':
                raise ValueError('Read-only inputs can only be initialized once')
            self.call('start', name)
            for stage, uid in (('seed-root', '0:0'), ('seed-worker', '10001:10001')):
                self.call('exec', '-i', '--user', uid, name, 'python', '/opt/lab/transport.py', stage, input=archive)
        else:
            self.call('cp', '-a', '-', name + ':/', input=archive)

    def start(self, name, owner):
        row = self.inspect(name, owner)
        if self.readonly:
            if row['State']['Status'] != 'running':
                raise ValueError('Read-only executor disappeared; tmpfs cannot be restarted')
            self.call('exec', '--user', '0:0', name, 'python', '/opt/lab/transport.py', 'ready')
            return
        if row['State']['Status'] == 'created':
            self.call('start', name)
        elif row['State']['Status'] not in ('running', 'exited'):
            raise ValueError('Executor requires reconciliation; cannot restart it')

    def read(self, name, owner, path, max_bytes=2000000):
        self.inspect(name, owner)
        if path not in ('/exchange/request.json', '/exchange/result.json', '/exchange/commands.json', '/workspace/.'):
            raise ValueError('Only fixed artifact paths may be collected')
        if self.readonly:
            if not self.inspect(name, owner)['State']['Running']:
                raise ValueError('Read-only executor lost tmpfs before durable collection')
            raw = self.call('exec', name, 'python', '/opt/lab/transport.py', 'collect', path, str(max_bytes),
                            timeout=60, max_output=max_bytes+6000000)
            return unpack(raw, max_bytes) if path == '/workspace/.' else json.loads(raw)
        # docker cp emits a tar. File-size ulimit and rootfs quota bound producer storage;
        # total snapshot budget is checked before parsing/extraction.
        raw = self.call('cp', name + ':' + path, '-', timeout=60, max_output=max_bytes+65536)
        if len(raw) > max_bytes + 65536:
            raise ValueError('Artifact exceeds collection limit')
        if path == '/workspace/.':
            with tarfile.open(fileobj=io.BytesIO(raw)) as tar:
                files = {}
                for item in tar:
                    path = item.name.removeprefix('./').rstrip('/')
                    if not path or item.isdir():
                        continue
                    safe_path(path)
                    if not item.isfile() or item.size > max_bytes:
                        raise ValueError('Worker supplied a link/special/oversized artifact')
                    files[path] = tar.extractfile(item).read()
                if sum(map(len, files.values())) > max_bytes:
                    raise ValueError('Candidate exceeds snapshot budget')
                return files
        with tarfile.open(fileobj=io.BytesIO(raw)) as tar:
            members = tar.getmembers()
            if len(members) != 1 or not members[0].isfile() or members[0].size > max_bytes:
                raise ValueError('Malformed mailbox artifact')
            return json.loads(tar.extractfile(members[0]).read())

    def completion(self, name, owner):
        if not self.readonly:
            state = self.inspect(name, owner)['State']
            return state if not state['Running'] else None
        if not self.inspect(name, owner)['State']['Running']:
            raise ValueError('Read-only executor lost tmpfs; explicit recovery required')
        try:
            raw = self.call('exec', name, 'python', '/opt/lab/transport.py', 'collect',
                            '/exchange/completion.json', '10000', max_output=10000)
        except RuntimeError as error:
            if 'No such file' in str(error):
                return None
            raise
        value = json.loads(raw)
        if type(value.get('ExitCode')) is not int:
            raise ValueError('Invalid executor completion marker')
        return value

    def respond(self, name, owner, response):
        self.inspect(name, owner)
        data = json.dumps(response).encode()
        # Fixed code and path; no host/provider credentials ever enter the container.
        self.call('exec', '-i', name, 'python', '-c',
                  "import os,sys; p='/exchange/response.tmp'; fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_TRUNC|os.O_NOFOLLOW,0o600); f=os.fdopen(fd,'wb'); f.write(sys.stdin.buffer.read(2000001)); f.close(); os.replace(p,'/exchange/response.json')",
                  input=data)

    def freeze(self, name, owner):
        self.inspect(name, owner)
        if not self.readonly:
            raise ValueError('Fixed quiescent collection requires the read-only profile')
        result = json.loads(self.call('exec', name, 'python', '/opt/lab/transport.py', 'freeze', max_output=10000))
        if result.get('quiesced') is not True:
            raise ValueError('Collection could not quiesce the owned executor')
        return result

    def stop(self, name, owner):
        self.inspect(name, owner)
        self.call('stop', '--time', '5', name)
        return not self.inspect(name, owner)['State']['Running']
