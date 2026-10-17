"""Conservative measured admission; no model loading, unloading or hardware assumptions."""
import psutil
import httpx

from .inference import local_origin


def memory_admission(contract, policy, total_mb=None, available_mb=None):
    if (contract.override_lane or contract.requested_lane) != 'local_implementation':
        return True, None
    memory = psutil.virtual_memory()
    total_mb = memory.total / 1048576 if total_mb is None else total_mb
    available_mb = memory.available / 1048576 if available_mb is None else available_mb
    plan = policy.get('memory_plan', {})
    fields = ('os_and_apps_mb', 'lab_mb', 'runtime_mb', 'context_cache_mb', 'headroom_mb')
    if not plan.get('supervisor_verified') or any(type(plan.get(k)) not in (int, float) or plan[k] <= 0 for k in fields):
        return False, 'A measured combined memory plan is required'
    total = sum(plan[k] for k in fields) + contract.limits.memory_mb
    if total > total_mb or contract.limits.memory_mb + plan['headroom_mb'] > available_mb:
        return False, 'Combined OS/LAB/runtime/context/sandbox memory exceeds available resources'
    return True, None


async def competing_runtime(contract, policy, transport=None):
    """Never unload someone else's model. A resident competitor needs operator action."""
    async with httpx.AsyncClient(trust_env=False, follow_redirects=False, transport=transport,
                                 timeout=httpx.Timeout(5, connect=3)) as client:
        for backend, provider in policy.get('providers', {}).items():
            if not provider.get('enabled', backend == 'ollama'):
                if not provider.get('endpoint'):
                    continue
                from urllib.parse import urlsplit
                port = urlsplit(local_origin(provider['endpoint'])).port
                if not any(c.status == psutil.CONN_LISTEN and c.laddr.port == port
                           for c in psutil.net_connections(kind='tcp')):
                    continue
            origin = local_origin(provider['endpoint'])
            try:
                if backend == 'ollama':
                    response = await client.get(origin + '/api/ps')
                    response.raise_for_status()
                    rows = response.json().get('models')
                    if not isinstance(rows, list):
                        raise ValueError('Cannot verify resident Ollama models')
                    if any(contract.backend != 'ollama' or row.get('name') != contract.model for row in rows):
                        return 'Another Ollama model is resident; manually release it before changing providers/models'
                elif backend == 'strata' and contract.backend != 'strata':
                    response = await client.get(origin + '/health')
                    response.raise_for_status()
                    if response.json().get('loaded'):
                        return 'Strata is resident; manually release it before starting Ollama inference'
            except httpx.ConnectError:
                if backend == contract.backend:
                    raise
                # No listener on the configured alternate origin is not a loaded competitor.
                continue
        return None

class HostGuard:
    """Sample whole-host pressure independently of inference; never kill host processes."""
    def __init__(self, limits, path, sample=None, clock=None):
        import time
        self.limits, self.path = limits, path
        self.enabled = bool(limits)
        self.sample = sample or host_sample
        self.clock = clock or time.monotonic
        self.low_since = None

    def check(self, admission=False):
        import json
        if not self.enabled:
            return
        row = self.sample()
        now = self.clock()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path.exists() and self.path.stat().st_size > 8*1024*1024:
            raise ValueError('Resource evidence storage ceiling reached')
        with self.path.open('a', encoding='utf-8') as stream:
            stream.write(json.dumps(row)+'\n')
        available = row['host_available']
        if admission and available < self.limits['minimum_available_before_bytes']:
            raise ValueError('Insufficient whole-host RAM before admission')
        if available < self.limits['hard_available_bytes']:
            raise ValueError('Hard whole-host RAM pressure stop')
        if available < self.limits['sustained_available_bytes']:
            self.low_since = now if self.low_since is None else self.low_since
            if now-self.low_since >= self.limits['sustained_seconds']:
                raise ValueError('Sustained whole-host RAM pressure stop')
        else:
            self.low_since = None
        if not row['gpu_used_mib']:
            raise ValueError('GPU diagnostics unavailable; no CPU fallback')
        if any(v > self.limits['maximum_gpu_mib'] for v in row['gpu_used_mib']):
            raise ValueError('Whole-host GPU memory ceiling reached')
        return row

    async def watch(self):
        import asyncio
        while True:
            await asyncio.sleep(2)
            await asyncio.to_thread(self.check)

def host_sample():
    import subprocess
    import time
    memory = psutil.virtual_memory()
    result = subprocess.run(['nvidia-smi','--query-gpu=memory.used','--format=csv,noheader,nounits'],
                            stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=8,
                            creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    if result.returncode:
        raise ValueError('GPU diagnostic failure')
    try:
        gpu = [int(v.strip()) for v in result.stdout.splitlines() if v.strip()]
    except ValueError:
        raise ValueError('GPU diagnostic output is invalid') from None
    return {'time':time.time(),'host_total':memory.total,'host_available':memory.available,'gpu_used_mib':gpu}
