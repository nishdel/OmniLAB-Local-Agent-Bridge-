"""Observed values, estimates and unavailable metrics are explicitly distinct."""
import json
import math

from .companion_store import encode

PHASES = {'planning', 'handoff', 'queue', 'model_loading', 'local_inference', 'review', 'repair',
          'verification', 'integration', 'end_to_end', 'operator'}
METRICS = {'cloud_input_tokens', 'cloud_cached_input_tokens', 'cloud_output_tokens', 'local_input_tokens',
           'local_output_tokens', 'elapsed_seconds', 'retries', 'corrections', 'accepted', 'interventions'}


def record(store, job_id, key, phase, metrics, kind, evidence):
    if phase not in PHASES or kind not in ('observed','estimated','unavailable') or not evidence.strip():
        raise ValueError('Measurement requires known phase, provenance and evidence')
    if not key or len(key)>160 or not isinstance(metrics,dict) or not metrics or set(metrics)-METRICS:
        raise ValueError('Invalid measurement key/metrics')
    for value in metrics.values():
        if value is not None and (type(value) not in (int,float) or value<0 or not math.isfinite(value)):
            raise ValueError('Invalid measurement value')
        if kind=='unavailable' and value is not None:
            raise ValueError('Unavailable metrics cannot contain invented values')
    payload=encode({'phase':phase,'metrics':metrics,'kind':kind,'evidence':evidence})
    with store.db() as db:
        db.execute('BEGIN IMMEDIATE')
        if not db.execute('SELECT 1 FROM jobs WHERE id=?',(job_id,)).fetchone():
            raise ValueError('Unknown measurement job')
        old=db.execute('SELECT payload FROM task_measurements WHERE job_id=? AND key=?',(job_id,key)).fetchone()
        if old and old[0]!=payload:
            raise ValueError('Measurement identity already recorded differently')
        db.execute('INSERT OR IGNORE INTO task_measurements VALUES(?,?,?,?)',
                   (job_id,key,store.clock(),payload))


def summary(store, job_id):
    with store.db() as db:
        values=[json.loads(r[0]) for r in db.execute('SELECT payload FROM task_measurements WHERE job_id=?',(job_id,))]
    return values

def local_usage(store, job, request_id, answer, started, duration, status='ok'):
    """One provider receipt in the existing usage table; measurements are a separate view."""
    from .telemetry import Store
    c = job['request']['contract']
    usage = answer.get('usage') or {}
    i, o = usage.get('input_tokens'), usage.get('output_tokens')
    Store(store.directory/'usage').usage(id=request_id,source='local',session_id=job['run_id'],
        model=c['model'], started=started, status=status, tool='contract:'+c['backend'],
        logical_id=job['id'], duration=duration, input_tokens=i, output_tokens=o,
        cached_input_tokens=usage.get('cached_input_tokens'),
        total_tokens=i+o if i is not None and o is not None else None)
