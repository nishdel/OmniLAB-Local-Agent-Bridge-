"""Audit an explicit source allowlist and optionally create a fresh local copy.

Does not initialize Git, push, publish, include dependencies, or copy ignored history.
Set LAB_AUDIT_TERMS to comma-separated private names to check without committing them.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import pathspec


PRIVATE_SAMPLES = ('config.toml', 'config.work.local.toml', '.env', '.env.production',
    'data/usage.sqlite3', 'data/usage.sqlite3-wal', 'trace.log', 'rollouts/session.jsonl',
    '.codex/config.toml', '.ollama/models/blobs/weights.bin', 'model.gguf', 'weights.safetensors',
    '.venv/Lib/package.py', '__pycache__/module.pyc', 'benchmarks/v04/private-prompt.json',
    'release-staging/anything.txt', 'private/source.txt', '.v041-test-run-1/output.txt',
    'bridge.log.1', 'scratch.tmp', 'backup.bak', 'package.whl', 'benchmarks/v05/private.json')

# Exact reviewed synthetic attack fixtures, not file-wide exemptions.
SYNTHETIC_MATCHES = {
    ('tests/test_v2_context.py', 'absolute_windows_path', 'C:/outside'),
    ('tests/test_selective_contracts.py', 'absolute_windows_path', 'C:/x'),
    ('tests/test_v4_release.py', 'absolute_personal_unix_path', '/Users/Private/'),
}
SYNTHETIC_MATCHES |= {('scripts/prepare_release.py', label, value) for _,label,value in SYNTHETIC_MATCHES}


def ignore_findings(root):
    ignore=pathspec.GitIgnoreSpec.from_lines((Path(root)/'.gitignore').read_text().splitlines())
    return [dict(file=name,problem='private/generated sample is not ignored')
            for name in PRIVATE_SAMPLES if not ignore.match_file(name)]


def exact_findings(root, report):
    """Use only on the fresh publication copy, before creating an environment there."""
    root=Path(root)
    expected=set(report['sha256'])
    actual={p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}
    return [dict(file=name,problem='unlisted file in exact release tree') for name in sorted(actual-expected)]


def audit(root):
    root=Path(root).resolve()
    ignore=pathspec.GitIgnoreSpec.from_lines((root/'.gitignore').read_text().splitlines())
    manifest=(root/'PUBLIC-FILES.txt').read_text().splitlines()
    files=[line.strip() for line in manifest if line.strip() and not line.startswith('#')]
    if len(files)!=len(set(files)):
        raise ValueError('Duplicate public manifest entries')
    terms=[t.casefold() for t in os.getenv('LAB_AUDIT_TERMS','').split(',') if t.strip()]
    user=os.getenv('USERNAME') or Path.home().name
    if len(user)>3:
        terms.append(user.casefold())
    patterns={
        'absolute_windows_path':re.compile(r'(?i)\b[a-z]:(?:/(?!/)|\\+(?![nrt](?:\s|\\|")))[a-z0-9_.-]+'),
        'absolute_personal_unix_path':re.compile(r'/(?:Users|home)/[a-zA-Z0-9_.-]+/'),
        'network_share_path':re.compile(r'\\\\[a-zA-Z0-9_-]+\\[a-zA-Z0-9_$-]+\\'),
        'private_key':re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
        'api_secret':re.compile(r'\b(?:sk-[A-Za-z0-9_-]{25,}|gh[pousr]_[A-Za-z0-9]{25,}|AKIA[A-Z0-9]{16})\b'),
        'personal_session_identifier':re.compile(r'\b(?!00000000-0000-0000-0000-000000000000)[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}\b',re.I),
    }
    findings=[]
    reviewed=[]
    hashes={}
    for name in files:
        path=root/name
        if not path.resolve().is_relative_to(root) or path.is_symlink() or not path.is_file():
            findings.append(dict(file=name,problem='missing or unsafe path'))
            continue
        if ignore.match_file(name):
            findings.append(dict(file=name,problem='manifest includes ignored private/generated material'))
        if path.suffix.lower() in ('.db','.sqlite','.sqlite3','.log','.jsonl','.gguf','.bin','.safetensors','.pyc','.whl','.zip','.pkl'):
            findings.append(dict(file=name,problem='forbidden release artifact type'))
        raw=path.read_bytes()
        hashes[name]=hashlib.sha256(raw).hexdigest()
        if path.suffix.lower()=='.png':
            continue  # Only manually reviewed synthetic screenshots are allowlisted.
        try:
            content=raw.decode('utf-8')
        except UnicodeDecodeError:
            findings.append(dict(file=name,problem='unexpected binary content'))
            continue
        for label,pattern in patterns.items():
            for match in pattern.finditer(content):
                if (name,label,match.group()) in SYNTHETIC_MATCHES:
                    reviewed.append(dict(file=name,pattern=label,reason='Reviewed synthetic path-security test input'))
                else:
                    findings.append(dict(file=name,problem=label))
        if any(term in content.casefold() for term in terms):
            findings.append(dict(file=name,problem='private audit term'))
    return dict(file_count=len(files),findings=findings,sha256=hashes,reviewed_synthetic_matches=reviewed,
                limits='Allowlist and pattern scan plus manual content review; not proof against every possible secret.')


def stage(root, target, report):
    root,target=Path(root).resolve(),Path(target).resolve()
    if report['findings']:
        raise ValueError('Resolve audit findings before staging')
    if target.exists() or not target.is_relative_to(root) or target==root:
        raise ValueError('Stage must be a new directory inside this checkout; nothing is overwritten')
    target.mkdir(parents=True)
    for name in report['sha256']:
        dest=target/name
        dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(root/name,dest)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage',help='New local directory under this checkout')
    parser.add_argument('--report',help='Local audit JSON output, normally under data/')
    parser.add_argument('--check-ignore',action='store_true',help='Check representative private/generated paths')
    parser.add_argument('--exact',action='store_true',help='Reject extra files in a fresh source-only publication copy')
    args=parser.parse_args()
    root=Path(__file__).resolve().parents[1]
    report=audit(root)
    if args.check_ignore:
        report['findings'].extend(ignore_findings(root))
    if args.exact:
        report['findings'].extend(exact_findings(root,report))
    if args.report:
        Path(args.report).write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='sha256'},indent=2))
    if report['findings']:
        raise SystemExit(1)
    if args.stage:
        stage(root,args.stage,report)
