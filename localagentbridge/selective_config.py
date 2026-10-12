"""Trusted controller policy, never interpreted from a model response."""
import math
from .inference import local_origin


def validate_policy(value):
    if not isinstance(value, dict):
        raise ValueError('selective must be a table')
    allowed = {'enabled', 'implementation_enabled', 'pilot_enabled', 'pilot_categories',
               'qualified', 'scoped_task_approvals', 'capability_evidence', 'providers', 'sandbox', 'memory_plan',
               'defaults', 'model_profiles', 'project_root', 'host_limits'}
    if set(value) - allowed:
        raise ValueError('Unknown selective policy fields')
    for key in ('enabled', 'implementation_enabled', 'pilot_enabled'):
        if key in value and type(value[key]) is not bool:
            raise ValueError(key + ' must be boolean')
    approvals = value.get('scoped_task_approvals', [])
    if not isinstance(approvals, list) or len(approvals) > 20 or any(not isinstance(h, str) or len(h) != 64 or any(c not in '0123456789abcdef' for c in h) for h in approvals):
        raise ValueError('Scoped approvals require exact contract SHA-256 identities')
    for backend, provider in value.get('providers', {}).items():
        if backend not in ('ollama', 'strata') or not isinstance(provider, dict):
            raise ValueError('Unknown provider')
        if set(provider) - {'enabled', 'endpoint', 'binding', 'api_key_env', 'temperature', 'reasoning_effort', 'verify_loaded_context', 'native_context', 'num_gpu', 'keep_alive_seconds', 'strict_context', 'draft_num_predict', 'runtime_binding', 'enable_thinking'}:
            raise ValueError('Unknown provider setting')
        if 'enabled' in provider and type(provider['enabled']) is not bool:
            raise ValueError('Provider enabled must be boolean')
        if 'enable_thinking' in provider and (backend != 'strata' or type(provider['enable_thinking']) is not bool):
            raise ValueError('enable_thinking requires a Strata boolean setting')
        if provider.get('runtime_binding') and (backend != 'ollama' or not provider.get('native_context') or not provider.get('verify_loaded_context')):
            raise ValueError('Effective runtime binding requires verified native Ollama transport')
        for key, low, high in (('num_gpu', 0, 256), ('keep_alive_seconds', 0, 1800), ('draft_num_predict', 0, 16)):
            if key in provider and (backend != 'ollama' or not provider.get('native_context') or type(provider[key]) is not int or not low <= provider[key] <= high):
                raise ValueError('Invalid scoped native Ollama ' + key)
        if 'strict_context' in provider and (backend != 'ollama' or not provider.get('native_context') or type(provider['strict_context']) is not bool):
            raise ValueError('Strict context requires native Ollama')
        if 'temperature' in provider and (type(provider['temperature']) not in (int, float) or not 0 <= provider['temperature'] <= 2):
            raise ValueError('temperature must be between zero and two')
        if provider.get('native_context') and provider.get('reasoning_effort') is not None:
            raise ValueError('Native non-thinking profile does not support reasoning_effort')
        if 'reasoning_effort' in provider and provider['reasoning_effort'] not in ('low', 'medium', 'high'):
            raise ValueError('Invalid reasoning_effort')
        if 'native_context' in provider and (backend != 'ollama' or type(provider['native_context']) is not bool):
            raise ValueError('Native scoped context requires an Ollama boolean setting')
        if 'verify_loaded_context' in provider and (backend != 'ollama' or type(provider['verify_loaded_context']) is not bool):
            raise ValueError('Loaded context verification requires an Ollama boolean setting')
        if 'endpoint' in provider:
            local_origin(provider['endpoint'])
    defaults = value.get('defaults', {})
    if not isinstance(defaults, dict) or set(defaults) - {'model','backend'}:
        raise ValueError('Invalid project model defaults')
    if defaults and (not defaults.get('model') or defaults.get('backend') not in ('ollama','strata')):
        raise ValueError('Defaults require exact model and backend')
    profiles = value.get('model_profiles', [])
    seen = set()
    for profile in profiles:
        if set(profile) - {'model','backend','identity','limits','provider'} or not all(profile.get(k) for k in ('model','backend','identity','limits')):
            raise ValueError('Invalid qualified model profile')
        key = (profile['backend'],profile['model'])
        if key in seen:
            raise ValueError('Duplicate model/backend profile')
        seen.add(key)
        from .task_contract import TaskLimits
        TaskLimits.model_validate(profile['limits'])
        validate_policy({'providers':{profile['backend']:profile.get('provider',{})}})
    if defaults and (defaults['backend'], defaults['model']) not in seen:
        raise ValueError('Default requires a qualified model profile')
    host = value.get('host_limits', {})
    required = {'minimum_available_before_bytes','hard_available_bytes','sustained_available_bytes',
                'sustained_seconds','maximum_gpu_mib'}
    if host and (set(host) != required or any(type(v) not in (int,float) or not math.isfinite(v) or v <= 0 for v in host.values())):
        raise ValueError('Host limits require all positive measured ceilings')
    if host and not host['hard_available_bytes'] <= host['sustained_available_bytes'] <= host['minimum_available_before_bytes']:
        raise ValueError('Invalid host headroom ordering')
    strata = value.get('providers', {}).get('strata', {})
    if strata.get('enabled') and strata.get('binding', {}).get('family') != 'coder':
        raise ValueError('Initial Strata support requires an explicitly configured Coder family binding')
    return value
