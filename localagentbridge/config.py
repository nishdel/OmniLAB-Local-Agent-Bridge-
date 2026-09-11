from dataclasses import dataclass, field
import ipaddress
import os
from pathlib import Path
import tomllib
from urllib.parse import urlsplit
import re
from .models import ModelProfile, AdaptiveConfig

ROUTES = {
    "find_relevant_context": "general", "summarize_context": "general",
    "analyze_code": "coding", "analyze_test_output": "coding", "review_diff": "coding",
    "triage_task": "reasoning", "second_opinion": "reasoning",
}


@dataclass
class SearchConfig:
    max_files: int = 2000
    max_entries: int = 10000
    max_file_bytes: int = 128000
    max_total_bytes: int = 8_000_000
    max_seconds: float = 5
    max_candidates: int = 12
    max_results: int = 5
    exclude: list[str] = field(default_factory=lambda: ["data/", ".*test*/", "*.lock*", "requirements.lock.txt"])

    def __post_init__(self):
        for key, low, high in (("max_files", 1, 10000), ("max_entries", 1, 100000),
                               ("max_file_bytes", 100, 1_000_000), ("max_total_bytes", 100, 32_000_000),
                               ("max_seconds", 0.1, 30), ("max_candidates", 1, 20), ("max_results", 1, 8)):
            if not low <= getattr(self, key) <= high:
                raise ValueError(f"search.{key} must be between {low} and {high}")


@dataclass
class DelegationConfig:
    local_first: bool = True
    min_context_chars: int = 1500
    min_file_count: int = 3
    max_files_for_local_analysis: int = 8
    min_confidence: str = "medium"
    min_compression: float = 0.25
    max_failed_local_attempts: int = 2

    def __post_init__(self):
        if type(self.local_first) is not bool or type(self.max_failed_local_attempts) is not int or not 1 <= self.max_failed_local_attempts <= 3:
            raise ValueError("Invalid local-first policy or failed-attempt limit")
        if not 0 <= self.min_context_chars <= 24000 or not 1 <= self.min_file_count <= 100:
            raise ValueError("Invalid delegation minimum thresholds")
        if not self.min_file_count <= self.max_files_for_local_analysis <= 100:
            raise ValueError("delegation maximum file count must be >= minimum")
        if self.min_confidence not in ("low", "medium", "high") or not 0 <= self.min_compression <= 1:
            raise ValueError("Invalid delegation confidence/compression threshold")


@dataclass
class Config:
    model: str = "qwen3:4b"
    endpoint: str = "http://localhost:11434"
    allow_remote: bool = False
    max_input_chars: int = 10000
    max_output_tokens: int = 600
    max_output_bytes: int = 3000
    num_ctx: int = 8192
    timeout_seconds: float = 180
    data_dir: Path = field(default_factory=lambda: Path(os.getenv("LOCALAPPDATA", str(Path.home()))) / "LocalAgentBridge")
    poll_seconds: float = 2
    discover_seconds: float = 30
    collapse_seconds: float = 10
    stale_seconds: float = 300
    otel_port: int = 4318
    codex_home: Path = field(default_factory=lambda: Path(os.getenv("CODEX_HOME", str(Path.home() / ".codex"))))
    source_root: Path | None = None
    # Absence of roles preserves v0.1's single-model configuration.
    roles: dict[str, str] = field(default_factory=dict)
    routes: dict[str, str] = field(default_factory=lambda: dict(ROUTES))
    consensus_roles: list[str] = field(default_factory=lambda: ["coding", "reasoning"])
    search: SearchConfig = field(default_factory=SearchConfig)
    delegation: DelegationConfig = field(default_factory=DelegationConfig)
    model_registry: list[ModelProfile] = field(default_factory=list)
    adaptive: AdaptiveConfig = field(default_factory=AdaptiveConfig)

    def __post_init__(self):
        if isinstance(self.adaptive, dict):
            self.adaptive = AdaptiveConfig(**self.adaptive)
        self.model_registry = [ModelProfile(**p) if isinstance(p, dict) else p for p in self.model_registry]
        from .routing import canonical
        if len({canonical(p.name) for p in self.model_registry}) != len(self.model_registry):
            raise ValueError('Duplicate registry model names')
        if self.adaptive.enabled and not self.model_registry:
            raise ValueError('Adaptive routing requires a model registry')
        if self.adaptive.enabled and self.max_output_bytes < 1800:
            raise ValueError('Adaptive routing requires max_output_bytes >= 1800')
        if isinstance(self.search, dict):
            self.search = SearchConfig(**self.search)
        if isinstance(self.delegation, dict):
            self.delegation = DelegationConfig(**self.delegation)
        self.routes = ROUTES | self.routes
        if self.roles and set(self.roles) != {"general", "coding", "reasoning"}:
            raise ValueError("roles must define exactly general, coding and reasoning")
        if self.adaptive.enabled:
            profiles = {p.name:p for p in self.model_registry}
            if self.adaptive.preferred_model:
                preferences = (self.adaptive.preferred_model, self.adaptive.lightweight_model)
                if len(set(preferences)) != 2 or any(n not in profiles or not profiles[n].enabled for n in preferences):
                    raise ValueError('Quality preferences must name two distinct enabled registered models')
                if profiles[preferences[0]].strength <= profiles[preferences[1]].strength:
                    raise ValueError('Preferred model must have greater reviewed strength than lightweight model')
            if not self.roles or any(model not in profiles or role not in profiles[model].roles for role,model in self.roles.items()):
                raise ValueError('Adaptive role defaults must be registered with the matching supported role')
        if set(self.routes) != set(ROUTES) or any(r not in ("general", "coding", "reasoning") for r in self.routes.values()):
            raise ValueError("Invalid tool-to-role routing")
        if not 2 <= len(self.consensus_roles) <= 3 or len(set(self.consensus_roles)) != len(self.consensus_roles):
            raise ValueError("consensus_roles must contain two or three distinct roles")
        if any(r not in ("general", "coding", "reasoning") for r in self.consensus_roles):
            raise ValueError("Unknown consensus role")
        for model in [self.model, *self.roles.values()]:
            if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9._:/-]{0,159}", model) or "cloud" in model.lower():
                raise ValueError("Use a local Ollama model name; cloud models and shell syntax are forbidden")
        self.data_dir = Path(self.data_dir).expanduser().resolve()
        self.codex_home = Path(self.codex_home).expanduser().resolve()
        if self.source_root is not None:
            self.source_root = Path(self.source_root).expanduser().resolve(strict=True)
            if not self.source_root.is_dir():
                raise ValueError("source_root must be a directory")
        url = urlsplit(self.endpoint)
        if url.scheme not in ("http", "https") or not url.hostname or url.username or url.password or url.query or url.fragment or url.path not in ("", "/"):
            raise ValueError("endpoint must be an HTTP(S) origin without credentials, path, query or fragment")
        try:
            loopback = ipaddress.ip_address(url.hostname).is_loopback
        except ValueError:
            loopback = url.hostname.lower() == "localhost"
        if not loopback and not self.allow_remote:
            raise ValueError("Remote Ollama endpoint requires allow_remote = true")
        if not loopback and (self.roles or self.model_registry):
            raise ValueError("Role profiles require a loopback Ollama endpoint; processing stays on this PC")
        # Pin localhost to a loopback literal; never use a proxy or follow redirects.
        if url.hostname.lower() == "localhost":
            self.endpoint = f"{url.scheme}://127.0.0.1:{url.port or (443 if url.scheme == 'https' else 80)}"
        self.endpoint = self.endpoint.rstrip("/")
        if not self.model or len(self.model) > 160 or any(ord(c) < 32 for c in self.model):
            raise ValueError("Invalid model name")
        for name, low, high in (("max_input_chars", 100, 24000), ("max_output_tokens", 64, 1200),
                                ("max_output_bytes", 512, 6000), ("num_ctx", 2048, 16384),
                                ("timeout_seconds", 1, 600), ("poll_seconds", 0.5, 60),
                                ("discover_seconds", 1, 300), ("collapse_seconds", 0, 3600),
                                ("stale_seconds", 10, 7200), ("otel_port", 0, 65535)):
            if not low <= getattr(self, name) <= high:
                raise ValueError(f"{name} must be between {low} and {high}")

    def resolve_model(self, tool, role=None):
        role = role or self.routes[tool]
        if role not in ("general", "coding", "reasoning"):
            raise ValueError("Unknown model role")
        return role, self.roles[role] if self.roles else self.model


def load_config(path=None):
    path = path or os.getenv("LAB_CONFIG") or ('config.toml' if Path('config.toml').is_file() else None)
    values = {}
    if path:
        path = Path(path).resolve()
        with path.open("rb") as f:
            values = tomllib.load(f)
        values.update(values.pop("monitor", {}))
        for key in ("data_dir", "codex_home", "source_root"):
            if key in values and not Path(values[key]).is_absolute():
                values[key] = path.parent / values[key]
    for key in ("model", "endpoint", "data_dir"):
        if f"LAB_{key.upper()}" in os.environ:
            values[key] = os.environ[f"LAB_{key.upper()}"]
    if "LAB_MODEL" in os.environ and values.get("roles"):
        values["roles"]["general"] = os.environ["LAB_MODEL"]
    for role in ("general", "coding", "reasoning"):
        if f"LAB_MODEL_{role.upper()}" in os.environ:
            if not values.get("roles"):
                raise ValueError("Role environment overrides require a [roles] configuration")
            values["roles"][role] = os.environ[f"LAB_MODEL_{role.upper()}"]
    return Config(**values)
