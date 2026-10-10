"""Trusted, project-scoped defaults; explicit selections retain their identity."""
from copy import deepcopy
from pathlib import Path
from .task_contract import Contract, TaskLimits

def resolve_contract(config, value, selected_model=None):
    raw = value.model_dump(exclude_unset=True) if isinstance(value, Contract) else deepcopy(value)
    policy = config.selective
    defaults = policy.get('defaults', {})
    root = policy.get('project_root')
    if root and Path(raw['repository']).resolve() != Path(root).resolve():
        raise ValueError('Personal local profile is scoped to its configured project')
    explicit_model = raw.get('model')
    raw.setdefault('backend', defaults.get('backend', 'ollama'))
    if not explicit_model:
        if raw['backend'] != defaults.get('backend','ollama'):
            raise ValueError('Explicit backend override requires an explicit model')
        raw['model'] = (selected_model if raw['backend']=='ollama' else None) or defaults.get('model', config.model)
    matches = [p for p in policy.get('model_profiles', []) if
               p['model'] == raw['model'] and p['backend'] == raw['backend']]
    if matches:
        profile = matches[0]
        if raw.get('exact_identity') is None:
            raw['exact_identity'] = profile['identity']
        supplied = raw.get('limits', {})
        limits = profile.get('limits', {}) | supplied
        # A per-job override may narrow a qualified profile, never enlarge it.
        approved = TaskLimits.model_validate(profile.get('limits', {})).model_dump()
        for key in ('output_tokens', 'output_bytes', 'steps', 'self_repair_cycles', 'transport_retries',
                    'attempt_seconds', 'test_seconds', 'memory_mb', 'cpus', 'snapshot_bytes', 'implementation_attempts'):
            if approved.get(key) is not None and key in limits and (limits[key] is None or limits[key] > approved[key]):
                raise ValueError('Job exceeds qualified profile: ' + key)
        if limits.get('context_tokens') != approved.get('context_tokens'):
            raise ValueError('Context change requires separate qualification')
        if limits.get('context_safety_tokens',approved['context_safety_tokens']) < approved['context_safety_tokens']:
            raise ValueError('Job reduces the qualified context safety margin')
        raw['limits'] = limits
    return Contract.model_validate(raw)

def provider_settings(policy, contract):
    settings = deepcopy(policy.get('providers', {}).get(contract.backend, {}))
    for profile in policy.get('model_profiles', []):
        if (profile['backend'], profile['model']) == (contract.backend, contract.model):
            if contract.exact_identity != profile['identity']:
                raise ValueError('Selected identity differs from the qualified profile')
            settings.update(profile.get('provider', {}))
            break
    return settings
