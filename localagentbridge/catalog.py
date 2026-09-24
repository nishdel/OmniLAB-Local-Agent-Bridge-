"""Strict, data-only workflow definitions. No project code or templates are executed."""
from copy import deepcopy
import hashlib
from pathlib import Path
import stat
import tomllib
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

ID = Annotated[str, Field(pattern=r'^[a-z][a-z0-9_-]{0,63}$')]
Text = Annotated[str, Field(max_length=2000)]
Names = Annotated[list[ID], Field(max_length=16)]
Category = Literal['general', 'coding', 'reasoning']
Adapter = Literal['repository_search', 'summarize_context', 'analyze_code', 'analyze_test_output',
                  'review_diff', 'implementation_plan']


class Strict(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, validate_default=True)


class Limits(Strict):
    max_stages: Annotated[int, Field(ge=1, le=12)] = 12
    max_attempts: Annotated[int, Field(ge=1, le=24)] = 12
    max_corrections: Annotated[int, Field(ge=0, le=8)] = 3
    max_reserved_tokens: Annotated[int, Field(ge=1, le=500000)] = 120000
    max_output_tokens: Annotated[int, Field(ge=1, le=28800)] = 7200
    max_input_chars: Annotated[int, Field(ge=1, le=576000)] = 120000
    max_seconds: Annotated[int, Field(ge=1, le=1800)] = 900

    def intersect(self, other):
        return Limits(**{k: min(v, getattr(other, k)) for k, v in self.model_dump().items()})


class Requirements(Strict):
    min_strength: Annotated[int, Field(ge=1, le=10)] = 1
    min_context: Annotated[int, Field(ge=2048, le=16384)] = 2048
    capabilities: Annotated[list[Literal['general', 'coding', 'reasoning', 'vision', 'embedding']],
                            Field(max_length=5)] = []
    timeout_seconds: Annotated[int, Field(ge=1, le=600)] = 180
    max_attempts: Annotated[int, Field(ge=1, le=3)] = 2
    auto_escalate: bool = True

    def intersect(self, other):
        return Requirements(min_strength=max(self.min_strength, other.min_strength),
            min_context=max(self.min_context, other.min_context),
            capabilities=sorted(set(self.capabilities + other.capabilities)),
            timeout_seconds=min(self.timeout_seconds, other.timeout_seconds),
            max_attempts=min(self.max_attempts, other.max_attempts),
            auto_escalate=self.auto_escalate and other.auto_escalate)


class Definition(Strict):
    schema_version: Literal[1] = 1
    id: ID
    version: Annotated[str, Field(pattern=r'^[a-zA-Z0-9_.-]{1,32}$')] = '1.0'
    description: Annotated[str, Field(min_length=1, max_length=300)]


class Skill(Definition):
    adapter: Adapter
    instruction: Text
    input: Literal['context', 'diff', 'test_output', 'issue', 'search']


class Role(Definition):
    skills: Annotated[list[ID], Field(min_length=1, max_length=8)]
    instruction: Text
    category: Category = 'general'
    authority: Literal['advisory'] = 'advisory'
    requirements: Requirements = Field(default_factory=Requirements)


class Stage(Strict):
    id: ID
    executor: Literal['local', 'codex'] = 'local'
    role: ID | None = None
    skills: Annotated[list[ID], Field(max_length=8)] = []
    inputs_from: Annotated[list[ID], Field(max_length=4)] = []
    when: Literal['always', 'security', 'resources'] = 'always'
    checkpoint: Literal['implementation', 'decision', 'final'] | None = None

    @model_validator(mode='after')
    def owner(self):
        if self.executor == 'local':
            if not self.role or not self.skills or self.checkpoint:
                raise ValueError('Local stages require a role/skills and cannot be checkpoints')
        elif self.role or self.skills or not self.checkpoint or self.when != 'always' or self.inputs_from:
            raise ValueError('Codex checkpoints cannot have local execution or conditions')
        return self


class Workflow(Definition):
    task_kinds: Annotated[list[ID], Field(min_length=1, max_length=8)]
    stages: Annotated[list[Stage], Field(min_length=1, max_length=12)]
    limits: Limits = Field(default_factory=Limits)

    @model_validator(mode='after')
    def order(self):
        seen = set()
        since_checkpoint = set()
        for index, stage in enumerate(self.stages):
            if stage.id in seen or len(set(stage.skills)) != len(stage.skills):
                raise ValueError('Duplicate stage or composed skill')
            if not set(stage.inputs_from) <= since_checkpoint:
                raise ValueError('Inputs must reference earlier local stages after the last checkpoint')
            if stage.checkpoint == 'final' and index != len(self.stages)-1:
                raise ValueError('Final verification must be last')
            seen.add(stage.id)
            if stage.executor == 'codex':
                since_checkpoint.clear()
            else:
                since_checkpoint.add(stage.id)
        if self.stages[-1].checkpoint not in ('final', 'decision'):
            raise ValueError('Every workflow ends with an unconditional Codex decision')
        if len(self.stages) > self.limits.max_stages:
            raise ValueError('Workflow exceeds stage budget')
        return self


class RoleOverride(Strict):
    role: ID
    instruction: Text = ''
    requirements: Requirements = Field(default_factory=Requirements)
    # Explicit project overrides may constrain exact models; generic roles cannot.
    allowed_models: Annotated[list[Annotated[str, Field(min_length=1, max_length=160)]], Field(max_length=16)] | None = None


class StageOverride(Strict):
    workflow: ID
    stage: ID
    disabled: bool = False
    replacement: Stage | None = None

    @model_validator(mode='after')
    def one_change(self):
        if self.disabled == (self.replacement is not None):
            raise ValueError('Choose either disabled or replacement')
        return self


class RequiredReview(Strict):
    role: ID
    skill: ID
    when: Literal['always', 'security', 'dependencies', 'resources', 'architecture', 'ui', 'release'] = 'always'


class ProjectProfile(Definition):
    workflows: Annotated[list[ID], Field(min_length=1, max_length=16)]
    enabled_roles: Names | None = None
    disabled_roles: Names = []
    instruction: Text = ''
    authority_documents: Annotated[list[Annotated[str, Field(max_length=240)]], Field(max_length=12)] = []
    require_security: bool = False
    require_resources: bool = False
    role_overrides: Annotated[list[RoleOverride], Field(max_length=16)] = []
    stage_overrides: Annotated[list[StageOverride], Field(max_length=16)] = []
    limits: Limits = Field(default_factory=Limits)
    workflow_mode: Literal['auto', 'direct', 'workflow'] = 'auto'
    decomposition_threshold: Annotated[int, Field(ge=1, le=12)] = 3
    required_reviews: Annotated[list[RequiredReview], Field(max_length=8)] = []


class AgenticConfig(Strict):
    enabled: bool = False
    catalog_root: str | None = None
    project_profile: ID = 'generic'
    limits: Limits = Field(default_factory=Limits)


def safe_relative(name):
    path = Path(name)
    if not name or path.is_absolute() or path.drive or '..' in path.parts or ':' in name or '\\' in name:
        raise ValueError('Catalog references must be confined relative paths using /')


def _files(root):
    """Bound directory enumeration too; never follow links into a catalog."""
    if not root.is_dir():
        raise ValueError('Catalog root is not a directory')
    for component in (root, *root.parents):
        info = component.lstat()
        if component.is_symlink() or getattr(info, 'st_file_attributes', 0) & 0x400:
            raise ValueError('Catalog paths cannot pass through links or reparse points')
    total = 0
    for kind in ('skills', 'roles', 'workflows', 'project-profiles'):
        directory = root / kind
        if not directory.exists():
            continue
        info = directory.lstat()
        if directory.is_symlink() or getattr(info, 'st_file_attributes', 0) & 0x400 or not directory.is_dir():
            raise ValueError('Catalog kinds must be regular directories')
        for count, path in enumerate(directory.iterdir(), 1):
            if count > 64:
                raise ValueError('Catalog kind has more than 64 entries')
            info = path.lstat()
            if not stat.S_ISREG(info.st_mode) or path.is_symlink() or getattr(info, 'st_file_attributes', 0) & 0x400:
                raise ValueError('Catalog entries must be regular files')
            if path.suffix != '.toml':
                raise ValueError('Catalog entries must be TOML')
            with path.open('rb') as stream:
                raw = stream.read(32769)
            total += len(raw)
            if len(raw) > 32768 or total > 1048576:
                raise ValueError('Catalog exceeds file or total byte bound')
            yield kind, path.name, raw


class Catalog:
    def __init__(self, config):
        self.config = config
        self.skills, self.roles, self.workflows, self.profiles = {}, {}, {}, {}
        kinds = {'skills': (Skill, self.skills), 'roles': (Role, self.roles),
                 'workflows': (Workflow, self.workflows), 'project-profiles': (ProjectProfile, self.profiles)}
        roots = [Path(__file__).with_name('definitions')]
        if config.catalog_root:
            roots.append(Path(config.catalog_root).absolute())
        digest = hashlib.sha256()
        total_bytes = 0
        for root in roots:
            for kind, name, raw in sorted(_files(root)):
                total_bytes += len(raw)
                if total_bytes > 1048576:
                    raise ValueError('Combined catalog exceeds total byte bound')
                model, collection = kinds[kind]
                definition = model.model_validate(tomllib.loads(raw.decode('utf-8-sig')))
                if definition.id in collection:
                    raise ValueError('Duplicate catalog ID: '+definition.id)
                collection[definition.id] = definition
                digest.update(kind.encode()+b'\0'+name.encode()+b'\0'+raw)
        self.digest = digest.hexdigest()
        for role in self.roles.values():
            if len(set(role.skills)) != len(role.skills) or not set(role.skills) <= self.skills.keys():
                raise ValueError('Role has unknown or duplicate skills: '+role.id)
        for workflow in self.workflows.values():
            self.validate_stages(workflow)
        for profile in self.profiles.values():
            for review in profile.required_reviews:
                role = self.roles.get(review.role)
                if (not role or review.skill not in role.skills or review.role in profile.disabled_roles or
                        (profile.enabled_roles is not None and review.role not in profile.enabled_roles)):
                    raise ValueError('Required review uses an unknown, disabled or incompatible role/skill')
            names = [r.role for r in profile.role_overrides]
            stage_keys = [(s.workflow, s.stage) for s in profile.stage_overrides]
            if len(set(names)) != len(names) or len(set(stage_keys)) != len(stage_keys):
                raise ValueError('Duplicate project override')
            if not set(profile.workflows) <= self.workflows.keys():
                raise ValueError('Unknown profile workflow')
            if not set((profile.enabled_roles or [])+profile.disabled_roles+names) <= self.roles.keys():
                raise ValueError('Unknown profile role')
            for name in profile.authority_documents:
                safe_relative(name)
            for change in profile.stage_overrides:
                if change.workflow not in profile.workflows:
                    raise ValueError('Override workflow is not selected by profile')
            for workflow_id in profile.workflows:
                self.resolve(workflow_id, profile.id)
        if config.project_profile not in self.profiles:
            raise ValueError('Unknown active project profile')

    def validate_stages(self, workflow):
        for stage in workflow.stages:
            if stage.executor == 'local' and (stage.role not in self.roles or
                    not set(stage.skills) <= set(self.roles[stage.role].skills)):
                raise ValueError('Stage has unknown role or incompatible skill composition')

    def resolve(self, workflow_id, profile_id=None):
        profile = self.profiles.get(profile_id or self.config.project_profile)
        if not profile or workflow_id not in profile.workflows:
            raise ValueError('Workflow is not enabled by the project profile')
        workflow = self.workflows[workflow_id].model_copy(deep=True)
        for change in profile.stage_overrides:
            if change.workflow != workflow_id:
                continue
            indices = [i for i, stage in enumerate(workflow.stages) if stage.id == change.stage]
            if not indices:
                raise ValueError('Unknown override stage')
            index = indices[0]
            original = workflow.stages[index]
            if original.executor == 'codex':
                raise ValueError('Profiles cannot remove or replace Codex checkpoints')
            if change.disabled:
                workflow.stages.pop(index)
            else:
                if change.replacement.id != original.id or change.replacement.executor != 'local':
                    raise ValueError('Stage replacement must preserve ID and local ownership')
                workflow.stages[index] = deepcopy(change.replacement)
        workflow.limits = workflow.limits.intersect(profile.limits).intersect(self.config.limits)
        workflow = Workflow.model_validate(workflow.model_dump())
        self.validate_stages(workflow)
        for stage in workflow.stages:
            if stage.executor == 'local' and (stage.role in profile.disabled_roles or
                    (profile.enabled_roles is not None and stage.role not in profile.enabled_roles)):
                raise ValueError('Workflow uses a disabled role; explicitly adjust its stages')
        return workflow, profile

    def role(self, role_id, profile):
        role = self.roles[role_id].model_copy(deep=True)
        allowed = None
        for override in profile.role_overrides:
            if override.role == role_id:
                role.instruction += '\n'+override.instruction
                role.requirements = role.requirements.intersect(override.requirements)
                allowed = override.allowed_models
        return role, allowed

    def inspect(self):
        return {'digest': self.digest, 'skills': sorted(self.skills), 'roles': sorted(self.roles),
                'workflows': sorted(self.workflows), 'project_profiles': sorted(self.profiles),
                'authority': 'advisory; Codex owns implementation and final verification'}
