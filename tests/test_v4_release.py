import importlib.util
from pathlib import Path
import pytest


spec=importlib.util.spec_from_file_location('release_audit',Path(__file__).resolve().parents[1]/'scripts/prepare_release.py')
release=importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)


def test_release_allowlist_excludes_private_history_and_refuses_overwrite(tmp_path):
    (tmp_path/'.gitignore').write_text('data/\n*.sqlite3\nconfig.toml\n')
    (tmp_path/'PUBLIC-FILES.txt').write_text('public.py\n')
    (tmp_path/'public.py').write_text('print("hello")\n')
    (tmp_path/'config.toml').write_text('personal = true')
    result=release.audit(tmp_path)
    assert not result['findings']
    release.stage(tmp_path,tmp_path/'stage',result)
    assert (tmp_path/'stage/public.py').is_file()
    assert not (tmp_path/'stage/config.toml').exists()
    with pytest.raises(ValueError):
        release.stage(tmp_path,tmp_path/'stage',result)
    with pytest.raises(ValueError):
        release.stage(tmp_path,tmp_path.parent/'outside',result)


def test_audit_flags_paths_identifiers_and_secret_shapes(tmp_path,monkeypatch):
    (tmp_path/'.gitignore').write_text('data/\n')
    (tmp_path/'PUBLIC-FILES.txt').write_text('public.txt\n')
    monkeypatch.setenv('LAB_AUDIT_TERMS','private-fixture-name')
    content='C:'+'/Users/Private/data\n'+'sk-'+'A'*40+'\nprivate-fixture-name'
    (tmp_path/'public.txt').write_text(content)
    problems={r['problem'] for r in release.audit(tmp_path)['findings']}
    assert {'absolute_windows_path','api_secret','private audit term'}<=problems


def test_public_fixture_digest_and_template_are_portable():
    from localagentbridge.config import load_config
    root=Path(__file__).resolve().parents[1]
    cfg=load_config(root/'config.example.toml')
    assert cfg.source_root==root and cfg.data_dir==root/'data'
    assert cfg.adaptive.enabled
    assert all(p.enabled for p in cfg.model_registry)


def test_ignore_samples_and_exact_tree_reject_leaks(tmp_path):
    root=Path(__file__).resolve().parents[1]
    assert release.ignore_findings(root)==[]
    (tmp_path/'public.py').write_text('pass')
    (tmp_path/'private.sqlite3').write_bytes(b'private')
    report={'sha256':{'public.py':'unused'}}
    assert release.exact_findings(tmp_path,report)==[
        dict(file='private.sqlite3',problem='unlisted file in exact release tree')]
