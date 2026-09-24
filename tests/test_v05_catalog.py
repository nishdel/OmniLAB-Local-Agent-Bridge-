from pathlib import Path
import tomllib

import pytest
from pydantic import ValidationError

from localagentbridge.catalog import (AgenticConfig, Catalog, Limits, Requirements, Role,
                                     Skill, Stage, Workflow)
from localagentbridge.config import Config, load_config


def catalog(tmp_path, profile=None, **options):
    if profile:
        directory = tmp_path/'project-profiles'
        directory.mkdir(exist_ok=True)
        (directory/'custom.toml').write_text(profile,encoding='utf-8')
    return Catalog(AgenticConfig(catalog_root=str(tmp_path),**options))


def test_bundled_roles_skills_and_workflows_are_loaded():
    c = Catalog(AgenticConfig())
    assert len(c.roles)==12 and len(c.skills)==15
    assert set(c.workflows)=={'implement_issue','review_change'}
    assert c.roles['planner'].skills==['issue-analysis','implementation-planning']
    assert c.skills['security-review'].adapter=='analyze_code'
    assert 'resource-review' in c.roles['code-reviewer'].skills
    assert c.resolve('implement_issue')[0].stages[2].checkpoint=='implementation'
    assert all('model' not in role.model_dump() for role in c.roles.values())


@pytest.mark.parametrize('data',[
    {'schema_version':2}, {'unknown':'value'}, {'adapter':'run_shell'}, {'input':'internet'},
    {'instruction':'x'*2001}, {'id':'../unsafe'}, {'version':'bad version'}])
def test_invalid_skills_rejected(data):
    base=dict(id='example',description='Example',adapter='analyze_code',input='context',instruction='Read evidence')
    with pytest.raises(ValidationError):
        Skill.model_validate(base|data)


@pytest.mark.parametrize('data',[{'model':'qwen3:4b'},{'authority':'workspace-write'}, {'skills':[]},
                               {'requirements':{'min_strength':True}}, {'requirements':{'max_attempts':4}}])
def test_invalid_roles_rejected(data):
    with pytest.raises(ValidationError):
        Role.model_validate(dict(id='example',description='Example',instruction='Read',skills=['code-review'])|data)


def test_invalid_or_cyclic_workflow_and_checkpoints():
    c=Catalog(AgenticConfig())
    original=c.workflows['review_change'].model_dump()
    for mutate in [lambda w:w['stages'].pop(),
                   lambda w:w['stages'][0].update(inputs_from=['review']),
                   lambda w:w['stages'][1].update(id='explore'),
                   lambda w:w['stages'][-1].update(when='security'),
                   lambda w:w['stages'][0].update(skills=['code-review','code-review'])]:
        import copy
        data=copy.deepcopy(original)
        mutate(data)
        with pytest.raises(ValidationError):
            Workflow.model_validate(data)


def test_handoffs_cannot_cross_implementation_checkpoint():
    data=Catalog(AgenticConfig()).workflows['implement_issue'].model_dump()
    data['stages'][4]['inputs_from']=['plan']
    with pytest.raises(ValidationError,match='after the last checkpoint'):
        Workflow.model_validate(data)


def test_profile_overrides_compose_and_narrow(tmp_path):
    c=catalog(tmp_path,'''id="custom"
description="Custom"
workflows=["review_change"]
instruction="Keep the host protocol unchanged."
require_security=true
[limits]
max_attempts=4
max_seconds=60
[[role_overrides]]
role="code-reviewer"
instruction="Check rollback."
allowed_models=["small:4b"]
[role_overrides.requirements]
min_strength=2
timeout_seconds=30
[[stage_overrides]]
workflow="review_change"
stage="explore"
[stage_overrides.replacement]
id="explore"
role="repository-explorer"
skills=["repository-discovery"]
''')
    workflow,profile=c.resolve('review_change','custom')
    assert workflow.stages[0].skills==['repository-discovery']
    assert workflow.limits.max_attempts==4 and workflow.limits.max_seconds==60
    role,models=c.role('code-reviewer',profile)
    assert role.requirements.min_strength==2 and role.requirements.timeout_seconds==30
    assert 'Check rollback.' in role.instruction and models==['small:4b']
    assert role.authority=='advisory'


@pytest.mark.parametrize('extra',[
    'disabled_roles=["code-reviewer"]',
    'workflows=["unknown"]',
    'authority_documents=["../AGENTS.md"]',
    'enabled_roles=["nonexistent"]',
    '[[role_overrides]]\nrole="code-reviewer"\n[[role_overrides]]\nrole="code-reviewer"',
    '[[stage_overrides]]\nworkflow="review_change"\nstage="decide"\ndisabled=true',
    '[[stage_overrides]]\nworkflow="review_change"\nstage="explore"\ndisabled=true',
    '[[stage_overrides]]\nworkflow="review_change"\nstage="nonexistent"\ndisabled=true',
])
def test_bad_profile_overrides_fail_before_execution(tmp_path,extra):
    base='id="custom"\ndescription="Custom"\n'
    if not extra.startswith('workflows='):
        base+='workflows=["review_change"]\n'
    with pytest.raises(ValueError):
        catalog(tmp_path,base+extra)


def test_profile_can_disable_unused_role_and_remove_optional_stage(tmp_path):
    c=catalog(tmp_path,'''id="custom"
description="Custom"
workflows=["review_change"]
disabled_roles=["security-reviewer", "implementation-advisor"]
[[stage_overrides]]
workflow="review_change"
stage="security"
disabled=true
''')
    workflow,_=c.resolve('review_change','custom')
    assert 'security' not in [s.id for s in workflow.stages]


def test_no_catalog_code_loading_duplicates_or_unbounded_files(tmp_path):
    root=tmp_path/'skills'
    root.mkdir()
    p=root/'skill.toml'
    p.write_text('id="code-review"\ndescription="Duplicate"\nadapter="review_diff"\ninput="diff"\ninstruction="Read"')
    with pytest.raises(ValueError,match='Duplicate'):
        catalog(tmp_path)
    p.write_bytes(b'x'*32769)
    with pytest.raises(ValueError,match='byte bound'):
        catalog(tmp_path)
    p.unlink()
    (root/'evil.py').write_text('raise RuntimeError("must not run")')
    with pytest.raises(ValueError,match='TOML'):
        catalog(tmp_path)


def test_catalog_rejects_reparse_file(tmp_path,monkeypatch):
    directory=tmp_path/'skills'
    directory.mkdir()
    path=directory/'skill.toml'
    path.write_text('')
    original=Path.lstat
    def modified(self):
        result=original(self)
        if self==path:
            from types import SimpleNamespace
            return SimpleNamespace(st_mode=result.st_mode,st_file_attributes=0x400)
        return result
    monkeypatch.setattr(Path,'lstat',modified)
    with pytest.raises(ValueError,match='regular files'):
        catalog(tmp_path)


def test_intersections_never_raise_limits_or_lower_requirements():
    assert Limits(max_attempts=2).intersect(Limits(max_attempts=20)).max_attempts==2
    result=Requirements(min_strength=3,timeout_seconds=10,capabilities=['reasoning']).intersect(
        Requirements(min_strength=1,timeout_seconds=200,capabilities=['coding']))
    assert result.min_strength==3 and result.timeout_seconds==10
    assert result.capabilities==['coding','reasoning']


def test_legacy_configuration_stays_opted_out(tmp_path):
    root=Path(__file__).resolve().parents[1]
    for file in ['config.example.toml','profiles/balanced.toml','profiles/quality.toml']:
        assert not load_config(root/file).agentic.enabled
    cfg=Config(data_dir=tmp_path,model='qwen3:4b')
    assert not cfg.agentic.enabled and cfg.roles=={}
    assert Config(data_dir=tmp_path,agentic={'enabled':False,'catalog_root':'does-not-exist'}).agentic.enabled is False
    with pytest.raises(ValueError,match='adaptive registry'):
        Config(data_dir=tmp_path,agentic={'enabled':True})


def test_catalog_path_resolves_relative_to_config(tmp_path):
    root=Path(__file__).resolve().parents[1]
    values=tomllib.loads((root/'config.example.toml').read_text())
    # Use the starter file as text so paths and environment handling exercise the actual loader.
    path=tmp_path/'config.toml'
    text=(root/'config.example.toml').read_text()
    (tmp_path/'custom').mkdir()
    path.write_text(text+'\n[agentic]\nenabled=true\ncatalog_root="custom"\n')
    cfg=load_config(path)
    assert cfg.agentic.catalog_root==str(tmp_path/'custom')
    assert cfg.model==values['model']
