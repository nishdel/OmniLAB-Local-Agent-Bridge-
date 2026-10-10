"""Prepare eight matched synthetic cases; never execute an inference or benchmark."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

CASES = [
 ('boundary', 'Make the upper boundary inclusive without changing the lower boundary.',
  'def contains(x, low, high):\n    return low <= x < high\n',
  'from subject import contains\nassert contains(10, 0, 10)\nassert not contains(-1, 0, 10)\nassert not contains(11, 0, 10)\n'),
 ('unicode', 'Measure UTF-8 payload bytes rather than Python character count.',
  'def payload_size(text):\n    return len(text)\n',
  'from subject import payload_size\nassert payload_size("é🙂") == 6\nassert payload_size("") == 0\nassert payload_size("abc") == 3\n'),
 ('stable_unique', 'Deduplicate labels while preserving their first-occurrence order.',
  'def unique(items):\n    return sorted(set(items))\n',
  'from subject import unique\nassert unique(["b","a","b","c"]) == ["b","a","c"]\nassert unique([]) == []\n'),
 ('boolean_config', 'Parse only true/false strings case-insensitively; reject other text.',
  'def enabled(value):\n    return bool(value)\n',
  'from subject import enabled\nassert enabled("false") is False\nassert enabled("TRUE") is True\ntry:\n    enabled("maybe")\nexcept ValueError:\n    pass\nelse:\n    raise AssertionError("invalid configuration accepted")\n'),
 ('pagination', 'Preserve all entries on the final partial page; reject zero page size.',
  'def pages(items, size):\n    return [items[i:i+size] for i in range(0, len(items)-size+1, size)]\n',
  'from subject import pages\nassert pages([1,2,3],2)==[[1,2],[3]]\nassert pages([],2)==[]\ntry:\n    pages([1],0)\nexcept ValueError:\n    pass\nelse:\n    raise AssertionError("zero page size")\n'),
 ('optional_usage', 'Return unknown totals when any component is unavailable, while preserving observed zero.',
  'def total(values):\n    return sum(value or 0 for value in values)\n',
  'from subject import total\nassert total([2,None]) is None\nassert total([]) is None\nassert total([0,0]) == 0\nassert total([2,3]) == 5\n'),
 ('retry_limit', 'Permit retries strictly below the configured maximum; zero disables retry.',
  'def retry(attempts, limit):\n    return attempts <= limit\n',
  'from subject import retry\nassert retry(0,1)\nassert not retry(1,1)\nassert not retry(0,0)\n'),
 ('status_separation', 'Show awaiting_review after finished execution unless a supervisor accepted it; preserve failures.',
  'def status(execution, review):\n    return "completed" if execution == "finished" else execution\n',
  'from subject import status\nassert status("finished","pending")=="awaiting_review"\nassert status("finished","accepted")=="completed"\nassert status("failed","pending")=="failed"\n')
]


def prepare(output):
    output.mkdir(parents=True, exist_ok=False)
    manifest={'schema_version':1,'executed':False,'hardware':None,'cases':[],
              'metrics':{'cloud_input_tokens':None,'cloud_cached_input_tokens':None,'cloud_output_tokens':None,
                         'planning_seconds':None,'handoff_seconds':None,'review_seconds':None,'repair_seconds':None,
                         'model_loading_seconds':None,'queue_seconds':None,'local_inference_seconds':None,
                         'elapsed_seconds':None,'retries':None,'acceptance':None,'corrections':None,'operator_interventions':None}}
    for key,objective,source,checks in CASES:
        hashes={name:hashlib.sha256(content.encode()).hexdigest() for name,content in
                [('subject.py',source),('acceptance.py',checks)]}
        case={'id':key,'objective':objective,'files_sha256':hashes,'arms':[],
              'acceptance_command':['python','acceptance.py']}
        # Each arm begins with identical public source and tests, without a proposed solution.
        for arm in ('codex_only','local_advisory','local_implementation'):
            folder=output/key/arm
            folder.mkdir(parents=True)
            (folder/'subject.py').write_text(source,encoding='utf-8',newline='\n')
            (folder/'acceptance.py').write_text(checks,encoding='utf-8',newline='\n')
            case['arms'].append({'arm':arm,'directory':str(folder),'base_revision':None,
                                'result':'not_run','measurements':dict(manifest['metrics'])})
        manifest['cases'].append(case)
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    return manifest


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    manifest=prepare(args.output.resolve())
    print(json.dumps({'cases':len(manifest['cases']),'executed':False,'manifest':str(args.output/'manifest.json')}))
