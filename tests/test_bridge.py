import asyncio
import json
import logging
from pathlib import Path
import httpx
import pytest
from localagentbridge.bridge import Bridge, BridgeError
from localagentbridge.config import Config, load_config
from localagentbridge.files import read_selected
from localagentbridge.schemas import SCHEMAS, bounded_result, compact

SUMMARY = {"relevant_components_files": ["math.py"], "important_findings": ["Adds two numbers"],
           "uncertainties": [], "recommended_next_actions": ["Test zero"]}


def wire(value=SUMMARY, **metadata):
    return (json.dumps({"message": {"content": json.dumps(value)}, "done": False}) + "\n" +
            json.dumps({"done": True, "done_reason": "stop", "prompt_eval_count": 100,
                        "eval_count": 20, "eval_duration": 2_000_000_000, **metadata}) + "\n").encode()


def bridge(tmp_path, handler):
    return Bridge(Config(data_dir=tmp_path), httpx.MockTransport(handler))


def test_success_limits_options_and_metadata(tmp_path):
    def handler(request):
        body = json.loads(request.content)
        assert str(request.url) == "http://127.0.0.1:11434/api/chat"
        assert body["model"] == "qwen3:4b" and body["think"] is False
        assert body["stream"] and body["format"]["type"] == "object"
        assert body["options"]["num_predict"] == 600
        assert "tools" not in body
        # Ollama's format constrains decoding; the model must also see the
        # schema to understand field/enum meanings while evaluating evidence.
        assert compact(body["format"]) in body["messages"][0]["content"]
        assert "Follow the user's objective field" in body["messages"][0]["content"]
        return httpx.Response(200, content=wire())
    app = bridge(tmp_path, handler)
    result = asyncio.run(app.analyze("summarize_context", "sensitive source", "find components"))
    assert result["important_findings"] == SUMMARY["important_findings"]
    assert len(compact(result).encode()) <= 3000
    row = app.store.totals()[0]
    assert row["total_tokens"] == 120 and row["tokens_per_second"] == 10
    assert not app.store.active()
    with app.store.connect() as db:
        assert "sensitive source" not in str([tuple(r) for r in db.execute("SELECT * FROM usage")])


@pytest.mark.parametrize("status,expected", [(404, "not installed"), (500, "HTTP 500"), (302, "HTTP 302")])
def test_http_errors_are_short_and_private(tmp_path, status, expected):
    app = bridge(tmp_path, lambda r: httpx.Response(status, text="SECRET SOURCE FROM SERVER"))
    with pytest.raises(BridgeError, match=expected) as e:
        asyncio.run(app.analyze("review_diff", "diff"))
    assert "SECRET" not in str(e.value)
    assert not app.store.active()


@pytest.mark.parametrize("error,match", [(httpx.ConnectError("secret"), "unavailable"),
                                         (httpx.ReadTimeout("secret"), "timed out")])
def test_transport_failure(tmp_path, error, match):
    def handler(request):
        raise error
    app = bridge(tmp_path, handler)
    with pytest.raises(BridgeError, match=match):
        asyncio.run(app.analyze("review_diff", "diff"))
    assert not app.store.active()


@pytest.mark.parametrize("body,match", [(b'{"message":{"content":"secret"}}\n', "before final"),
                                       (wire({"unexpected": "secret"}), "structured JSON"),
                                       (wire(done_reason="length"), "token limit"),
                                       (b"x" * 262145, "transport limit")], ids=["unfinished", "invalid-schema", "token-limit", "transport-limit"])
def test_bad_or_truncated_response(tmp_path, body, match):
    app = bridge(tmp_path, lambda r: httpx.Response(200, content=body))
    with pytest.raises(BridgeError, match=match):
        asyncio.run(app.analyze("summarize_context", "input"))


def test_input_limit_checked_before_request(tmp_path):
    app = bridge(tmp_path, lambda r: pytest.fail("must not call Ollama"))
    with pytest.raises(BridgeError, match="limit"):
        asyncio.run(app.analyze("review_diff", "a" * 10001))
    with pytest.raises(BridgeError, match="non-empty"):
        asyncio.run(app.analyze("review_diff", " "))
    assert not app.store.totals()


def test_response_byte_budget_keeps_json_and_fields():
    raw = {key: ["界" * 240] * 4 for key in SUMMARY}
    result = bounded_result("summarize_context", json.dumps(raw), 512)
    assert len(compact(result).encode()) <= 512
    assert result.pop("truncated") is True
    SCHEMAS["summarize_context"].model_validate(result)


def test_no_model_contents_in_log(tmp_path, caplog):
    app = bridge(tmp_path, lambda r: httpx.Response(200, content=wire()))
    with caplog.at_level(logging.INFO, logger="localagentbridge"):
        asyncio.run(app.analyze("summarize_context", "DO_NOT_LOG_THIS"))
    assert "DO_NOT_LOG_THIS" not in caplog.text
    assert "model=qwen3:4b" in caplog.text and "output_bytes=" in caplog.text


def test_busy_and_cancellation_clear_activity(tmp_path):
    started, release = asyncio.Event(), asyncio.Event()
    async def handler(request):
        started.set()
        await release.wait()
        return httpx.Response(200, content=wire())
    app = bridge(tmp_path, handler)
    async def run():
        first = asyncio.create_task(app.analyze("summarize_context", "input"))
        await started.wait()
        with pytest.raises(BridgeError, match="busy"):
            await app.analyze("summarize_context", "second")
        first.cancel()
        with pytest.raises(asyncio.CancelledError):
            await first
    asyncio.run(run())
    assert not app.store.active()
    with app.store.connect() as db:
        assert db.execute("SELECT status FROM usage").fetchone()[0] == "cancelled"


@pytest.mark.parametrize("endpoint", ["http://192.168.1.2:11434", "https://ollama.com", "file:///etc/passwd",
                                      "http://user:pass@localhost:11434", "http://localhost:11434/api", "http://0.0.0.0:11434"])
def test_reject_unsafe_endpoint(endpoint):
    with pytest.raises(ValueError):
        Config(endpoint=endpoint)


def test_config_env_and_relative_paths(tmp_path, monkeypatch):
    config = tmp_path / "config.toml"
    config.write_text('model="file-model"\ndata_dir="records"\n[monitor]\notel_port=0', encoding="utf-8")
    monkeypatch.setenv("LAB_MODEL", "env-model")
    c = load_config(config)
    assert c.model == "env-model" and c.data_dir == tmp_path / "records" and c.otel_port == 0
    assert Config(endpoint="http://192.168.1.2:11434", allow_remote=True).allow_remote


def test_selected_files_are_bounded_and_confined(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    (root / "math.py").write_text("return a + b", encoding="utf-8")
    config = Config(source_root=root, data_dir=tmp_path / "data")
    assert "return a + b" in read_selected(config, ["math.py"])
    for path in ("../private.txt", str(tmp_path / "private.txt"), "math.py:hidden", "missing.py", "."):
        with pytest.raises(BridgeError):
            read_selected(config, [path])
    (root / "big.txt").write_text("x" * 10001, encoding="utf-8")
    with pytest.raises(BridgeError, match="budget"):
        read_selected(config, ["big.txt"])
    with pytest.raises(BridgeError, match="disabled"):
        read_selected(Config(data_dir=tmp_path), ["math.py"])


def test_symlink_rejected(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    target = tmp_path / "secret.txt"
    target.write_text("secret")
    try:
        (root / "link.txt").symlink_to(target)
    except OSError:
        pytest.skip("symlinks require Windows developer mode")
    with pytest.raises(BridgeError, match="symlinks"):
        read_selected(Config(source_root=root, data_dir=tmp_path / "db"), ["link.txt"])


def test_windows_reparse_point_rejected_without_following(tmp_path, monkeypatch):
    from types import SimpleNamespace
    import stat
    (tmp_path / "file.txt").write_text("secret")
    original = Path.lstat
    def fake_lstat(path):
        if path == tmp_path / "file.txt":
            return SimpleNamespace(st_mode=stat.S_IFREG, st_file_attributes=0x400)
        return original(path)
    config = Config(source_root=tmp_path, data_dir=tmp_path / "db")
    monkeypatch.setattr(Path, "lstat", fake_lstat)
    with pytest.raises(BridgeError, match="junctions"):
        read_selected(config, ["file.txt"])
