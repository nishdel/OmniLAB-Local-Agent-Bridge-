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
    if row['remote']:
        raise SelectionError('This model routes to cloud weights; local-only jobs cannot use it.')
    capabilities = row.get('capabilities')
    if capabilities is not None and required not in capabilities:
        raise SelectionError(f'Model does not advertise required capability: {required}')
    return dict(row)


async def discover(config, transport=None):
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
