"""Aggregate recorded measurements and explicit grades; never grade model prose."""
import argparse
from collections import Counter
import json
from pathlib import Path
from statistics import median


def summarize(directory,reviews):
    grades=json.loads(Path(reviews).read_text(encoding='utf-8'))
    expected={f['category']:f['sha256'] for f in json.loads(Path('tests/fixtures/paired_requests.json').read_text(encoding='utf-8'))}
    output=[]
    for path in Path(directory).glob('*.json'):
        run=json.loads(path.read_text(encoding='utf-8'))
        cases=run['cases']
        for case in cases:
            if case['input_sha256']!=expected[case['category']]:
                raise ValueError('Frozen input hash mismatch')
        usage=[row for c in cases for row in c['usage']]
        successful=[r for r in usage if r['status']=='ok']
        reviewed=grades['models'].get(run['model'],{})
        generation=sum(r['generation_seconds'] or 0 for r in usage)
        source=sum(r['source_bytes'] or 0 for r in successful)
        returned=sum(r['output_bytes'] or 0 for r in successful)
        outputs=sum(r['output_tokens'] or 0 for r in usage)
        record=dict(model=run['model'],cases=len(cases),calls=len(usage),errors=sum(c['error'] is not None for c in cases),
            input_tokens=sum(r['input_tokens'] or 0 for r in usage),output_tokens=outputs,
            total_tokens=sum(r['total_tokens'] or 0 for r in usage),
            unavailable_token_counts=sum(r['total_tokens'] is None for r in usage),
            wall_seconds=sum(r['duration'] or 0 for r in usage),
            average_latency_seconds=sum(r['duration'] or 0 for r in usage)/len(usage) if usage else None,
            median_latency_seconds=median(r['duration'] for r in usage) if usage else None,
            generation_seconds=generation,load_seconds=sum(r['load_seconds'] or 0 for r in usage),
            generation_tokens_per_second=outputs/generation if generation else None,
            source_bytes=source,returned_bytes=returned,potential_bytes_reduced=source-returned,
            potential_context_reduction=1-returned/source if source else None,
            outcomes=dict(Counter(v[0] for v in reviewed.values())),
            error_flags={key:sum(v[1][i] for v in reviewed.values()) for i,key in enumerate(grades['flags_order'])},
            categories={c['category']:reviewed.get(c['category'],['unreviewed'])[0] for c in cases})
        for field in ('peak_ollama_rss_bytes_sampled','peak_system_used_bytes_sampled','peak_gpu_used_mib_sampled','model_allocation_bytes','model_vram_bytes'):
            values=[c['hardware'].get(field) for c in cases if field!='peak_ollama_rss_bytes_sampled' or 'process_scope' in c['hardware']]
            values=[v for v in values if v is not None]
            record[field]=max(values) if values else None
        discovery=[c['usage'][0] for c in cases if c['category'] in ('repository_discovery','code_search','code_summarization') and c['usage'] and not c['error']]
        size=sum(r['source_bytes'] for r in discovery)
        record['discovery_summary_reduction']=1-sum(r['output_bytes'] for r in discovery)/size if size else None
        output.append(record)
    return {'note':'Paired real calls only. Potential byte reduction is not measured Codex token reduction. Missing token counters are not zero usage. Process RSS omitted for pre-fix sampler; see memory-recheck.', 'models':output}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--results',default='benchmarks/v03/results')
    parser.add_argument('--reviews',default='benchmarks/v03/reviews.json')
    parser.add_argument('--output',default='benchmarks/v03/metrics.json')
    args=parser.parse_args()
    Path(args.output).write_text(json.dumps(summarize(args.results,args.reviews),indent=2),encoding='utf-8')
