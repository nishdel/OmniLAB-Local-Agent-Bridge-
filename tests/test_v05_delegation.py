import asyncio
from dataclasses import replace
import json

import httpx
import pytest
from pydantic import ValidationError

from localagentbridge.bridge import BridgeError
from localagentbridge.catalog import (AgenticConfig, Catalog, Limits, ProjectProfile, RequiredReview,
                                     Requirements, RoleOverride, StageOverride, Stage)
from localagentbridge.config import load_config
from localagentbridge.service import Service
from localagentbridge.workflow import WorkflowTask
from test_v05_workflows import setup, step, reach


def fixture(tmp_path, kind='review_change', **hints):
    service,old,chats=setup(tmp_path)
    task=WorkflowTask.model_validate(old.model_dump()|{'kind':kind,'delegation':hints})
    return service,task,chats


@pytest.mark.parametrize('kind',['repository_discovery','summarize_context','documentation_change',
    'review_change','test_failure','bug_analysis','issue_analysis'])
def test_small_tasks_default_direct_without_a_classifier(tmp_path,kind):
    service,task,chats=fixture(tmp_path,kind)
    engine=service.workflows
    plan=engine.plan(task)
    assert plan['delegation']['path']=='direct' and not chats
    assert plan['delegation']['selected_roles']==[]
    state=step(engine,engine.start(task),task)
    assert state['next_stage']=='decide'
    assert len(chats)==(0 if kind=='repository_discovery' else 1)
    if chats:
        assert 'Workflow role ' not in chats[0]['messages'][0]['content']
    assert state['delegation']['path']=='direct'


@pytest.mark.parametrize('hints,roles',[
    ({'security_sensitive':True},['security-reviewer']),
    ({'resource_sensitive':True},['performance-reviewer']),
    ({'architecture_impact':True},['architect']),
    ({'ui_change':True,'independent_review':True},['ux-reviewer']),
    ({'release_scope':True,'components':2,'expected_files':4},['documentation-reviewer']),
    ({'architecture_impact':True,'components':3,'independent_concerns':2},['code-reviewer','architect']),
])
def test_positive_reasons_select_only_relevant_roles(tmp_path,hints,roles):
    service,task,_=fixture(tmp_path,**hints)
    plan=service.workflows.plan(task)
    assert plan['delegation']['path']=='workflow'
    assert plan['delegation']['selected_roles']==roles
    assert all(not s['inputs_from'] for s in plan['stages'])
    assert plan['stages'][-1]['executor']=='codex'


def test_one_specialist_is_a_complete_workflow(tmp_path):
    service,task,chats=fixture(tmp_path,security_sensitive=True)
    engine=service.workflows
    state=step(engine,engine.start(task),task)
    assert len(chats)==1 and state['next_stage']=='decide'
    state=step(engine,state,task)
    assert state['state']=='waiting_for_codex'
    state=engine.checkpoint(state['run_id'],state['version'],task,{'action':'accept','note':'Codex verified evidence.'})
    assert state['state']=='codex_verified'


@pytest.mark.parametrize('mode,path,calls',[('auto','direct',1),('direct','direct',1),('workflow','workflow',2)])
def test_project_mode_controls_override_task_preference(tmp_path,mode,path,calls):
    service,task,chats=fixture(tmp_path)
    service.workflows.catalog.profiles['generic'].workflow_mode=mode
    if mode=='direct':
        task.delegation.mode='workflow'
    if mode=='workflow':
        task.delegation.mode='direct'
    engine=service.workflows
    state=reach(engine,engine.start(task),task,'decide')
    assert state['delegation']['path']==path and len(chats)==calls
    assert state['delegation']['project_policy_mandatory']==(mode=='workflow')


def test_direct_still_requires_project_security_review(tmp_path):
    service,task,chats=fixture(tmp_path,'issue_analysis',mode='direct',security_sensitive=True)
    engine=service.workflows
    profile=engine.catalog.profiles['generic']
    profile.required_reviews=[RequiredReview(role='security-reviewer',skill='security-review',when='security')]
    state=engine.start(task)
    assert state['delegation']['path']=='direct' and state['delegation']['project_policy_mandatory']
    state=step(engine,state,task)
    assert state['next_stage']=='required-1'
    with pytest.raises(BridgeError,match='Checkpoint requires'):
        engine.checkpoint(state['run_id'],state['version'],task,{'action':'accept','note':'Skip required reviewer'})
    state=step(engine,state,task)
    assert state['next_stage']=='decide' and len(chats)==2
    assert 'Workflow role security-reviewer' in chats[-1]['messages'][0]['content']
    assert 'untrusted_prior_results\\":[]' in chats[-1]['messages'][1]['content']


def test_conditional_policy_does_not_activate_for_typo(tmp_path):
    service,task,_=fixture(tmp_path,mode='direct')
    profile=service.workflows.catalog.profiles['generic']
    profile.required_reviews=[RequiredReview(role='security-reviewer',skill='security-review',when='dependencies')]
    task.diff='--- a/README.md\n+++ b/README.md\n-teh\n+the'
    assert service.workflows.plan(task)['delegation']['required_reviews']==[]
    task.diff='--- a/package.json\n+++ b/package.json\n-1.0\n+2.0'
    plan=service.workflows.plan(task)
    assert plan['delegation']['indicators']['path_signals']['dependencies']
    assert plan['delegation']['required_reviews'][0]['role']=='security-reviewer'
    assert plan['delegation']['path']=='direct'


def test_multiple_reviews_are_conditional_and_independent(tmp_path):
    service,task,chats=fixture(tmp_path,mode='direct',security_sensitive=True,resource_sensitive=True)
    profile=service.workflows.catalog.profiles['generic']
    profile.required_reviews=[RequiredReview(role='security-reviewer',skill='security-review',when='security'),
        RequiredReview(role='performance-reviewer',skill='resource-review',when='resources'),
        RequiredReview(role='ux-reviewer',skill='ui-ux-review',when='ui')]
    state=reach(service.workflows,service.workflows.start(task),task,'decide')
    assert len(chats)==3
    assert state['delegation']['selected_roles']==['security-reviewer','performance-reviewer']
    assert not any('ux-reviewer' in str(c) for c in chats)


@pytest.mark.parametrize('cap',['Light','Medium','Large','Maximum'])
def test_gate_uses_existing_cap_and_role_minimum(tmp_path,cap):
    service,task,_=fixture(tmp_path,security_sensitive=True)
    engine=service.workflows
    engine.catalog.profiles['generic'].role_overrides=[RoleOverride(role='security-reviewer',requirements=Requirements(min_strength=2))]
    service.bridge.store.compute_cap(value=cap)
    plan=engine.plan(task)
    assert plan['delegation']['compute_tier']==cap
    assert plan['delegation']['path']==('direct' if cap=='Light' else 'workflow')
    assert plan['delegation']['runnable']


def test_mandatory_unavailable_review_hands_to_codex_no_bypass(tmp_path):
    service,task,chats=fixture(tmp_path,mode='direct',security_sensitive=True)
    engine=service.workflows
    profile=engine.catalog.profiles['generic']
    profile.require_security=True
    profile.role_overrides=[RoleOverride(role='security-reviewer',allowed_models=[])]
    state=engine.start(task)
    assert state['state']=='handed_off' and not chats
    assert state['delegation']['project_policy_mandatory']
    assert not state['delegation']['runnable']
    assert any(s['role']=='security-reviewer' for s in state['stages'])


def test_optional_budget_falls_back_but_mandatory_budget_does_not(tmp_path):
    service,task,chats=fixture(tmp_path,architecture_impact=True,components=3,independent_concerns=2)
    engine=service.workflows
    engine.catalog.profiles['generic'].limits=Limits(max_attempts=1)
    plan=engine.plan(task)
    assert plan['delegation']['path']=='direct' and plan['delegation']['runnable']
    assert 'optional_decomposition_unavailable_within_cap_or_budget' in plan['delegation']['reasons']
    engine.catalog.profiles['generic'].require_security=True
    state=engine.start(task)
    assert state['state']=='handed_off' and not chats
    assert not state['delegation']['estimate']['fits_budget']


@pytest.mark.parametrize('hints,complexity',[({'ambiguous':True},'simple'),({},'complex')])
def test_unscoped_work_stays_with_codex(tmp_path,hints,complexity):
    service,task,chats=fixture(tmp_path,**hints)
    task.complexity=complexity
    state=service.workflows.start(task)
    assert state['state']=='handed_off' and not chats
    assert 'codex_must_scope_complex_or_ambiguous_work' in state['delegation']['blockers']


def test_stable_decision_and_budget_survive_cap_change_and_restart(tmp_path):
    service,task,chats=fixture(tmp_path)
    engine=service.workflows
    state=step(engine,engine.start(task),task)
    service.bridge.store.compute_cap(value='Light')
    second=Service(service.config,service.bridge.transport).workflows
    resumed=second.start(task)
    assert resumed['run_id']==state['run_id'] and resumed['budget']['attempts']==1
    assert resumed['delegation']['compute_tier']=='Medium'  # original decision, not current route cap
    task.delegation.mode='workflow'
    with pytest.raises(BridgeError,match='immutable'):
        second.start(task)
    assert len(chats)==1


def test_gate_metadata_does_not_persist_diff_or_objective(tmp_path):
    service,task,_=fixture(tmp_path,architecture_impact=True)
    task.objective='SECRET_OBJECTIVE'
    task.diff='+SECRET_DIFF'
    state=service.workflows.start(task)
    with service.bridge.store.connect() as db:
        dump='\n'.join(db.iterdump())
    assert 'SECRET_OBJECTIVE' not in dump and 'SECRET_DIFF' not in dump
    assert 'positive_specialization_case' in dump
    assert state['delegation']['indicators']['architecture']


@pytest.mark.parametrize('field,value',[('mode','swarm'),('expected_files',True),('components',-1),
    ('independent_concerns',20),('security_sensitive','true'),('specialization_value',100)])
def test_invalid_hints_rejected(tmp_path,field,value):
    with pytest.raises(ValidationError):
        fixture(tmp_path,**{field:value})


def test_profile_threshold_does_not_override_required_review(tmp_path):
    service,task,_=fixture(tmp_path,security_sensitive=True)
    p=service.workflows.catalog.profiles['generic']
    p.decomposition_threshold=12
    p.require_security=True
    plan=service.workflows.plan(task)
    assert plan['delegation']['path']=='direct'
    assert plan['delegation']['selected_roles']==['security-reviewer']


def test_new_sensitive_evidence_cannot_skip_required_review(tmp_path):
    service,task,_=fixture(tmp_path,'implement_issue',mode='direct')
    engine=service.workflows
    p=engine.catalog.profiles['generic']
    p.required_reviews=[RequiredReview(role='security-reviewer',skill='security-review',when='dependencies')]
    state=step(engine,reach(engine,engine.start(task),task,'implement'),task)
    task.diff='--- a/requirements.txt\n+++ b/requirements.txt\n+unreviewed-dependency'
    with pytest.raises(BridgeError,match='additional project reviews'):
        engine.checkpoint(state['run_id'],state['version'],task,{'action':'accept','note':'Dependency added'})


def test_explicit_workflow_and_stage_overrides_are_preserved(tmp_path):
    service,task,_=fixture(tmp_path)
    p=service.workflows.catalog.profiles['generic']
    p.stage_overrides=[StageOverride(workflow='review_change',stage='explore',replacement=Stage(
        id='explore',role='repository-explorer',skills=['repository-discovery']))]
    plan=service.workflows.plan(task)
    assert plan['delegation']['project_policy_mandatory']
    assert plan['stages'][0]['skills']==['repository-discovery']
    p.workflow_mode='direct'
    with pytest.raises(BridgeError,match='conflicts'):
        service.workflows.plan(task)


def test_profile_file_controls_and_validation(tmp_path):
    directory=tmp_path/'project-profiles'; directory.mkdir()
    file=directory/'project.toml'
    base='id="test"\ndescription="Test"\nworkflows=["review_change"]\nworkflow_mode="direct"\n'
    file.write_text(base+'[[required_reviews]]\nrole="security-reviewer"\nskill="security-review"\nwhen="dependencies"\n')
    c=Catalog(AgenticConfig(catalog_root=str(tmp_path),project_profile='test'))
    assert c.profiles['test'].workflow_mode=='direct'
    file.write_text(base+'[[required_reviews]]\nrole="security-reviewer"\nskill="code-review"\n')
    with pytest.raises(ValueError,match='Required review'):
        Catalog(AgenticConfig(catalog_root=str(tmp_path),project_profile='test'))


def test_explicit_profile_policy_cannot_be_bypassed_by_omitting_task_hints(tmp_path):
    service,task,chats=setup(tmp_path)
    profile=service.workflows.catalog.profiles['generic']
    profile.workflow_mode='direct'
    profile.required_reviews=[RequiredReview(role='security-reviewer',skill='security-review')]
    assert task.delegation is None
    engine=service.workflows
    state=reach(engine,engine.start(task),task,'decide')
    assert state['delegation']['path']=='direct' and state['delegation']['project_policy_mandatory']
    assert len(chats)==2 and state['delegation']['selected_roles']==['security-reviewer']
