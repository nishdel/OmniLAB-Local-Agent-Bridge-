"""Cheap, explainable delegation gate. Scores are policy heuristics, never quality scores.

No inference or model inventory request occurs during planning. The existing
router and execution ledger remain responsible for admission and actual usage.
"""
from pathlib import PurePosixPath
import re
from typing import Annotated, Literal

from pydantic import Field

from .adaptive import AdaptiveRouter
from .bridge import BridgeError
from .catalog import Strict


class DelegationHints(Strict):
    mode: Literal['auto', 'direct', 'workflow'] = 'auto'
    expected_files: Annotated[int, Field(ge=0, le=1000)] = 1
    components: Annotated[int, Field(ge=1, le=64)] = 1
    independent_concerns: Annotated[int, Field(ge=1, le=12)] = 1
    security_sensitive: bool = False
    dependency_change: bool = False
    architecture_impact: bool = False
    resource_sensitive: bool = False
    ui_change: bool = False
    release_scope: bool = False
    ambiguous: bool = False
    independent_review: bool = False
    # Explicit caller expectation, not a local model's self-assessed confidence.
    specialization_value: Literal['unknown', 'useful', 'essential'] = 'unknown'


# This maps an operation to an adapter, not a task name to a delegation verdict.
PRIMARY = {
    'repository_discovery': ('repository-explorer', 'repository-discovery'),
    'summarize_context': ('repository-explorer', 'context-summary'),
    'documentation_change': ('documentation-reviewer', 'documentation-review'),
    'review_change': ('code-reviewer', 'code-review'),
    'test_failure': ('test-engineer', 'test-failure-analysis'),
    **{kind: ('planner', 'issue-analysis') for kind in ('bug_analysis', 'issue_analysis',
       'architecture_review', 'security_review', 'resource_review', 'release_review', 'implement_issue')},
}
SPECIALISTS = {
    'architecture': ('architect', 'architecture-review'),
    'security': ('security-reviewer', 'security-review'),
    'resources': ('performance-reviewer', 'resource-review'),
    'ui': ('ux-reviewer', 'ui-ux-review'),
    'release': ('documentation-reviewer', 'release-review'),
}
DEPENDENCIES = {'pyproject.toml', 'requirements.txt', 'requirements.lock.txt', 'package.json',
                'package-lock.json', 'pnpm-lock.yaml', 'cargo.toml', 'cargo.lock', 'packages.lock.json'}


def indicators(task):
    hints = task.delegation
    # Evidence paths are hints, never commands, and are not copied into telemetry.
    paths = {f.path.replace('\\', '/') for f in task.files}
    paths.update(re.findall(r'^\+\+\+ (?:b/)?([^\r\n\t]{1,240})', task.diff, re.M))
    paths.discard('/dev/null')
    parts = [PurePosixPath(p.lower()) for p in paths]
    dependency_path = any(p.name in DEPENDENCIES or p.suffix == '.csproj' for p in parts)
    security_path = any(set(p.parts) & {'auth', 'security', 'secrets', 'permissions'} for p in parts)
    ui_path = any(p.suffix in {'.css', '.scss', '.tsx', '.jsx', '.axaml', '.xaml'} for p in parts)
    security = hints.security_sensitive or task.security_review or security_path
    dependencies = hints.dependency_change or dependency_path
    return dict(complexity=task.complexity, expected_files=max(hints.expected_files, len(paths)),
        observed_files=len(paths), components=hints.components, independent_concerns=hints.independent_concerns,
        security=security or dependencies, dependencies=dependencies,
        architecture=hints.architecture_impact, resources=hints.resource_sensitive or task.resource_review,
        ui=hints.ui_change or ui_path, release=hints.release_scope, ambiguous=hints.ambiguous,
        independent_review=hints.independent_review, specialization_value=hints.specialization_value,
        path_signals={'dependencies':dependency_path, 'security':security_path, 'ui':ui_path})


def stage(name, pair, *, direct=False, inputs=()):
    role, skill = pair
    return dict(id=name, executor='local', role=role, skills=[skill], inputs_from=list(inputs),
                when='always', checkpoint=None, skip=False, direct=direct)


def checkpoint(name='decide', kind='decision'):
    return dict(id=name, executor='codex', role=None, skills=[], inputs_from=[], when='always',
                checkpoint=kind, skip=False)


def plan(engine, task):
    cfg, catalog, hints = engine.config, engine.catalog, task.delegation
    profile_id = task.project_profile or cfg.agentic.project_profile
    profile = catalog.profiles.get(profile_id)
    if not profile:
        raise BridgeError('Unknown project profile.')
    primary = PRIMARY.get(task.kind)
    matching = [w for w in profile.workflows if task.kind in catalog.workflows[w].task_kinds]
    base_id = task.workflow or (matching[0] if len(matching)==1 else None)
    if len(matching)>1 and not task.workflow:
        raise BridgeError('Workflow selection is ambiguous; supply an enabled workflow ID.')
    if not base_id:
        # A profile must explicitly allow this template family even for an adaptive single stage.
        base_id = 'review_change' if 'review_change' in profile.workflows else None
    if not base_id or (primary is None and not task.workflow):
        raise BridgeError('Unsupported adaptive operation or no allowed workflow template.')
    base, profile = catalog.resolve(base_id, profile_id)
    facts = indicators(task)
    relevant = [pair for flag,pair in SPECIALISTS.items() if facts[flag]]
    required = [(r.role,r.skill) for r in profile.required_reviews if r.when=='always' or facts[r.when]]
    if profile.require_security:
        required.append(SPECIALISTS['security'])
    if profile.require_resources:
        required.append(SPECIALISTS['resources'])
    required = list(dict.fromkeys(required))
    points = {
        'complexity': {'simple':0, 'moderate':1, 'complex':2}[task.complexity],
        'breadth': 2 if facts['components']>=3 or facts['expected_files']>=8 else int(facts['components']>=2 or facts['expected_files']>=4),
        'independent_concerns': min(2, facts['independent_concerns']-1),
        'security': 2*int(facts['security']),
        'architecture': 2*int(facts['architecture']),
        'resources': 2*int(facts['resources']),
        'ui_or_release': int(facts['ui'] or facts['release']),
        'independent_review': 2*int(facts['independent_review']),
        'specialization': max(int(bool(relevant)), {'unknown':0, 'useful':1, 'essential':2}[hints.specialization_value]),
    }
    score = sum(points.values())
    mode = profile.workflow_mode if profile.workflow_mode!='auto' else hints.mode
    # Explicit workflow choice/custom stage policy must not be silently pruned by auto.
    profile_pinned = any(s.workflow==base_id for s in profile.stage_overrides)
    pinned = bool(task.workflow or profile_pinned)
    if profile.workflow_mode=='direct' and pinned:
        raise BridgeError('Direct project mode conflicts with an explicit workflow or stage override.')
    policy_workflow = profile.workflow_mode=='workflow' or profile_pinned
    positive = bool(relevant or facts['independent_review'] or facts['independent_concerns']>1 or
                    task.kind=='implement_issue' and task.complexity!='simple')
    path = 'workflow' if pinned or policy_workflow or mode=='workflow' or (
        mode=='auto' and positive and score>=profile.decomposition_threshold) else 'direct'
    reasons = [f'{key}:+{value}' for key,value in points.items() if value]
    reasons.append('project_workflow_policy' if policy_workflow else 'explicit_'+mode if mode!='auto'
                   else 'positive_specialization_case' if path=='workflow' else 'direct_is_default')
    cap = engine.service.bridge.store.compute_cap(cfg.adaptive.default_cap)
    router = AdaptiveRouter(cfg, engine.service.bridge.store)

    def enabled(pair):
        return pair[0] not in profile.disabled_roles and (
            profile.enabled_roles is None or pair[0] in profile.enabled_roles)

    def candidates(pair):
        role, allowed = catalog.role(pair[0],profile)
        skill = catalog.skills[pair[1]]
        if not enabled(pair):
            return [], ['disabled_role']
        if skill.adapter=='repository_search':
            return [], []
        choices, blocked = router.candidates(role.category,skill.adapter,cap,
            2 if task.complexity=='moderate' else 1, requirements=role.requirements,allowed_models=allowed)
        choices, _ = router.selection(choices,skill.adapter,cap,len(task.context)+len(task.diff),
                                      {'complexity':task.complexity})
        return choices, blocked

    def compose(chosen_path):
        if chosen_path=='workflow' and (pinned or task.kind=='implement_issue' or task.kind=='review_change' and mode=='workflow'):
            stages = [s.model_dump()|{'skip':s.when!='always' and not (
                facts[s.when] or s.when=='security' and profile.require_security or
                s.when=='resources' and profile.require_resources)} for s in base.stages]
        else:
            stages = []
            if chosen_path=='direct':
                stages.append(stage('direct',primary,direct=True))
            else:
                # Forced decomposition is a comparison/override, not the auto default.
                if mode=='workflow' or policy_workflow:
                    stages.append(dict(id='explore',executor='local',role='repository-explorer',
                        skills=['repository-discovery','context-summary'],inputs_from=[],when='always',checkpoint=None,skip=False))
                selected = list(relevant)
                if not selected or facts['independent_concerns']>1 or mode=='workflow':
                    selected.insert(0,primary)
                selected = list(dict.fromkeys(selected))
                for index,pair in enumerate(selected):
                    if pair==PRIMARY['repository_discovery'] and stages:
                        continue  # explorer already supplied this result; don't scan again
                    inputs = ['explore'] if stages and stages[0]['id']=='explore' and pair==primary and not facts['independent_review'] else []
                    stages.append(stage('advice-'+str(index+1),pair,inputs=inputs))
            if task.kind=='implement_issue':
                # Direct issue analysis still leaves actual work with Codex, followed by validation.
                stages.extend([checkpoint('implement','implementation'),
                    stage('test',('test-engineer','test-failure-analysis')),
                    stage('review',('code-reviewer','code-review'))])
            stages.append(checkpoint())
        # Mandatory reviews cannot disappear under direct mode or optional role pruning.
        present = {(s['role'],skill) for s in stages if not s['skip'] and not s.get('direct') for skill in s['skills']}
        for index,pair in enumerate(required):
            if pair not in present:
                stages.insert(-1,stage('required-'+str(index+1),pair))
                present.add(pair)
        # Explicit task risk-review requests remain mandatory across the gate too.
        for flag,pair in [('security_review',SPECIALISTS['security']),('resource_review',SPECIALISTS['resources'])]:
            if getattr(task,flag) and pair not in present:
                stages.insert(-1,stage('requested-'+flag.replace('_','-'),pair))
                present.add(pair)
        return stages

    def estimate(stages):
        calls, seconds, known = 0, 0.0, True
        blocked = []
        for s in stages:
            if s['skip'] or s['executor']=='codex':
                continue
            if not enabled((s['role'],s['skills'][0])):
                blocked.append('disabled_role:'+s['role'])
            role, _ = catalog.role(s['role'],profile)
            stage_calls = sum(catalog.skills[k].adapter!='repository_search' for k in s['skills'])
            if stage_calls>min(cfg.adaptive.max_attempts,role.requirements.max_attempts):
                blocked.append('role_attempt_budget:'+s['role'])
            for skill_id in s['skills']:
                skill = catalog.skills[skill_id]
                choices, rejected = candidates((s['role'],skill_id))
                if skill.adapter=='repository_search':
                    continue
                calls += 1
                if not choices:
                    blocked.extend(rejected or ['no_eligible_model'])
                latency = engine.service.bridge.store.model_metrics(choices[0].name,skill.adapter).get('average_latency') if choices else None
                known &= latency is not None and latency>0
                seconds += latency or 0
        limits = base.limits
        tokens = calls*(cfg.num_ctx+cfg.max_output_tokens)
        output = calls*cfg.max_output_tokens
        fits = (len(stages)<=limits.max_stages and calls<=limits.max_attempts and
                tokens<=limits.max_reserved_tokens and output<=limits.max_output_tokens and
                (not known or seconds<=limits.max_seconds))
        return dict(first_pass_model_calls=calls,reserved_tokens=tokens,output_tokens_reserved=output,
            measured_time_estimate_seconds=round(seconds,3) if known and calls else None,
            time_limit_seconds=limits.max_seconds, fits_budget=fits,
            blocked_reasons=sorted(set(blocked)), installed_models_checked=False,
            excludes_retries=True, exact_context_fit_checked_at_execution=True)

    stages = compose(path)
    estimate_row = estimate(stages)
    # A constrained machine doesn't make specialization free. Optional decomposition can fall back.
    mandatory = bool(pinned or policy_workflow or required or task.security_review or task.resource_review)
    if path=='workflow' and mode=='auto' and not mandatory and (
            not estimate_row['fits_budget'] or estimate_row['blocked_reasons']):
        direct_stages = compose('direct')
        direct_estimate = estimate(direct_stages)
        if direct_estimate['fits_budget'] and not direct_estimate['blocked_reasons']:
            path, stages, estimate_row = 'direct', direct_stages, direct_estimate
            reasons.append('optional_decomposition_unavailable_within_cap_or_budget')
    if len(stages)>12 or len({s['id'] for s in stages})!=len(stages):
        raise BridgeError('Adaptive plan exceeds stage capacity or has conflicting stage IDs.')
    unresolved = facts['ambiguous'] or task.complexity=='complex'
    blockers = estimate_row['blocked_reasons'] + ([] if estimate_row['fits_budget'] else ['workflow_budget'])
    if unresolved:
        blockers.append('codex_must_scope_complex_or_ambiguous_work')
    direct_candidates, direct_blocks = candidates(primary) if primary else ([],['custom_workflow'])
    decision = dict(policy_version=1,path=path,mode=mode,selected_workflow=base_id if pinned or task.kind=='implement_issue'
        else 'adaptive-specialists' if path=='workflow' else None,
        score=score,threshold=profile.decomposition_threshold,reasons=reasons,indicators=facts,
        compute_tier=cap,decomposition_mandatory=mandatory,
        project_policy_mandatory=bool(policy_workflow or required),
        required_reviews=[{'role':r,'skill':s} for r,s in required],
        selected_roles=list(dict.fromkeys(s['role'] for s in stages if s['role'] and not s['skip'] and not s.get('direct'))),
        direct_model_candidates=[p.name for p in direct_candidates],direct_model_blocks=direct_blocks,
        estimate=estimate_row,runnable=not blockers,blockers=blockers)
    return dict(workflow=base_id,profile=profile_id,stages=stages,limits=base.limits.model_dump(),
        validation_status=task.validation_status,catalog=catalog.digest,codex_owns_decision=True,delegation=decision)
