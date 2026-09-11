import asyncio
import json
import httpx
import pytest
from localagentbridge.bridge import Bridge, BridgeError
from localagentbridge.config import Config, load_config
from localagentbridge.routing import model_status
from localagentbridge.service import Service
from localagentbridge.schemas import compact
from test_bridge import SUMMARY, wire

ROLES = {"general": "qwen3:4b", "coding": "qwen2.5-coder:7b", "reasoning": "phi4-mini"}
OPINION = {"verdict": "support", "reasons": ["The invariant is preserved."], "checks": ["Test the boundary."], "confidence": "medium"}


def transport(chats, answer=SUMMARY, missing=()):
    def handler(request):
        if request.url.path == "/api/tags":
            return httpx.Response(200, json={"models": [{"name": v if ":" in v else v + ":latest"} for v in ROLES.values() if v not in missing]})
        body = json.loads(request.content)
        chats.append(body)
        return httpx.Response(200, content=wire(answer))
    return httpx.MockTransport(handler)


def test_role_routing_and_legacy_config(tmp_path):
    cfg = Config(data_dir=tmp_path, roles=ROLES)
    assert cfg.resolve_model("summarize_context") == ("general", "qwen3:4b")
    assert cfg.resolve_model("analyze_test_output") == ("coding", "qwen2.5-coder:7b")
    assert cfg.resolve_model("triage_task") == ("reasoning", "phi4-mini")
    legacy = Config(model="custom:3b", data_dir=tmp_path)
    assert legacy.resolve_model("review_diff")[1] == "custom:3b"
    assert legacy.resolve_model("triage_task")[1] == "custom:3b"


def test_explicit_overrides_no_silent_substitution(tmp_path, monkeypatch):
    path = tmp_path / "config.toml"
    path.write_text('[roles]\ngeneral="qwen3:4b"\ncoding="qwen2.5-coder:7b"\nreasoning="phi4-mini"\n[routes]\nreview_diff="reasoning"')
    monkeypatch.setenv("LAB_MODEL_CODING", "custom:7b")
    cfg = load_config(path)
    assert cfg.resolve_model("review_diff")[1] == "phi4-mini"
    assert cfg.resolve_model("analyze_code")[1] == "custom:7b"


@pytest.mark.parametrize("kwargs", [{"roles": {"general": "qwen3:4b"}}, {"routes": {"review_diff": "unknown"}},
                                   {"roles": ROLES | {"coding": "some:cloud"}}, {"model": "qwen;whoami"},
                                   {"consensus_roles": ["coding", "coding"]}])
def test_invalid_routing_fails_early(kwargs):
    with pytest.raises(ValueError):
        Config(**kwargs)


def test_role_profile_cannot_send_processing_off_machine():
    with pytest.raises(ValueError, match="loopback"):
        Config(roles=ROLES, endpoint="http://192.168.1.3:11434", allow_remote=True)


def test_missing_models_exact_commands_and_no_inference(tmp_path):
    cfg = Config(data_dir=tmp_path, roles=ROLES)
    chats = []
    fake = transport(chats, missing=("qwen2.5-coder:7b", "phi4-mini"))
    rows = asyncio.run(model_status(cfg, fake))
    assert rows[1]["install_command"] == "ollama pull qwen2.5-coder:7b"
    assert rows[2]["install_command"] == "ollama pull phi4-mini"
    app = Bridge(cfg, fake)
    with pytest.raises(BridgeError, match="ollama pull qwen2.5-coder:7b"):
        asyncio.run(app.analyze("review_diff", "diff"))
    assert not chats
    assert app.store.totals()[0]["model"] == "qwen2.5-coder:7b"


def test_metadata_limits_and_real_accounting(tmp_path):
    cfg = Config(data_dir=tmp_path, roles=ROLES)
    chats = []
    app = Bridge(cfg, transport(chats))
    result = asyncio.run(app.analyze("summarize_context", "example " * 400, with_metadata=True))
    assert result["_meta"]["model"] == "qwen3:4b" and chats[0]["keep_alive"] == 0
    with app.store.connect() as db:
        row = db.execute("SELECT * FROM usage").fetchone()
        assert row["id"] == result["_meta"]["request_id"]
        assert row["output_bytes"] == len(compact(result).encode()) <= cfg.max_output_bytes
        assert row["context_compression"] == 1 - row["output_bytes"] / row["source_bytes"]
        assert row["input_tokens"] == 100 and row["output_tokens"] == 20


def test_consensus_is_sequential_independent_and_bounded(tmp_path):
    chats = []
    cfg = Config(data_dir=tmp_path, roles=ROLES)
    service = Service(cfg, transport(chats, OPINION))
    result = asyncio.run(service.second_opinion("Keep invariant?", "Evidence " * 300, consensus=True))
    assert [r["model"] for r in chats] == [ROLES["coding"], ROLES["reasoning"]]
    assert chats[0]["messages"] == chats[1]["messages"]  # No previous model's answer fed forward.
    assert result["agreement"] == "unanimous" and result["codex_decides"]
    assert result["verdict_counts"]["support"] == 2
    assert len(compact(result).encode()) <= cfg.max_output_bytes
    with service.bridge.store.connect() as db:
        groups = [r[0] for r in db.execute("SELECT group_id FROM usage")]
        assert len(groups) == 2 and groups[0] == groups[1] and groups[0]


def test_consensus_missing_member_fails_before_any_chat(tmp_path):
    chats = []
    service = Service(Config(data_dir=tmp_path, roles=ROLES), transport(chats, OPINION, missing=("phi4-mini",)))
    with pytest.raises(BridgeError, match="ollama pull phi4-mini"):
        asyncio.run(service.second_opinion("Question?", consensus=True))
    assert not chats


def test_local_first_small_work_skips_triage_but_keeps_local_analysis(tmp_path):
    service = Service(Config(data_dir=tmp_path, roles=ROLES), httpx.MockTransport(lambda r: pytest.fail("No inference expected")))
    result = asyncio.run(service.triage("Small task", 100, 1))
    assert result["delegation"] == "delegate_analysis" and result["model_called"] is False
    assert asyncio.run(service.triage("Huge task", 10000, 40))["delegation"] == "find_relevant_context_first"
    assert asyncio.run(service.triage("Important decision", 3000, 4, "high"))["delegation"] == "codex"


@pytest.mark.parametrize("hints,expected", [
    ({"complexity": "complex"}, "codex"),
    ({"ambiguous": True}, "codex"),
    ({"risk": "high"}, "codex"),
    ({"confidence": "low"}, "codex"),
    ({"capability": "architecture"}, "codex"),
    ({"capability": "orchestration"}, "codex"),
    ({"capability": "disagreement"}, "codex"),
    ({"capability": "execution"}, "codex"),
    ({"failed_local_attempts": 2}, "codex"),
    ({"failed_local_attempts": 1, "capability": "implementation"}, "delegate_analysis"),
    ({"context_chars": 10001}, "find_relevant_context_first"),
    ({"file_count": 9}, "find_relevant_context_first"),
    ({"file_count": 9, "complexity": "complex"}, "codex"),
])
def test_escalation_gates_never_call_an_llm(tmp_path, hints, expected):
    service = Service(Config(data_dir=tmp_path, roles=ROLES), httpx.MockTransport(lambda r: pytest.fail("No inference expected")))
    result = asyncio.run(service.triage("Bounded task", **({"context_chars": 100, "file_count": 1} | hints)))
    assert result["delegation"] == expected and result["model_called"] is False
    with service.bridge.store.connect() as db:
        assert db.execute("SELECT COUNT(*) FROM usage").fetchone()[0] == 0
        row = dict(db.execute("SELECT * FROM decisions").fetchone())
        assert row["delegation"] == expected and row["request_id"] is None
        assert "Bounded task" not in str(row)


def test_optional_legacy_minimum_and_configurable_failure_limit(tmp_path):
    service = Service(Config(data_dir=tmp_path, roles=ROLES, delegation={"local_first": False, "max_failed_local_attempts": 1}))
    assert service.delegation(100, 1, "low")[0] == "codex_direct"
    assert service.delegation(3000, 4, "low", failed_local_attempts=1)[0] == "codex"


@pytest.mark.parametrize("policy", [{"local_first": "yes"}, {"max_failed_local_attempts": 0}, {"max_failed_local_attempts": 4}])
def test_invalid_local_first_policy(policy):
    with pytest.raises(ValueError):
        Config(delegation=policy)


def test_small_useful_answers_do_not_escalate_solely_for_expansion(tmp_path):
    answer = {"behavior": "Adds inputs", "findings": [], "uncertainties": [], "recommended_tests": ["Test zero"], "confidence": "high"}
    app = Bridge(Config(data_dir=tmp_path, roles=ROLES), transport([], answer))
    result = asyncio.run(app.analyze("analyze_code", "def add(a,b): return a+b", with_metadata=True))
    assert result["_meta"]["compression_estimate"] < 0
    assert result["_meta"]["codex_review_recommended"] is False


def test_opinions_always_require_codex_review_even_if_confident(tmp_path):
    app = Bridge(Config(data_dir=tmp_path, roles=ROLES), transport([], OPINION | {"confidence": "high"}))
    result = asyncio.run(app.analyze("second_opinion", "Evidence " * 400, with_metadata=True))
    assert result["_meta"]["codex_review_recommended"] is True


def test_large_expansion_and_low_confidence_still_recommend_review(tmp_path):
    cfg = Config(data_dir=tmp_path, roles=ROLES, delegation={"min_compression": 1})
    answer = {"behavior": "Adds inputs", "findings": [], "uncertainties": [], "recommended_tests": [], "confidence": "high"}
    result = asyncio.run(Bridge(cfg, transport([], answer)).analyze("analyze_code", "Evidence " * 300, with_metadata=True))
    assert result["_meta"]["codex_review_recommended"] is True
    result = asyncio.run(Bridge(cfg, transport([], answer | {"confidence": "low"})).analyze("analyze_code", "Evidence", with_metadata=True))
    assert result["_meta"]["codex_review_recommended"] is True


@pytest.mark.parametrize("tool,answer", [
    ("summarize_context", SUMMARY | {"uncertainties": ["Missing evidence"]}),
    ("second_opinion", OPINION | {"verdict": "uncertain", "confidence": "high"}),
])
def test_model_uncertainty_requires_review_even_with_small_input(tmp_path, tool, answer):
    app = Bridge(Config(data_dir=tmp_path, roles=ROLES), transport([], answer))
    result = asyncio.run(app.analyze(tool, "Small input", with_metadata=True))
    assert result["_meta"]["codex_review_recommended"] is True


def test_low_confidence_and_high_model_risk_override_delegation(tmp_path):
    answer = {"task_type": "coding", "risk": "high", "local_steps": [], "codex_decisions": ["Review migration"], "confidence": "high"}
    chats = []
    service = Service(Config(data_dir=tmp_path, roles=ROLES), transport(chats, answer))
    result = asyncio.run(service.triage("Review migration", 3000, 4))
    assert result["delegation"] == "codex" and chats[0]["model"] == "phi4-mini"
    assert service.delegation(3000, 4, "low", "low")[0] == "codex"
