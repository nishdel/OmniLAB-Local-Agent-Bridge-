"""Owned-process identities, kernel locks and Windows job containment.

Extracted from the protected independent benchmark worker. Shared by the
companion; never signals a process selected by executable name or PID alone.
"""
import ctypes
import os
from pathlib import Path
import subprocess
import psutil

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


