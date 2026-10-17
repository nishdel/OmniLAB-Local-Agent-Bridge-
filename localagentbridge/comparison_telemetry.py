"""Explicit read-only benchmark sampling; never starts a monitoring service.

Prefer an already-running LaptopPower status export for power. Its estimates and
subtotal are deliberately ignored. NVML/nvidia-smi board power is an alternative,
not another stream to add to the same GPU. CPU probes/drivers are not invoked.
"""
import csv
import json
import os
from pathlib import Path
import subprocess
import time

import psutil

from .comparison import number, energy


def laptop_power(path, now=None, max_age=25):
    now = time.time() if now is None else now
    value = json.loads(Path(path).read_text(encoding='utf-8-sig'))
    stamp = value.get('timestamp')
    if not number(stamp) or not 0 <= now-stamp <= max_age:
        raise ValueError('Existing power monitor export is stale or has an invalid clock')
    rows = []
    for key, reading in value.get('components', {}).items():
        kind = reading.get('kind')
        if kind not in ('cpu', 'egpu', 'internal_gpu'):
            continue
        watts = reading.get('watts')
        rows.append(dict(timestamp=stamp, clock='utc_only', units='W',
            source='LaptopPower:'+str(reading.get('provider')), device=key,
            domain='cpu_package' if kind == 'cpu' else 'gpu_board',
            watts=watts if number(watts) and not reading.get('error') else None,
            # Sensor reading generation is a sample sequence, not a restart ID.
            generation=value.get('started'), limitation=reading.get('error')))
    return rows


def sample(*, power_status=None, run=subprocess.run):
    stamp, monotonic = time.time(), time.monotonic()
    memory = psutil.virtual_memory()
    disk = psutil.disk_io_counters()
    resources = dict(timestamp=stamp, monotonic_seconds=monotonic,
                     host_used_bytes=memory.total-memory.available,
                     available_ram_bytes=memory.available, gpu_used_mib=None,
                     disk_read_bytes=disk.read_bytes if disk else None,
                     disk_write_bytes=disk.write_bytes if disk else None,
                     scope='whole host; disk counters include unrelated activity')
    power, error = [], None
    try:
        response = run(['nvidia-smi', '--query-gpu=uuid,memory.used,power.draw',
                        '--format=csv,noheader,nounits'], stdin=subprocess.DEVNULL,
                       capture_output=True, text=True, timeout=8,
                       creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        if response.returncode:
            raise ValueError('nvidia-smi read-only query failed')
        gpu_memory = []
        for device, used, watts in csv.reader(response.stdout.splitlines(), skipinitialspace=True):
            gpu_memory.append(float(used))
            try:
                watts = float(watts)
            except ValueError:
                watts = None
            power.append(dict(timestamp=stamp, monotonic_seconds=monotonic, units='W',
                source='nvidia-smi:power.draw', domain='gpu_board', device=device,
                watts=watts if number(watts) else None, generation=None))
        resources['gpu_used_mib'] = sum(gpu_memory) if gpu_memory else None
    except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
        error = type(exc).__name__ + ': ' + str(exc)
    if power_status is not None:
        # Explicit source selection: never silently fill a failed CPU/GPU sensor
        # with a different boundary or add simultaneous duplicate GPU streams.
        try:
            power = laptop_power(power_status)
        except (OSError, ValueError) as exc:
            power, error = [], type(exc).__name__ + ': ' + str(exc)
    return dict(resources=resources, power=power, error=error,
                whole_system_wall_watts=None, cpu_probe_started=False)


def capture(path, seconds, *, interval=2, power_status=None, maximum_bytes=8*1024*1024):
    if not 0 < seconds <= 1800 or not 1 <= interval <= 10:
        raise ValueError('Sampling is bounded to 1800 seconds, interval 1..10 seconds')
    started = time.monotonic()
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as stream:
        while True:
            row = sample(power_status=power_status)
            raw = json.dumps(row, allow_nan=False)+'\n'
            if stream.tell()+len(raw.encode()) > maximum_bytes:
                raise ValueError('Sampling evidence storage limit reached')
            stream.write(raw)
            stream.flush()
            if time.monotonic()-started >= seconds:
                break
            time.sleep(max(0, min(interval, seconds-(time.monotonic()-started))))
    return {'path': str(path), 'seconds': time.monotonic()-started,
            'boundary': 'local client and machine only; not cloud datacenter',
            'pid': os.getpid()}


def summarize(rows, start, end, max_gap=5, idle_watts=None):
    """Report observed whole-host peaks and disjoint per-device energy streams."""
    if end <= start:
        raise ValueError('Invalid telemetry boundary')
    resources = sorted([r['resources'] for r in rows if start <= r['resources']['timestamp'] <= end],
                       key=lambda r: r['timestamp'])
    def peak(field, minimum=False):
        values = [r[field] for r in resources if number(r.get(field))]
        return (min(values) if minimum else max(values)) if values else None
    def delta(field):
        values = [r.get(field) for r in resources]
        if len(values)<2 or not all(number(v) for v in values) or any(a>b for a,b in zip(values,values[1:])):
            return None
        return values[-1]-values[0]
    streams = {(p['source'],p['domain'],p['device']) for r in rows for p in r.get('power',[])}
    energies = []
    for source, domain, device in sorted(streams):
        samples = [p for r in rows for p in r.get('power',[])
                   if (p['source'],p['domain'],p['device']) == (source,domain,device)]
        # A failed sample explicitly breaks interpolation even when the next
        # successful sample arrives inside max_gap.
        for r in rows:
            if not any((p['source'],p['domain'],p['device']) == (source,domain,device)
                       for p in r.get('power',[])):
                samples.append(dict(timestamp=r['resources']['timestamp'], source=source, domain=domain,
                    device=device, units='W', watts=None, clock='utc_only', generation=None))
        energies.append(energy(samples,start,end,max_gap_seconds=max_gap,
                               idle_watts=(idle_watts or {}).get(device)))
    return dict(resources=dict(peak_ram_bytes=peak('host_used_bytes'),
                minimum_available_ram_bytes=peak('available_ram_bytes',True),
                peak_vram_mib=peak('gpu_used_mib'), disk_read_bytes=delta('disk_read_bytes'),
                disk_write_bytes=delta('disk_write_bytes'), scope='whole host; unrelated loads included',
                coverage={'samples':len(resources), 'first':resources[0]['timestamp'] if resources else None,
                          'last':resources[-1]['timestamp'] if resources else None,
                          'limitation':'Sampled peaks can miss transients; disk deltas cover first through last resource sample only.'}),
                energy=energies, errors=[r['error'] for r in rows if r.get('error')])
