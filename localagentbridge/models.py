"""Small explicit registry. Compute, memory and measured quality are separate."""
from dataclasses import dataclass, field
import re

TIERS = ('Light', 'Medium', 'Large', 'Maximum')
# Active billions, weight/runtime GiB, measured wall seconds. Not VRAM claims.
LIMITS = {'Light': (4, 6, 45), 'Medium': (8, 12, 120),
          'Large': (16, 24, 300), 'Maximum': (1000, 512, 600)}


@dataclass
class ModelProfile:
    name: str
    architecture: str
    total_parameters_b: float
    roles: list[str]
    active_parameters_b: float | None = None
    quantization: str = 'unknown'
    weight_gb: float = 0
    strength: int = 1
    enabled: bool = False
    display_name: str = ''
    min_tier: str | None = None
    experimental: bool = False
    disabled_reason: str = ''
    capabilities: list[str] = field(default_factory=list)
    reliability: dict = field(default_factory=dict)
    thinking: bool | str = False

    def __post_init__(self):
        if not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9._:/-]{0,159}', self.name) or 'cloud' in self.name.lower():
            raise ValueError('Registry models must be explicit local Ollama names')
        if self.architecture not in ('dense', 'moe') or not 0 < self.total_parameters_b <= 1000:
            raise ValueError('Invalid model architecture/parameter count')
        if self.architecture == 'dense' and self.active_parameters_b is None:
            self.active_parameters_b = self.total_parameters_b
        if self.active_parameters_b is not None and not 0 < self.active_parameters_b <= self.total_parameters_b:
            raise ValueError('Active parameters must be positive and no greater than total')
        if self.architecture == 'dense' and self.active_parameters_b != self.total_parameters_b:
            raise ValueError('Dense active and total parameter counts must match')
        if (not self.roles and not self.capabilities) or not set(self.roles) <= {'general', 'coding', 'reasoning'}:
            raise ValueError('Invalid supported roles')
        if not 0 < self.weight_gb <= 1000 or not 1 <= self.strength <= 10 or type(self.enabled) is not bool:
            raise ValueError('Invalid model weight size, strength or enabled flag')
        if self.min_tier is not None and self.min_tier not in TIERS:
            raise ValueError('min_tier must name a compute tier')
        if type(self.experimental) is not bool or len(self.display_name) > 160 or len(self.disabled_reason) > 500:
            raise ValueError('Invalid model display metadata')
        if not set(self.capabilities) <= {'general', 'coding', 'reasoning', 'vision', 'embedding'}:
            raise ValueError('Unknown model capability')
        if type(self.thinking) is not bool and self.thinking not in ('low', 'medium', 'high'):
            raise ValueError('thinking must be a boolean or low/medium/high')
        for metrics in self.reliability.values():
            if set(metrics) != {'reviewed_cases', 'accepted_rate', 'rejected_rate'} or type(metrics['reviewed_cases']) is not int or metrics['reviewed_cases'] < 1:
                raise ValueError('Reliability requires reviewed_cases, accepted_rate and rejected_rate')
            if not 0 <= metrics['accepted_rate'] <= 1 or not 0 <= metrics['rejected_rate'] <= 1 or metrics['accepted_rate'] + metrics['rejected_rate'] > 1.000001:
                raise ValueError('Invalid reviewed reliability rates')


@dataclass
class AdaptiveConfig:
    enabled: bool = False  # configs without this section retain v0.2 behavior
    default_cap: str = 'Medium'
    max_attempts: int = 2
    memory_budget_gb: float = 12
    runtime_reserve_gb: float = 2
    min_reviewed_cases: int = 3
    min_accepted_rate: float = 0.5
    max_rejected_rate: float = 0.5
    # Optional quality-first policy. Omitted fields preserve smallest-first routing.
    preferred_model: str | None = None
    lightweight_model: str | None = None
    trivial_max_chars: int = 1200
    maximum_trivial_max_chars: int = 256
    limits: dict = field(default_factory=lambda: dict(LIMITS))

    def __post_init__(self):
        if self.default_cap not in TIERS or type(self.enabled) is not bool or type(self.max_attempts) is not int or not 1 <= self.max_attempts <= 3:
            raise ValueError('Invalid compute cap or automatic-attempt limit')
        if not 1 <= self.memory_budget_gb <= 1024 or not 0 <= self.runtime_reserve_gb <= 32:
            raise ValueError('Invalid local memory budget')
        if not 1 <= self.min_reviewed_cases <= 100 or not 0 <= self.min_accepted_rate <= 1 or not 0 <= self.max_rejected_rate <= 1:
            raise ValueError('Invalid benchmark reliability threshold')
        if bool(self.preferred_model) != bool(self.lightweight_model):
            raise ValueError('Set both preferred_model and lightweight_model, or neither')
        if not 0 <= self.maximum_trivial_max_chars <= self.trivial_max_chars <= 24000:
            raise ValueError('Invalid trivial-work character thresholds')
        self.limits = dict(LIMITS) | self.limits
        if set(self.limits) != set(TIERS):
            raise ValueError('Compute limits must use the four named tiers')
        previous = (0, 0, 0)
        for tier in TIERS:
            values = self.limits[tier]
            if len(values) != 3 or any(v <= 0 or v < p for v, p in zip(values, previous)):
                raise ValueError('Compute limits must be positive and increase monotonically')
            previous = values


def eligibility(profile, policy, cap, metrics=None):
    metrics = metrics or {}
    active, memory, latency = policy.limits[cap]
    # An unknown MoE active count is NOT silently treated as a tiny dense model.
    cost = profile.active_parameters_b if profile.active_parameters_b is not None else profile.total_parameters_b
    footprint = max(profile.weight_gb + policy.runtime_reserve_gb, metrics.get('model_memory_gb') or 0)
    if profile.experimental and cap != 'Maximum':
        return False, 'experimental_cap'
    # Explicit tiers encode reviewed usefulness; legacy profiles retain numeric gates.
    if (profile.min_tier and TIERS.index(cap) < TIERS.index(profile.min_tier)) or (not profile.min_tier and cost > active):
        return False, 'compute_cap'
    if footprint > min(memory, policy.memory_budget_gb):
        return False, 'memory_budget'
    if (metrics.get('average_latency') or 0) > latency:
        return False, 'measured_latency'
    return True, None


def task_eligibility(profile, policy, cap, metrics, tool):
    allowed, reason = eligibility(profile, policy, cap, metrics)
    if not allowed:
        return allowed, reason
    quality = metrics if metrics.get('reviewed_cases', 0) else profile.reliability.get(tool, {})
    if quality.get('reviewed_cases', 0) >= policy.min_reviewed_cases and (
        quality['accepted_rate'] < policy.min_accepted_rate or quality['rejected_rate'] > policy.max_rejected_rate):
        return False, 'benchmark_reliability'
    return True, None


def model_tier(profile, policy):
    if profile.experimental:
        return 'Maximum'
    if profile.min_tier:
        return profile.min_tier
    cost = profile.active_parameters_b or profile.total_parameters_b
    return next((tier for tier in TIERS if cost <= policy.limits[tier][0] and
                 profile.weight_gb + policy.runtime_reserve_gb <= policy.limits[tier][1]), 'Maximum')


async def registry_status(config, transport=None):
    """Inspectable static registry joined with measured local metadata."""
    from dataclasses import asdict
    from .routing import inventory, canonical, install_command
    from .telemetry import Store
    installed = await inventory(config, transport)
    store = Store(config.data_dir)
    cap = store.compute_cap(config.adaptive.default_cap)
    rows = []
    for profile in config.model_registry:
        measurements = store.model_metrics(profile.name)
        allowed, reason = eligibility(profile, config.adaptive, cap, measurements)
        found = canonical(profile.name) in installed
        rows.append(asdict(profile) | dict(installed=found, cap=cap,
            resource_eligible=allowed, resource_block=reason, measurements=measurements,
            install_command=None if found else install_command(profile.name)))
    return rows
