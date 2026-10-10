"""Auditable views over existing usage records, not another token counter."""
from collections import defaultdict
import time
from .telemetry import TOKEN_FIELDS, Store

def aggregate(rows):
    fields = {}
    for key in TOKEN_FIELDS:
        known = [r.get(key) for r in rows if r.get(key) is not None]
        fields[key] = {'known_total':sum(known) if known else None,
                       'total':sum(known) if rows and len(known)==len(rows) else None,
                       'reported_records':len(known),'missing_records':len(rows)-len(known)}
    return {'records':len(rows),'tokens':fields}

CATEGORIES = ('implementation', 'evaluation', 'operating', 'unattributed')


def bind_usage(store, *, kind, session_id, run_id, category, evidence, logical_id=None, task_id=None):
    """Trusted metadata only: bind a whole session or exact whole turn/job, never a fraction."""
    if kind not in ('cloud', 'local') or category not in CATEGORIES:
        raise ValueError('Unknown usage kind/category')
    for value in (session_id, run_id, evidence):
        if not isinstance(value, str) or not value.strip() or len(value) > 2000:
            raise ValueError('Usage attribution requires bounded identity and evidence')
    for value in (logical_id, task_id):
        if value is not None and (not isinstance(value, str) or not value.strip() or len(value) > 200):
            raise ValueError('Invalid turn/job/task identity')
    row = (kind, session_id, logical_id or '', run_id, task_id, category, evidence)
    usage = Store(store.directory/'usage')
    with usage.connect() as db:
        db.execute('BEGIN IMMEDIATE')
        old = db.execute('SELECT * FROM usage_bindings WHERE kind=? AND session_id=? AND logical_id=?', row[:3]).fetchone()
        if old:
            if tuple(old)[:7] != row:
                raise ValueError('Usage identity already attributed differently')
            return dict(old)
        overlap = db.execute("SELECT 1 FROM usage_bindings WHERE kind=? AND session_id=? AND (logical_id='' OR ?='')",
                             row[:3]).fetchone()
        if overlap:
            raise ValueError('Whole-session and turn/job attribution cannot overlap')
        db.execute('INSERT INTO usage_bindings VALUES(?,?,?,?,?,?,?,?)', (*row, time.time()))
        return dict(db.execute('SELECT * FROM usage_bindings WHERE kind=? AND session_id=? AND logical_id=?', row[:3]).fetchone())


def attribute(usage, rows):
    with usage.connect() as db:
        bindings = {(r['kind'], r['session_id'], r['logical_id']): dict(r)
                    for r in db.execute('SELECT * FROM usage_bindings')}
    for row in rows:
        kind = 'local' if row['source'] == 'local' else 'cloud'
        key = (kind, row['session_id'])
        row['attribution'] = bindings.get((*key, row.get('logical_id') or '')) or bindings.get((*key, ''))
        row['category'] = row['attribution']['category'] if row['attribution'] else 'unattributed'
    return {category: {kind: aggregate([r for r in rows if r['category'] == category
                                      and (r['source'] == 'local') == (kind == 'local')])
                       for kind in ('cloud', 'local')} for category in CATEGORIES}


def investment(store, since=0, cutoff=None, session_ids=None):
    cutoff = time.time() if cutoff is None else cutoff
    usage = Store(store.directory/'usage')
    with usage.connect() as db:
        rows=[dict(r) for r in db.execute('SELECT * FROM usage WHERE started>=? AND started<=? ORDER BY started,id',(since,cutoff))]
    if session_ids is not None:
        rows=[r for r in rows if r['source']=='local' or r['session_id'] in session_ids]
    # Preserve the existing store's complete-stream preference: never add OTEL
    # and rollout observations of the same session/model.
    streams=defaultdict(list)
    for row in rows:
        streams[(row['session_id'],row['model'],row['source'])].append(row)
    selected=[]
    groups={(s,m) for s,m,src in streams if src!='local'}
    for session,model in groups:
        choices=[v for (s,m,src),v in streams.items() if (s,m)==(session,model) and src!='local']
        selected += max(choices,key=lambda v:(sum(r['total_tokens'] or 0 for r in v),v[0]['source']=='otel'))
    selected += [r for r in rows if r['source']=='local']
    categories = attribute(usage, selected)
    grouped=defaultdict(list)
    for row in selected:
        backend=(row.get('tool') or '').removeprefix('contract:') if row['source']=='local' else 'codex'
        grouped[(row['source'],backend,row['model'])].append(row)
    runs=defaultdict(list)
    for row in selected:
        binding=row['attribution'] or {}
        runs[(binding.get('run_id'),binding.get('task_id'),row['category'],
              'local' if row['source']=='local' else 'cloud')].append(row)
    return {'runs':[dict(run_id=r,task_id=t,category=c,kind=k,**aggregate(v))
                    for (r,t,c,k),v in runs.items()],
            'view':'recorded_usage','since':since,'cutoff':cutoff,'categories':categories,
            'groups':[dict(source=s,backend=b,model=m,**aggregate(v)) for (s,b,m),v in sorted(grouped.items())],
            'records':[{k:r.get(k) for k in ('id','session_id','logical_id','source','model','tool','started','status','category','attribution',*TOKEN_FIELDS)} for r in selected],
            'semantics':'Input includes cached input; output includes reasoning. Subsets are never added twice. Unknown is not zero.',
            'coverage':'Bindings label entire observed sessions/turns/jobs, not proof of complete instrumentation. Unbound records remain unattributed. All recorded attempts in scope, including failures. Responses after cutoff and uninstrumented work are excluded, not zero.'}

def operating_savings(baseline, hybrid, *, equivalent=False, complete=False, evidence=None):
    if not equivalent or not complete or not evidence or baseline is None or hybrid is None:
        return {'status':'not established','baseline_cloud_tokens':baseline,'hybrid_cloud_tokens':hybrid,
                'net_cloud_tokens_avoided':None,'reduction_percent':None}
    if any(type(v) is not int or v<0 for v in (baseline,hybrid)):
        raise ValueError('Comparison requires nonnegative measured cloud counters')
    net=baseline-hybrid
    return {'status':'measured sample only','baseline_cloud_tokens':baseline,'hybrid_cloud_tokens':hybrid,
            'net_cloud_tokens_avoided':net,'reduction_percent':100*net/baseline if baseline>0 else None,
            'evidence':evidence,'limitation':'No implementation-wide or monthly extrapolation; tokens are not subscription bill savings.'}
