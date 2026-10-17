"""Read-only verification of the actual local inference runner."""
import hashlib
from pathlib import Path
import psutil

def runner_evidence(binding, limits, processes=None):
    required = binding.get('runner_flags', {})
    if not required or not binding.get('runner_model'):
        raise ValueError('Effective runtime requires an exact runner model and flags')
    candidates = []
    for process in processes if processes is not None else psutil.process_iter():
        try:
            args = process.cmdline()
            if args and Path(args[0]).name.lower() == binding.get('runner_executable', 'llama-server.exe').lower():
                def flag(key):
                    return args[args.index(key)+1] if key in args and args.index(key)+1 < len(args) else None
                if flag('--model') == binding['runner_model']:
                    observed = {key: flag(key) for key in required}
                    if any(observed[k] != str(v) for k,v in required.items()):
                        raise ValueError('Effective runner setting differs from approved profile')
                    candidates.append({'pid':process.pid, 'created':process.create_time(),
                                       'executable':process.exe(), 'flags':observed,
                                       'model_path':flag('--model')})
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    if len(candidates) != 1:
        raise ValueError('Exactly one verified qualified runner is required; no CPU/other-model fallback')
    if str(required.get('-c', required.get('--ctx-size'))) != str(limits.context_tokens):
        raise ValueError('Runner context differs from task capacity')
    return candidates[0]

def template_identity(value):
    return hashlib.sha256(value.encode('utf-8')).hexdigest()
