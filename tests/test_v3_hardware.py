from types import SimpleNamespace
import sys
from localagentbridge.hardware import HardwareSampler


def test_opt_in_ram_sampler_includes_actual_ollama_runner(monkeypatch):
    rows=[dict(pid=1,ppid=0,name='ollama.exe',memory_info=SimpleNamespace(rss=100)),
          dict(pid=2,ppid=1,name='llama-server.exe',memory_info=SimpleNamespace(rss=1000)),
          dict(pid=3,ppid=99,name='unrelated.exe',memory_info=SimpleNamespace(rss=5000))]
    fake=SimpleNamespace(process_iter=lambda attrs:[SimpleNamespace(info=r) for r in rows],
                         virtual_memory=lambda:SimpleNamespace(total=10000,available=2000),Error=RuntimeError)
    monkeypatch.setitem(sys.modules,'psutil',fake)
    monkeypatch.setattr('localagentbridge.hardware.shutil.which',lambda name:None)
    values=HardwareSampler('http://127.0.0.1:11434','model').local_sample()
    assert values['peak_ollama_rss_bytes_sampled']==1100
    assert values['peak_system_used_bytes_sampled']==8000
