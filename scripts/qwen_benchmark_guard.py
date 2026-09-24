"""Benchmark-only workload ownership. Names select candidates, never grant ownership."""
import time
import os

import psutil

from qwen_benchmark_io import append, process_filetime


def model_name(name):
    name = (name or '').lower()
    return name.startswith(('ollama', 'llama-server')) or name in (
        'lm studio.exe', 'lmstudio.exe', 'llama-cli.exe')


def observe(pid):
    """Fresh objects avoid psutil process_iter's identity/metadata cache."""
    p = psutil.Process(pid)
    created = p.create_time()
    native = process_filetime(pid) if os.name=='nt' else None
    result = dict(pid=pid, created=created, name=p.name(), exe=p.exe(), ppid=p.ppid())
    if native is not None:
        result['created_filetime'] = native
    if ((native is not None and process_filetime(pid)!=native) or
            psutil.Process(pid).create_time() != created):
        raise RuntimeError('PID replaced during observation')
    return result


def ancestry(row, probe=observe):
    chain, current, seen = [], row, {row['pid']}
    while current.get('ppid'):
        pid = current['ppid']
        if pid in seen:
            return chain, 'ancestry cycle'
        seen.add(pid)
        try:
            parent = probe(pid)
        except psutil.NoSuchProcess:
            chain.append({'pid':pid,'created':None,'error':'parent exited'})
            return chain, 'parent exited'
        except psutil.AccessDenied:
            chain.append({'pid':pid,'created':None,'error':'access denied'})
            return chain, 'parent access denied'
        except (psutil.Error, RuntimeError, OSError) as error:
            return chain, type(error).__name__
        chain.append(parent)
        if parent['created'] > current['created']:
            return chain, 'parent PID reused; ancestry not trusted'
        current = parent
        if len(chain) >= 64:
            return chain, 'ancestry depth limit'
    return chain, None


def inspect_candidate(pid, runtime=None, probe=observe):
    row = {'observed_at':time.time(), 'pid':pid, 'created':None, 'exe':None,
           'ancestry':[], 'classification':'unresolved'}
    try:
        candidate = probe(pid)
        row.update(candidate)
        row['ancestry'], row['ancestry_note'] = ancestry(candidate, probe)
        if not model_name(candidate['name']):
            row.update(classification='vanished', reason='Candidate PID now names a non-model process')
            return row
        if runtime is None:
            # No benchmark runtime exists: a stable live model process is external.
            owned = False
        else:
            # Membership is checked on a pinned Windows handle with matching creation time.
            owned = runtime.contains(candidate)
        fresh = probe(pid)
        if (fresh['created'] != candidate['created'] or fresh['exe'] != candidate['exe'] or
                fresh.get('created_filetime') != candidate.get('created_filetime')):
            row['reason'] = 'PID identity changed during classification'
        else:
            row.update(classification='owned' if owned else 'external',
                       reason='Verified benchmark Job Object membership' if owned else
                              'Verified outside benchmark Job Object' if runtime else
                              'Stable model process exists before benchmark runtime launch')
    except psutil.NoSuchProcess:
        row.update(classification='vanished', reason='Process exited during inspection')
    except psutil.AccessDenied:
        row['reason'] = 'Access denied; ownership not established'
    except (psutil.Error, OSError, RuntimeError) as error:
        row['reason'] = type(error).__name__ + ': ownership could not be established'
    return row


def workloads(runtime=None, evidence=None, enumerate_processes=None, probe=observe):
    """Recheck suspected conflicts. Unresolved model ownership blocks safely, without killing it."""
    source = enumerate_processes or (lambda: psutil.process_iter(['pid', 'name']))
    blocked = []
    try:
        candidates = list(source())
    except psutil.Error as error:
        candidates = []
        row = dict(observed_at=time.time(), pid=None, created=None, exe=None, ancestry=[],
                   classification='unresolved', reason='Process enumeration failed: '+type(error).__name__)
        if evidence:
            append(evidence, row)
        return [row]
    for p in candidates:
        info = p if isinstance(p, dict) else p.info
        # Unknown enumeration names require fresh inspection too, never silent permission.
        if info.get('name') is not None and not model_name(info.get('name')):
            continue
        first = inspect_candidate(info['pid'], runtime, probe)
        if first['classification'] in ('external', 'unresolved'):
            last = inspect_candidate(info['pid'], runtime, probe)
            last['revalidated'] = True
            last['first_observation'] = first
            # A replacement is not confirmed external based on the original candidate.
            if (first.get('created') is not None and last.get('created') is not None
                    and first['created'] != last['created'] and last['classification']=='external'):
                last.update(classification='unresolved', reason='Candidate PID reused across revalidation')
        else:
            last = first
        if evidence:
            append(evidence, last)
        if last['classification'] in ('external', 'unresolved'):
            blocked.append(last)
    return blocked
