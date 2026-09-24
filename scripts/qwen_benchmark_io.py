"""Benchmark-only durable IO, transport capture and Windows ownership helpers."""
import asyncio
import ctypes
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import time
import uuid

import httpx
import psutil


def clean(value):
    if hasattr(value, 'model_dump'):
        return clean(value.model_dump())
    if isinstance(value, dict):
        return {str(k): clean(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [clean(v) for v in value]
    if isinstance(value, float) and not math.isfinite(value):
        return 'unbounded'
    if isinstance(value, Path):
        return str(value)
    return value


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def atomic(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    with temp.open('x', encoding='utf-8') as stream:
        json.dump(clean(value), stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temp, path)


def append(path, value):
    with Path(path).open('a', encoding='utf-8') as stream:
        stream.write(json.dumps(clean(value), ensure_ascii=False, allow_nan=False) + '\n')
        stream.flush()
        os.fsync(stream.fileno())


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def identity(pid=None):
    process = psutil.Process(pid or os.getpid())
    result = dict(pid=process.pid, created=process.create_time(), exe=process.exe(), args=process.cmdline())
    if os.name == 'nt':
        result['created_filetime'] = process_filetime(process.pid)
    return result


def handle_filetime(handle):
    """Exact 100 ns Windows creation identity; no float/datetime round trip."""
    from ctypes import wintypes
    values = [wintypes.FILETIME() for _ in range(4)]
    get_times = ctypes.windll.kernel32.GetProcessTimes
    get_times.argtypes = [wintypes.HANDLE] + [ctypes.POINTER(wintypes.FILETIME)]*4
    get_times.restype = wintypes.BOOL
    if not get_times(int(handle), *(ctypes.byref(v) for v in values)):
        raise OSError('Unable to read pinned process creation identity')
    return (values[0].dwHighDateTime << 32) | values[0].dwLowDateTime


def process_filetime(pid):
    import win32api
    try:
        handle = win32api.OpenProcess(0x1000,False,pid)
    except win32api.error as error:
        if error.winerror == 87:
            raise psutil.NoSuchProcess(pid) from None
        if error.winerror == 5:
            raise psutil.AccessDenied(pid) from None
        raise OSError('Process identity unavailable') from None
    try:
        return handle_filetime(handle)
    finally:
        win32api.CloseHandle(handle)


def alive(record):
    if not record:
        return False
    try:
        process = psutil.Process(record['pid'])
        same = (process_filetime(record['pid'])==record['created_filetime'] if record.get('created_filetime')
                else process.create_time()==record['created'])
        return same and process.exe() == record['exe'] and process.is_running()
    except (psutil.Error,OSError):
        return False


class Lock:
    """Kernel-released lock; the file is never treated as evidence of a live owner."""
    def __init__(self, path):
        self.path = Path(path)

    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.handle = self.path.open('a+b')
        if self.path.stat().st_size == 0:
            self.handle.write(b'0')
            self.handle.flush()
        self.handle.seek(0)
        try:
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(self.handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(self.handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            self.handle.close()
            raise RuntimeError('Another worker/reviewer owns this lock: ' + str(self.path)) from None
        return self

    def __exit__(self, *_):
        self.handle.close()


def detached(argv, cwd, stdout, stderr, env=None):
    """No inherited console or input/output pipes; no breakaway/sandbox bypass flags."""
    with Path(stdout).open('ab') as out, Path(stderr).open('ab') as err:
        return subprocess.Popen(argv, cwd=str(cwd), env=env or os.environ.copy(),
            stdin=subprocess.DEVNULL, stdout=out, stderr=err, close_fds=True,
            creationflags=(subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP) if os.name == 'nt' else 0,
            start_new_session=os.name != 'nt')


class OwnedRuntime:
    """Windows kill-on-close job contains ONLY this benchmark's runtime tree."""
    def __init__(self, argv, cwd, env, directory):
        import win32api
        import win32job
        self.api, self.jobs = win32api, win32job
        self.job = win32job.CreateJobObject(None, '')
        limits = win32job.QueryInformationJobObject(self.job, win32job.JobObjectExtendedLimitInformation)
        limits['BasicLimitInformation']['LimitFlags'] = win32job.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        win32job.SetInformationJobObject(self.job, win32job.JobObjectExtendedLimitInformation, limits)
        self.out = (directory / 'runtime.stdout.log').open('ab')
        self.err = (directory / 'runtime.stderr.log').open('ab')
        # Assign the job before the runtime can create any children.
        self.process = subprocess.Popen(argv, cwd=str(cwd), env=env, stdin=subprocess.DEVNULL,
            stdout=self.out, stderr=self.err, close_fds=True,
            creationflags=subprocess.CREATE_NO_WINDOW | 0x00000004)  # CREATE_SUSPENDED
        handle = win32api.OpenProcess(0x0100 | 0x0001, False, self.process.pid)
        try:
            win32job.AssignProcessToJobObject(self.job, handle)
            import win32process
            for thread in psutil.Process(self.process.pid).threads():
                thread_handle = win32api.OpenThread(0x0002, False, thread.id)  # THREAD_SUSPEND_RESUME
                try:
                    win32process.ResumeThread(thread_handle)
                finally:
                    win32api.CloseHandle(thread_handle)
        except Exception:
            self.process.terminate()
            self.process.wait(timeout=10)
            win32api.CloseHandle(self.job)
            raise
        finally:
            win32api.CloseHandle(handle)
        self.identity = identity(self.process.pid)

    def contains(self, candidate):
        """Use one pinned handle for identity and authoritative Windows job membership."""
        import win32process
        try:
            handle = self.api.OpenProcess(0x1000, False, candidate['pid'])  # QUERY_LIMITED_INFORMATION
        except self.api.error as error:
            if error.winerror == 87:
                raise psutil.NoSuchProcess(candidate['pid']) from None
            if error.winerror == 5:
                raise psutil.AccessDenied(candidate['pid']) from None
            raise OSError('Process handle unavailable') from None
        try:
            stamp = handle_filetime(handle)
            if stamp != candidate.get('created_filetime'):
                raise RuntimeError('Exact native process creation identity changed or is unavailable')
            if win32process.GetExitCodeProcess(handle) != 259:  # STILL_ACTIVE
                raise psutil.NoSuchProcess(candidate['pid'])
            return bool(self.jobs.IsProcessInJob(handle, self.job))
        except self.api.error as error:
            if error.winerror == 5:
                raise psutil.AccessDenied(candidate['pid']) from None
            raise OSError('Job membership query unavailable') from None
        finally:
            self.api.CloseHandle(handle)

    def close(self):
        self.api.CloseHandle(self.job)
        self.process.wait(timeout=15)
        self.out.close()
        self.err.close()


def windows_commit():
    if os.name != 'nt':
        return None
    from ctypes import wintypes
    class Performance(ctypes.Structure):
        _fields_ = [('cb', wintypes.DWORD)] + [(n, ctypes.c_size_t) for n in
            ('CommitTotal', 'CommitLimit', 'CommitPeak', 'PhysicalTotal', 'PhysicalAvailable',
             'SystemCache', 'KernelTotal', 'KernelPaged', 'KernelNonpaged', 'PageSize')] + [
            (n, wintypes.DWORD) for n in ('HandleCount', 'ProcessCount', 'ThreadCount')]
    data = Performance()
    data.cb = ctypes.sizeof(data)
    if not ctypes.windll.psapi.GetPerformanceInfo(ctypes.byref(data), data.cb):
        return {'error': ctypes.get_last_error()}
    return {k: getattr(data, k) * data.PageSize for k in
            ('CommitTotal', 'CommitLimit', 'CommitPeak', 'PhysicalAvailable')}


def sample(runtime=None):
    memory, swap = psutil.virtual_memory(), psutil.swap_memory()
    processes = []
    if alive(runtime):
        parent = psutil.Process(runtime['pid'])
        for process in [parent, *parent.children(recursive=True)]:
            try:
                processes.append(dict(pid=process.pid, created=process.create_time(), name=process.name(),
                    memory=process.memory_info()._asdict(), cpu=process.cpu_times()._asdict()))
            except psutil.Error:
                pass
    return dict(time=time.time(), system_ram=memory._asdict(), swap=swap._asdict(),
                commit=windows_commit(), owned_processes=processes,
                owned_rss_bytes=sum(p['memory']['rss'] for p in processes) if processes else None)


def exhaustion(sample_value, free_disk):
    # Low physical availability alone is expected with mmap/paging and never stops a run.
    commit = sample_value.get('commit') or {}
    if free_disk < 64 * 1024**2:
        return 'Evidence volume has less than 64 MiB free; reserve remaining capacity for terminal evidence.'
    if (commit.get('CommitLimit', 0) - commit.get('CommitTotal', 0) < 64 * 1024**2
            and sample_value['system_ram']['available'] < 64 * 1024**2 and commit.get('CommitLimit')):
        return 'Both system commit headroom and available physical RAM below 64 MiB.'
    return None


class CaptureStream(httpx.AsyncByteStream):
    def __init__(self, inner, directory, progress):
        self.inner, self.directory, self.progress = inner, directory, progress

    def __aiter__(self):
        self.iterator = self._iterate()
        return self.iterator

    async def _iterate(self):
        buffer = b''
        counters = {'content_chars': 0, 'thinking_chars': 0, 'last_model_output_at': None,
                    'last_stream_event_at': None, 'runtime_tokens': None}
        final = None
        with (self.directory/'response.ndjson').open('xb') as raw, \
             (self.directory/'answer.txt').open('x', encoding='utf-8') as answer, \
             (self.directory/'thinking.txt').open('x', encoding='utf-8') as thinking:
            try:
                async for chunk in self.inner:
                    raw.write(chunk)
                    raw.flush()
                    os.fsync(raw.fileno())
                    buffer += chunk
                    while b'\n' in buffer:
                        line, buffer = buffer.split(b'\n', 1)
                        if not line.strip():
                            continue
                        event = json.loads(line)
                        now = time.time()
                        content = event.get('message', {}).get('content') or ''
                        thought = event.get('message', {}).get('thinking') or ''
                        answer.write(content)
                        thinking.write(thought)
                        for output in (answer, thinking):
                            output.flush()
                            os.fsync(output.fileno())
                        counters['content_chars'] += len(content)
                        counters['thinking_chars'] += len(thought)
                        counters['last_stream_event_at'] = now
                        if content or thought:
                            counters['last_model_output_at'] = now
                        if event.get('done'):
                            final = event
                            atomic(self.directory/'terminal.json', event)
                            counters['runtime_tokens'] = {k: event.get(k) for k in ('prompt_eval_count', 'eval_count')}
                        atomic(self.directory/'progress.json', counters | {'finish_reason': (final or {}).get('done_reason')})
                        self.progress(counters, self.directory)
                    yield chunk
            finally:
                atomic(self.directory/'stream-state.json', counters | {'final_event_received': final is not None,
                    'finish_reason': (final or {}).get('done_reason'), 'ended_at': time.time(),
                    'unparsed_tail_bytes': len(buffer)})

    async def aclose(self):
        try:
            if hasattr(self, 'iterator'):
                await self.iterator.aclose()
        finally:
            await self.inner.aclose()


class CaptureTransport(httpx.AsyncBaseTransport):
    def __init__(self, directory, progress, expected=None, inner=None):
        self.directory, self.progress, self.expected = directory, progress, expected
        self.inner = inner or httpx.AsyncHTTPTransport(retries=0)
        self.calls = 0

    async def handle_async_request(self, request):
        if request.url.path != '/api/chat':
            return await self.inner.handle_async_request(request)
        self.calls += 1
        directory = self.directory / f'call-{self.calls:03d}'
        directory.mkdir(parents=True, exist_ok=False)
        body = json.loads(await request.aread())
        atomic(directory/'request.json', body)
        atomic(directory/'transport.json', {'started': time.time(), 'url': str(request.url),
                                          'timeouts': request.extensions.get('timeout')})
        if self.expected and self.calls <= len(self.expected):
            expected = self.expected[self.calls-1]
            matches = {k: body.get(k) == expected.get(k) for k in ('model', 'messages', 'format', 'think', 'options', 'keep_alive')}
            atomic(directory/'prior-request-match.json', matches)
            # Later workflow content can legitimately include newly generated prior packets.
            strict = self.calls == 1
            invariant = ('model', 'format', 'think', 'options', 'keep_alive')
            same_system = body['messages'][0] == expected['messages'][0]
            def normalize(value):
                # Frozen source snapshot omits generated __pycache__ directory entries.
                # Only deterministic coverage metadata may differ on the first workflow prompt.
                if isinstance(value, dict):
                    return {k:normalize(v) for k,v in value.items() if k!='entries_seen'}
                if isinstance(value, list):
                    return [normalize(v) for v in value]
                if isinstance(value, str):
                    try:
                        parsed=json.loads(value)
                    except ValueError:
                        return value
                    if isinstance(parsed,(dict,list)):
                        return normalize(parsed)
                return value
            coverage_only = normalize(body['messages']) == normalize(expected['messages'])
            atomic(directory/'comparison.json', {'exact_messages':matches['messages'],
                'equal_except_frozen_search_entry_count':coverage_only,
                'later_workflow_content_can_depend_on_new_answers':not strict})
            if not all(matches[k] for k in invariant) or not same_system or (strict and not coverage_only):
                raise RuntimeError('Frozen request differs from recorded baseline: ' + str(matches))
        try:
            response = await self.inner.handle_async_request(request)
            atomic(directory/'http.json', {'status': response.status_code, 'received_at': time.time()})
            if response.status_code != 200:
                raw = await response.aread()
                (directory/'http-error.txt').write_bytes(raw)
                return httpx.Response(response.status_code, content=raw)
            return httpx.Response(response.status_code, headers=response.headers,
                stream=CaptureStream(response.stream, directory, self.progress), extensions=response.extensions)
        except BaseException as error:
            atomic(directory/'transport-error.json', {'type': type(error).__name__, 'error': str(error), 'time': time.time()})
            raise

    async def aclose(self):
        await self.inner.aclose()
