"""Installed inventory and exact selection. No downloads, probes or substitutions."""
import re
import time
import httpx


class SelectionError(ValueError):
    pass


def remote_model(tag, show):
    # GPT-OSS correction reviewed against both documented Ollama metadata sources.
    return any(d.get(k) for d in (tag, show) for k in ('remote_host', 'remote_model'))


def select_model(rows, name, required='completion'):
    row = next((r for r in rows if r['name'] == name), None)
    if row is None:
        raise SelectionError('Selected model is missing; refresh inventory. No substitute was used.')
    if row.get('selectable') is False:
        raise SelectionError(row.get('reason') or 'Provider/model is disabled, unavailable or unqualified; no substitute was used')
    if row['remote']:
        raise SelectionError('This model routes to cloud weights; local-only jobs cannot use it.')
    capabilities = row.get('capabilities')
    if capabilities is not None and required not in capabilities:
        raise SelectionError(f'Model does not advertise required capability: {required}')
    return dict(row)


async def discover_ollama(config, transport=None):
    async with httpx.AsyncClient(trust_env=False, follow_redirects=False,
                                timeout=httpx.Timeout(15, connect=5), transport=transport) as client:
        response = await client.get(config.endpoint + '/api/tags')
        response.raise_for_status()
        models = response.json().get('models')
        if not isinstance(models, list):
            raise SelectionError('Invalid Ollama inventory')
        rows = []
        for item in models:
            name = item.get('name', '')
            if not isinstance(name, str) or not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9._:/-]{0,159}', name):
                raise SelectionError('Invalid model name in inventory')
            details = await client.post(config.endpoint + '/api/show', json={'model': name})
            details.raise_for_status()
            show = details.json()
            capabilities = show.get('capabilities')
            if capabilities is not None and (not isinstance(capabilities, list) or
                                            not all(isinstance(v, str) for v in capabilities)):
                raise SelectionError('Invalid model capabilities')
            remote = remote_model(item, show) or name.lower().endswith(':cloud')
            rows.append(dict(name=name, digest=item.get('digest'), size=item.get('size'),
                             details=item.get('details', {}), capabilities=capabilities, remote=remote,
                             validation='incompatible' if remote or capabilities is not None and 'completion' not in capabilities
                             else 'untested', observed_at=time.time()))
        return rows


def selection_pair(value):
    if value and value.startswith('strata::'):
        return 'strata', value[len('strata::'):]
    return 'ollama', value


async def provider_status(config, backend, model=None, transport=None):
    """Read-only diagnostics. Never load weights, run inference or qualify a model."""
    from .inference import ChatProvider
    policy = config.selective
    settings = dict(policy.get('providers', {}).get(backend, {}))
    if backend == 'ollama':
        settings.setdefault('endpoint', config.endpoint)
    profile = next((p for p in policy.get('model_profiles', []) if
                    (p['backend'],p['model']) == (backend,model)), None)
    if profile:
        settings.update(profile.get('provider', {}))
    enabled = settings.get('enabled', backend == 'ollama')
    status = {'backend':backend, 'enabled':enabled, 'endpoint':settings.get('endpoint'),
              'model':model, 'installed':None, 'compatible':False, 'qualified':False,
              'ready':False, 'identity_verified':False, 'selectable':False}
    if not enabled:
        return status | {'reason':'Provider is disabled; explicit configuration and live qualification required'}
    try:
        provider = ChatProvider(backend, settings, transport)
        if model is None:
            models = await provider.list_models() if backend == 'strata' else [r['name'] for r in await discover_ollama(config, transport)]
            return status | {'models':models, 'reason':'Listed names are not verified weight identities; inspect an exact model'}
        observed = await provider.inspect(model)
        status.update(observed)
        status['installed'] = observed['ready'] and observed['identity_verified']
        status['compatible'] = status['installed']
        status['qualified'] = bool(profile and observed['identity'] == profile['identity'] and any(
            q[:2] == [backend, profile['identity']] and q[3] == profile['limits'].get('context_tokens')
            for q in policy.get('qualified', []) if isinstance(q, list) and len(q) == 4))
        # A saved selector chooses future jobs, so require a reviewed profile. A
        # supervisor can still admit an explicit scoped qualification contract.
        status['selectable'] = bool(policy.get('enabled') and profile and status['installed'] and status['qualified'])
        if not status['selectable']:
            status['reason'] = observed.get('reason') or observed.get('identity_uncertainty') or 'Exact model profile is unqualified or selective execution is disabled'
    except (ValueError, OSError, httpx.HTTPError) as error:
        status['reason'] = type(error).__name__ + ': ' + str(error)
    return status


async def discover(config, transport=None):
    profiles = [p for p in config.selective.get('model_profiles', []) if p['backend'] == 'strata']
    try:
        rows = await discover_ollama(config, transport)
    except (ValueError, OSError, httpx.HTTPError):
        if not profiles:
            raise
        rows = []
    for row in rows:
        row.setdefault('backend', 'ollama')
    for profile in profiles:
        status = await provider_status(config, 'strata', profile['model'], transport)
        rows.append(dict(name='strata::'+profile['model'], model=profile['model'], backend='strata',
            digest=status.get('identity'), remote=False, size=None, details={},
            capabilities=['completion'] + (['tools'] if status.get('tools_advertised') else []),
            validation='qualified' if status['qualified'] else 'unqualified', observed_at=time.time(),
            **{k:status[k] for k in ('installed','compatible','qualified','enabled','selectable')},
            reason=status.get('reason'), runtime_status=status))
    return rows
