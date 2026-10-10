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
    grouped=defaultdict(list)
    for row in selected:
        backend=(row.get('tool') or '').removeprefix('contract:') if row['source']=='local' else 'codex'
        grouped[(row['source'],backend,row['model'])].append(row)
    return {'view':'implementation_investment','since':since,'cutoff':cutoff,
            'groups':[dict(source=s,backend=b,model=m,**aggregate(v)) for (s,b,m),v in sorted(grouped.items())],
            'records':[{k:r.get(k) for k in ('id','session_id','logical_id','source','model','tool','started','status',*TOKEN_FIELDS)} for r in selected],
            'semantics':'Input includes cached input; output includes reasoning. Subsets are never added twice. Unknown is not zero.',
            'coverage':'All recorded attempts in scope, including failures. Responses after cutoff and uninstrumented work are excluded, not zero.'}

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
