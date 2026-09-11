"""Opt-in benchmark sampling; no polling or subprocesses during normal service use."""
import asyncio
import os
import shutil
import subprocess
import httpx


class HardwareSampler:
    def __init__(self, endpoint, model):
        self.endpoint, self.model = endpoint, model
        self.stop = asyncio.Event()
        self.values = {'samples':0,'peak_ollama_rss_bytes_sampled':None,
                       'peak_system_used_bytes_sampled':None,'peak_gpu_used_mib_sampled':None,
                       'model_allocation_bytes':None,'model_vram_bytes':None,
                       'process_scope':'Ollama processes and descendants, including llama-server.exe'}

    def local_sample(self):
        values = {}
        try:
            import psutil
        except ImportError:
            psutil = None
        try:
            if psutil is None:
                raise OSError('Optional psutil is unavailable')
            processes = [p.info for p in psutil.process_iter(['pid','ppid','name','memory_info'])]
            selected = {p['pid'] for p in processes if (p['name'] or '').lower().startswith('ollama')}
            for _ in range(4):
                selected.update(p['pid'] for p in processes if p['ppid'] in selected)
            rss = [p['memory_info'].rss for p in processes if p['pid'] in selected and p['memory_info']]
            values['peak_ollama_rss_bytes_sampled'] = sum(rss) if rss else None
            values['peak_system_used_bytes_sampled'] = psutil.virtual_memory().total - psutil.virtual_memory().available
        except (OSError, psutil.Error if psutil else OSError):
            pass
        path = shutil.which('nvidia-smi')
        if path:
            try:
                proc = subprocess.run([path,'--query-gpu=memory.used','--format=csv,noheader,nounits'],
                    capture_output=True,text=True,timeout=3,creationflags=0x08000000 if os.name=='nt' else 0)
                values['peak_gpu_used_mib_sampled'] = sum(int(line) for line in proc.stdout.splitlines()) or None
            except (ValueError,OSError,subprocess.TimeoutExpired):
                pass
        return values

    async def sample(self):
        from .routing import canonical
        async with httpx.AsyncClient(trust_env=False,timeout=3) as client:
            while not self.stop.is_set():
                sample = await asyncio.to_thread(self.local_sample)
                try:
                    response = await client.get(self.endpoint+'/api/ps')
                    for row in response.json().get('models',[]):
                        if canonical(row['name']) == canonical(self.model):
                            sample['model_allocation_bytes'] = row.get('size')
                            sample['model_vram_bytes'] = row.get('size_vram')
                except (httpx.HTTPError,ValueError,KeyError):
                    pass
                for key,value in sample.items():
                    if value is not None:
                        self.values[key] = max(self.values[key] or 0,value)
                self.values['samples'] += 1
                try:
                    await asyncio.wait_for(self.stop.wait(),timeout=1)
                except TimeoutError:
                    pass

    async def __aenter__(self):
        self.task = asyncio.create_task(self.sample())
        return self

    async def __aexit__(self,*args):
        self.stop.set()
        await self.task
