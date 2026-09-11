"""Import explicit independent reviews; never infer acceptance from model output."""
import argparse
import json
from pathlib import Path
from localagentbridge.config import load_config
from localagentbridge.telemetry import Store


def record(config, results, reviews):
    document=json.loads(Path(reviews).read_text(encoding='utf-8'))
    store=Store(load_config(config).data_dir)
    for path in Path(results).glob('*.json'):
        run=json.loads(path.read_text(encoding='utf-8'))
        grades=document['models'].get(run['model'])
        if not grades:
            continue
        if set(grades)!={c['category'] for c in run['cases']}:
            raise ValueError('Review must cover exactly the completed cases for '+run['model'])
        reports=[]
        entries=[]
        for case in run['cases']:
            outcome,flags,note=grades[case['category']]
            if outcome not in ('accepted','corrected','rejected') or len(flags)!=4 or any(type(v) is not int or v not in (0,1) for v in flags) or not note:
                raise ValueError('Invalid explicit review')
            if len(case['usage'])!=1:
                raise ValueError('Paired case must identify exactly one request')
            request=case['usage'][0]['id']
            reports.append(dict(request_id=request,outcome=outcome))
            entries.append((request,run['run_id'],case['category'],case['tool'],run['model'],outcome,*flags))
        store.report(reports)
        with store.connect() as db:
            db.executemany('INSERT OR REPLACE INTO benchmark_reviews VALUES (?,?,?,?,?,?,?,?,?,?)',entries)
        print(run['model'],len(entries),'independently reviewed cases recorded')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',default='config.toml')
    parser.add_argument('--results',default='benchmarks/v03/results')
    parser.add_argument('--reviews',default='benchmarks/v03/reviews.json')
    args=parser.parse_args()
    record(args.config,args.results,args.reviews)
