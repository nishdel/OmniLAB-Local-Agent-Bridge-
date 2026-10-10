"""Opt-in supervisor contracts. Orchestration, inference and execution are separate."""
import hashlib
import json
from pathlib import PurePosixPath
from typing import Annotated, Literal

from pydantic import Field, model_validator
from .catalog import Strict, Catalog

Lane = Literal['codex_direct', 'local_advisory', 'local_implementation']
Short = Annotated[str, Field(min_length=1, max_length=2000)]
Key = Annotated[str, Field(pattern=r'^[a-zA-Z0-9][a-zA-Z0-9_.-]{0,100}$')]


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                    allow_nan=False, separators=(',', ':')).encode()).hexdigest()


def safe_path(value):
    p = PurePosixPath(value)
    if (not value or p.is_absolute() or '\\' in value or ':' in value or
            any(s in ('', '.', '..') for s in value.split('/')) or
            any(s.lower() in ('.git', '.codex', '.aws', '.ssh', '.env') for s in p.parts) or
            any(ord(c) < 32 for c in value)):
        raise ValueError('Unsafe contract path: ' + value)
    return value


class TaskLimits(Strict):
    steps: Annotated[int, Field(ge=1, le=80)] = 20
    output_tokens: Annotated[int, Field(ge=64, le=8192)] = 1024
    output_bytes: Annotated[int, Field(ge=1024, le=2000000)] = 65536
    context_tokens: Annotated[int, Field(ge=2048, le=131072)] = 16384
    context_safety_tokens: Annotated[int, Field(ge=0, le=8192)] = 0
    self_repair_cycles: Annotated[int, Field(ge=0, le=2)] | None = None
    implementation_attempts: Annotated[int, Field(ge=1, le=2)] = 2
    transport_retries: Annotated[int, Field(ge=0, le=2)] = 1
    inference_deadline_seconds: Annotated[int, Field(ge=1, le=3600)] | None = None
    attempt_seconds: Annotated[int, Field(ge=1, le=1800)] | None = None
    test_seconds: Annotated[int, Field(ge=1, le=900)] = 120
    memory_mb: Annotated[int, Field(ge=256, le=16384)] = 2048
    cpus: Annotated[int, Field(ge=1, le=8)] = 2
    snapshot_bytes: Annotated[int, Field(ge=1024, le=64000000)] = 16000000


class Check(Strict):
    id: Key
    argv: Annotated[list[Annotated[str, Field(min_length=1, max_length=1000)]], Field(min_length=1, max_length=32)]
    covers: Annotated[list[Key], Field(min_length=1, max_length=32)]


class Contract(Strict):
    schema_version: Literal[1] = 1
    task_id: Key
    objective: Short
    requirement_ref: Short
    acceptance: dict[Key, Short]
    non_goals: Annotated[list[Short], Field(max_length=20)] = []
    repository: Short
    base_revision: Annotated[str, Field(pattern=r'^[0-9a-f]{40,64}$')]
    permitted_files: Annotated[list[str], Field(max_length=40)] = []
    context_files: Annotated[list[str], Field(max_length=80)] = []
    acceptance_files: Annotated[list[str], Field(max_length=80)] = []
    operations: list[Literal['read', 'edit', 'test']] = ['read']
    context: Annotated[str, Field(max_length=16000)] = ''
    skills: Annotated[list[str], Field(max_length=8)] = []
    role: str = 'local-worker'
    parent_id: Key | None = None
    dependencies: Annotated[list[Key], Field(max_length=40)] = []
    requested_lane: Lane = 'codex_direct'
    orchestration: Literal['auto', 'direct', 'workflow'] = 'auto'
    backend: Literal['ollama', 'strata'] = 'ollama'
    model: Annotated[str, Field(min_length=1, max_length=160)]
    exact_identity: str | None = None
    require_exact: bool = True
    risk: Literal['low', 'architectural', 'cross_cutting', 'security', 'destructive', 'unknown'] = 'unknown'
    ambiguity: bool = True
    coherent_scope: bool = False
    reversible: bool = False
    category: Key = 'unspecified'
    supervisor_approved: bool = False
    review_required: Literal[True] = True
    checks: Annotated[list[Check], Field(max_length=20)] = []
    limits: TaskLimits = Field(default_factory=TaskLimits)
    override_lane: Lane | None = None
    override_reason: Annotated[str, Field(max_length=2000)] = ''

    @model_validator(mode='after')
    def validate_scope(self):
        if not self.acceptance or len(self.acceptance) > 32:
            raise ValueError('Supply bounded, identified acceptance criteria')
        for name in self.permitted_files + self.context_files + self.acceptance_files:
            safe_path(name)
        if set(self.permitted_files) & set(self.acceptance_files):
            raise ValueError('Worker cannot edit authoritative acceptance files')
        if len(set(self.dependencies)) != len(self.dependencies) or self.task_id in self.dependencies:
            raise ValueError('Duplicate or self dependency')
        if len(set(self.skills)) != len(self.skills):
            raise ValueError('Duplicate skills')
        if self.override_lane and not self.override_reason.strip():
            raise ValueError('Supervisor override requires a logged reason')
        if self.role == 'local-reviewer' and ('edit' in self.operations or self.permitted_files):
            raise ValueError('Reviewer is read-only')
        if any(not set(c.covers) <= self.acceptance.keys() for c in self.checks):
            raise ValueError('Check references unknown acceptance criterion')
        if len({c.id for c in self.checks}) != len(self.checks):
            raise ValueError('Duplicate check identifier')
        return self


def validate_graph(contracts):
    nodes = {c.task_id: c for c in contracts}
    if len(nodes) != len(contracts):
        raise ValueError('Duplicate task IDs')
    protected = {path for c in contracts for path in c.acceptance_files}
    if any(set(c.permitted_files) & protected for c in contracts):
        raise ValueError('A task cannot edit another task acceptance authority')
    seen, active = set(), set()
    def visit(key):
        if key in active:
            raise ValueError('Dependency or parent cycle')
        if key in seen:
            return
        if key not in nodes:
            raise ValueError('Unknown dependency or parent: ' + key)
        active.add(key)
        c = nodes[key]
        for dep in c.dependencies + ([c.parent_id] if c.parent_id else []):
            visit(dep)
        active.remove(key)
        seen.add(key)
    for key in nodes:
        visit(key)


def selected_skills(contract, agentic):
    catalog = Catalog(agentic)
    role = contract.role
    if role not in ('local-worker', 'local-reviewer'):
        if role not in catalog.roles:
            raise ValueError('Unknown role')
        # Old IDs retain their compatible skill restriction; they are personas.
        if not set(contract.skills) <= set(catalog.roles[role].skills):
            raise ValueError('Skill is not compatible with legacy role alias')
        role = 'local-reviewer' if role.endswith('reviewer') else 'local-worker'
    if role == 'local-reviewer' and ('edit' in contract.operations or contract.permitted_files):
        raise ValueError('Read-only role cannot receive edit permissions')
    result = []
    for key in contract.skills:
        if key not in catalog.skills:
            raise ValueError('Unknown canonical skill: ' + key)
        profile = catalog.profiles[agentic.project_profile]
        compatible = [r for r in catalog.roles.values() if key in r.skills and
                      r.id not in profile.disabled_roles and
                      (profile.enabled_roles is None or r.id in profile.enabled_roles) and
                      (contract.role in ('local-worker','local-reviewer') or r.id == contract.role)]
        if not compatible:
            raise ValueError('Profile disables the selected skill/role')
        resolved_roles = [catalog.role(r.id, profile) for r in compatible]
        if not any((allowed is None or contract.model in allowed) and
                   contract.limits.context_tokens >= resolved.requirements.min_context
                   for resolved, allowed in resolved_roles):
            raise ValueError('Profile model/context restrictions block selection')
        skill = catalog.skills[key]
        result.append(dict(id=key, version=skill.version, sha256=digest(skill.model_dump()),
                           instruction=skill.instruction))
    return role, result


def route(contract, capability, policy):
    """Use supplied classification, never infer task difficulty from text."""
    lane = contract.override_lane or contract.requested_lane
    reasons = []
    if not contract.supervisor_approved:
        reasons.append('Supervisor contract approval required')
    if contract.ambiguity or contract.risk == 'unknown':
        reasons.append('Return missing/ambiguous requirements or classification to Codex')
    if contract.orchestration == 'workflow' and lane != 'codex_direct':
        reasons.append('Use the existing workflow-submit/next/checkpoint interface for workflow orchestration; contract jobs are bounded single stages')
    if lane == 'local_implementation':
        if contract.risk != 'low' or not contract.coherent_scope or not contract.reversible:
            reasons.append('Implementation requires coherent, reversible low-risk scope')
        covered = {x for check in contract.checks for x in check.covers}
        if (not contract.checks or covered != set(contract.acceptance) or
                not contract.acceptance_files or not contract.permitted_files or
                not {'read', 'edit', 'test'} <= set(contract.operations)):
            reasons.append('Implementation requires protected acceptance checks and explicit edit/test scope')
        if not policy.get('implementation_enabled'):
            reasons.append('Implementation is disabled')
        if not capability.get('sandbox_available'):
            reasons.append('Restricted sandbox unavailable')
        if not capability.get('tool_roundtrip_verified') or not capability.get('context_verified'):
            reasons.append('Exact provider/model/context has no complete agent tool-roundtrip qualification')
        qualification = [contract.backend, contract.exact_identity, contract.category, contract.limits.context_tokens]
        scoped = digest(contract.model_dump()) in policy.get('scoped_task_approvals', [])
        if qualification not in policy.get('qualified', []) and not scoped:
            if not (policy.get('pilot_enabled') and contract.category in policy.get('pilot_categories', [])):
                reasons.append('Provider/model/category is unqualified; explicit pilot required')
    if lane != 'codex_direct':
        if not policy.get('enabled'):
            reasons.append('Selective execution is disabled')
        if not capability.get('ready'):
            reasons.append(capability.get('reason', 'Provider unavailable'))
        if contract.require_exact and (not contract.exact_identity or
                capability.get('identity') != contract.exact_identity or not capability.get('identity_verified')):
            reasons.append('Exact serving identity is missing, changed or unverified')
        if capability.get('context_tokens', 0) < contract.limits.context_tokens:
            reasons.append('Provider context capacity is insufficient')
    effective = 'codex_direct' if reasons else lane
    return dict(requested_lane=contract.requested_lane, effective_lane=effective,
                backend=contract.backend, model=contract.model, exact_identity=contract.exact_identity,
                reason='; '.join(reasons) or ('Supervisor approved this exact scoped contract' if
                    lane == 'local_implementation' and scoped else 'Supervisor selected ' + lane),
                override={'lane': contract.override_lane, 'reason': contract.override_reason} if contract.override_lane else None,
                orchestration=contract.orchestration, return_to_supervisor=effective == 'codex_direct')
