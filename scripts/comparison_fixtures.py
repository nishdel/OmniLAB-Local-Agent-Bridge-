"""Fresh public synthetic comparison fixtures, authored before any model trial.

The supervisor/evaluator can see these authorities: do not call this a blind or
private held-out benchmark. Each generation session sees only its declared source
and requirements. No answer or prior arm's solution is supplied to generation.
"""

FIXTURES = [
    dict(id='source_explanation', category='documentation', lane='local_advisory',
         objective='Explain cache.lookup from source, including expiry, missing keys and zero values. '
                   'Return JSON with summary (under 180 words), expiry_comparison (operator), '
                   'expired_result, missing_result, zero_is_cached (boolean), and source_lines (line numbers).',
         files={'cache.py': '''def lookup(entries, key, now):
    if key not in entries:
        return None
    value, expires = entries[key]
    if now >= expires:
        return None
    return value
'''}, editable=[],
         acceptance={'facts': 'All stated behavior matches source, with correct source references and no unsupported claims.'},
         authority='''import json
from pathlib import Path
a = json.loads(Path('answer.json').read_text())
assert a['expiry_comparison'] == '>='
assert a['expired_result'] is None and a['missing_result'] is None
assert a['zero_is_cached'] is True
assert {2, 5, 7} <= set(a['source_lines'])
assert 10 <= len(a['summary'].split()) <= 180
print('facts: structured facts passed; independent prose review still required')
'''),
    dict(id='defect_review', category='code-review', lane='local_advisory',
         objective='Review merge_readings against its specification: retain every reading in input order, '
                   'including equal timestamps and numeric zero; discard only None values. '
                   'Return JSON findings with line (integer), explanation, and a concrete reproduction '
                   'input plus expected output. Identify distinct defects without changing code.',
         files={'readings.py': '''def merge_readings(rows):
    by_time = {}
    for timestamp, value in rows:
        if value:
            by_time[timestamp] = value
    return list(by_time.items())
'''}, editable=[],
         acceptance={'defects': 'Identify loss of zero values and duplicate-timestamp readings; reproduce both, avoid invented defects.'},
         authority='''import json
from pathlib import Path
from readings import merge_readings
a = json.loads(Path('answer.json').read_text())
findings = a['findings']
assert len(findings) == 2
assert {f['line'] for f in findings} == {4, 5}
for f in findings:
    rows = f['input']
    expected = [row for row in rows if row[1] is not None]
    assert f['expected'] == expected
    assert [list(r) for r in merge_readings(rows)] != expected
    assert len(f['explanation'].split()) >= 5
assert any(any(row[1] == 0 for row in f['input']) for f in findings)
assert any(len({r[0] for r in f['input']}) < len(f['input']) for f in findings)
print('defects: reproduced; independent causal review still required')
'''),
    dict(id='regression_tests', category='test-generation', lane='local_implementation',
         objective='Write unittest tests in test_subject.py for lease_active. Valid interval is '
                   'acquired <= now < acquired + duration. Negative duration raises ValueError; '
                   'zero duration is never active. Test ordinary, start, expiry, pre-start and invalid cases. '
                   'Use only the public function; tests must run via unittest and detect behavior defects.',
         files={'subject.py': '''def lease_active(now, acquired, duration):
    if duration < 0:
        raise ValueError('negative duration')
    return acquired <= now < acquired + duration
''', 'test_subject.py': 'import unittest\nfrom subject import lease_active\n'},
         editable=['test_subject.py'],
         acceptance={'regression': 'Tests pass correct behavior and fail each of four independent behavior mutants, with no skipped/empty suite.'},
         authority='''import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
source = Path('subject.py').read_text()
tests = Path('test_subject.py').read_text()
mutants = [
    source.replace('now < acquired', 'now <= acquired'),
    source.replace('acquired <= now', 'acquired < now'),
    source.replace("raise ValueError('negative duration')", 'return False'),
    source.replace('acquired <= now < acquired + duration', 'now < acquired + duration'),
]
driver = """import unittest
s=unittest.defaultTestLoader.discover('.', pattern='test_subject.py')
assert s.countTestCases() >= 4, 'Need at least four independent tests'
r=unittest.TextTestRunner().run(s)
assert not r.skipped
raise SystemExit(0 if r.wasSuccessful() else 1)
"""
for i, code in enumerate([source, *mutants]):
    with tempfile.TemporaryDirectory() as tmp:
        Path(tmp, 'subject.py').write_text(code)
        Path(tmp, 'test_subject.py').write_text(tests)
        result = subprocess.run([sys.executable, '-B', '-c', driver], cwd=tmp,
                                capture_output=True, text=True, timeout=2)
        if i == 0:
            assert result.returncode == 0, result.stdout + result.stderr
        else:
            assert result.returncode != 0, 'Surviving mutant ' + str(i)
            assert 'FAILED (' in result.stderr, 'Must detect defect by a test failure'
print('regression: correct baseline passes; all four behavior mutants killed')
'''),
    dict(id='bounded_fix', category='small-fix', lane='local_implementation',
         objective='Fix bucket_counts in subject.py. Timestamps at an edge belong to the next '
                   'half-open bucket; ignore timestamps outside [edges[0],edges[-1]). '
                   'Reject fewer than two or non-strictly-increasing edges. Preserve input order and do not mutate inputs.',
         files={'subject.py': '''def bucket_counts(times, edges):
    counts = [0] * (len(edges) - 1)
    for t in times:
        for i in range(len(counts)):
            if edges[i] <= t <= edges[i + 1]:
                counts[i] += 1
                break
    return counts
'''}, editable=['subject.py'],
         acceptance={'boundaries': 'Correct half-open bucket boundaries and invalid edge handling; preserve inputs.'},
         authority='''from subject import bucket_counts
times = [-1, 0, 1, 2, 2, 3, 4, 5]
edges = [0, 2, 4]
assert bucket_counts(times, edges) == [2, 3]
assert times == [-1, 0, 1, 2, 2, 3, 4, 5] and edges == [0, 2, 4]
assert bucket_counts([], [0, 1]) == [0]
assert bucket_counts([0.5, 1.5], [0, 1, 2]) == [1, 1]
for bad in [[], [0], [0, 0], [2, 1]]:
    try:
        bucket_counts([], bad)
    except ValueError:
        pass
    else:
        raise AssertionError('Invalid edges accepted')
print('boundaries: edge, duplicate, float, empty and input-preservation checks passed')
'''),
    dict(id='multifile_refactor', category='small-refactor', lane='local_implementation',
         objective='Centralize label normalization in labels.normalize, then use it from '
                   'exporter.row_label and summary.group_label. Preserve strip/lower behavior, '
                   'empty/None fallback to unknown, existing signatures and exceptions for non-strings. '
                   'Both callers must dynamically use the shared implementation.',
         files={'labels.py': '# Shared normalization goes here.\n',
                'exporter.py': '''def row_label(value):
    return (value or '').strip().lower() or 'unknown'
''', 'summary.py': '''def group_label(value):
    return (value or '').strip().lower() or 'unknown'
'''}, editable=['labels.py', 'exporter.py', 'summary.py'],
         acceptance={'behavior': 'One shared function; preserve callers, fallback and invalid-input behavior.'},
         authority='''import labels
import exporter
import summary
for fn in [labels.normalize, exporter.row_label, summary.group_label]:
    for value, expected in [(None,'unknown'),('', 'unknown'),('  ', 'unknown'),('  A  ', 'a'),('É', 'é')]:
        assert fn(value) == expected
    try:
        fn(7)
    except AttributeError:
        pass
    else:
        raise AssertionError('Invalid value behavior changed')
labels.normalize = lambda value: 'shared-marker'
assert exporter.row_label('x') == summary.group_label('x') == 'shared-marker'
print('behavior: shared implementation and compatibility checks passed')
'''),
    dict(id='structured_logs', category='log-analysis', lane='local_advisory',
         objective='Analyze events.json. Count distinct attempts by terminal state, count accepted tasks, '
                   'and compute observed generation ms including retries. A duplicate event ID is a replay, '
                   'not another attempt; missing duration makes total duration unknown. '
                   'Return JSON attempts_by_state, accepted_tasks, known_generation_ms, '
                   'total_generation_ms, missing_duration_attempts and evidence_event_ids.',
         files={'events.json': '''[
  {"event":"e1","task":"alpha","attempt":1,"state":"failed","generation_ms":40},
  {"event":"e1","task":"alpha","attempt":1,"state":"failed","generation_ms":40},
  {"event":"e2","task":"alpha","attempt":2,"state":"accepted","generation_ms":60},
  {"event":"e3","task":"beta","attempt":1,"state":"blocked","generation_ms":null},
  {"event":"e4","task":"gamma","attempt":1,"state":"rejected","generation_ms":20}
]
'''}, editable=[],
         acceptance={'accounting': 'Deduplicate events, retain failed cost, separate blocked from quality failures and leave missing totals unknown.'},
         authority='''import json
from pathlib import Path
a = json.loads(Path('answer.json').read_text())
assert a['attempts_by_state'] == {'failed':1, 'accepted':1, 'blocked':1, 'rejected':1}
assert a['accepted_tasks'] == 1 and a['known_generation_ms'] == 120
assert a['total_generation_ms'] is None
assert a['missing_duration_attempts'] == 1
assert set(a['evidence_event_ids']) == {'e1','e2','e3','e4'}
print('accounting: replay, retry, blocked, rejection and unknown-duration checks passed')
''')
]
