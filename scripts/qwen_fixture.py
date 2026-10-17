"""Portable synthetic lifecycle fixture. Does not read personal benchmark evidence."""
import shutil
import sys
import time
import uuid


def freeze_fixture(qb, fixture_review=False):
    from qwen_benchmark_io import atomic,sha
    root=qb.ROOT
    job_id='fixture-'+time.strftime('%Y%m%d-%H%M%S')+'-'+uuid.uuid4().hex[:6]
    job=qb.OUT/'jobs'/job_id
    snapshot=job/'snapshot'
    snapshot.mkdir(parents=True)
    names=[p.relative_to(root).as_posix() for directory in ('localagentbridge','scripts','examples','tests/fixtures')
           for p in (root/directory).rglob('*') if p.is_file() and '__pycache__' not in p.parts]
    names+=['pyproject.toml','config.example.toml',*qb.RUNNER_FILES]
    for name in set(names):
        destination=snapshot/name
        destination.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(root/name,destination)
    shutil.copy2(root/'config.example.toml',snapshot/'config.toml')
    names.append('config.toml')
    atomic(job/'source-hashes.json',{name:sha(snapshot/name) for name in sorted(set(names))})
    (job/'prior').mkdir()
    for name in ('grading-rubric.json','paired-reviewed-results.json','v05-reviewed-results.json','results.json'):
        atomic(job/'prior'/name,{})
    for name in ('README.md','METHOD.md','MODEL-METADATA.md'):
        (job/'prior'/name).write_text('Synthetic fixture. No model measurement.',encoding='utf-8')
    atomic(job/'prior-requests.json',{})
    driver=qb.module('synthetic_v05_dataset',root/'scripts/evaluate_v05_delegation.py')
    atomic(job/'v05-cases.json',driver.cases())
    config=dict(job_id=job_id,created=time.time(),repository=str(root),revision=None,
        python=sys.executable,runtime_exe=sys.executable,runtime_sha256=sha(sys.executable),
        runtime_environment={},endpoint=qb.ENDPOINT,fixture=True,fixture_review=fixture_review,
        codex_exe=shutil.which('codex') or sys.executable,codex_version='fixture',
        settings={},memory_admission_gib=32,differences=['Synthetic lifecycle fixture; never run real inference'],
        queue=[{'id':'fixture/one','suite':'fixture'},{'id':'fixture/two','suite':'fixture'}])
    config['frozen_inputs']={p.relative_to(job).as_posix():sha(p) for p in [job/'source-hashes.json',job/'prior-requests.json',job/'v05-cases.json',*sorted((job/'prior').glob('*'))]}
    atomic(job/'experiment.json',config)
    atomic(job/'state.json',dict(job_id=job_id,state='queued',created=time.time(),experiment_sha256=sha(job/'experiment.json'),worker=None,current_case=None,
        cases=[dict(c,state='queued',attempts=[]) for c in config['queue']]))
    atomic(job/'review-state.json',dict(state='pending-review',automatic_attempt_claimed=False))
    return job
