import asyncio
import json
import httpx
import pytest
from localagentbridge.bridge import BridgeError
from localagentbridge.config import Config, SearchConfig
from localagentbridge.context import scan_repository
from localagentbridge.schemas import compact
from localagentbridge.service import Service


def repo(tmp_path, **search):
    root = tmp_path / "repo"
    root.mkdir()
    (root / "billing.py").write_text("def refund_invoice(invoice):\n    return invoice.total\n", encoding="utf-8")
    (root / "unrelated.py").write_text("def paint():\n    return 'blue'\n", encoding="utf-8")
    return Config(source_root=root, data_dir=tmp_path / "data", search=SearchConfig(**search))


def test_search_finds_real_symbol_and_exact_evidence(tmp_path):
    cfg = repo(tmp_path)
    candidates, coverage = scan_repository(cfg, "refund invoice")
    assert candidates[0]["path"] == "billing.py"
    assert candidates[0]["symbols"] == [{"name": "refund_invoice", "line": 1}]
    lines = (cfg.source_root / "billing.py").read_text().splitlines()
    for evidence in candidates[0]["evidence"]:
        assert evidence["text"] in lines[evidence["line"] - 1]
    assert coverage["files_scanned"] == 2 and not coverage["limit_reached"]


def test_ignore_rules_secrets_binary_generated_and_nested_negation(tmp_path):
    cfg = repo(tmp_path)
    root = cfg.source_root
    (root / ".gitignore").write_text("ignored.py\n*.tmp.py\n")
    for name in ("ignored.py", ".env", "credentials.json", "secret.py", "binary.py"):
        (root / name).write_bytes(b"refund invoice" + (b"\0" if name == "binary.py" else b""))
    (root / "node_modules").mkdir()
    (root / "node_modules" / "stolen.py").write_text("refund invoice")
    child = root / "src"
    child.mkdir()
    (child / ".gitignore").write_text("!keep.tmp.py\ndrop.py\n")
    (child / "keep.tmp.py").write_text("refund invoice")
    (child / "drop.py").write_text("refund invoice")
    found, _ = scan_repository(cfg, "refund invoice")
    assert {c["path"] for c in found} == {"billing.py", "src/keep.tmp.py"}


def test_scope_narrows_scan_and_rejects_escape(tmp_path):
    cfg = repo(tmp_path)
    (cfg.source_root / "src").mkdir()
    (cfg.source_root / "src" / "refund.py").write_text("refund invoice")
    found, _ = scan_repository(cfg, "refund", "src")
    assert {c["path"] for c in found} == {"src/refund.py"}
    for scope in ("../outside", "C:/outside", "/outside", "\\\\host\\share"):
        with pytest.raises(BridgeError):
            scan_repository(cfg, "refund", scope)


def test_scan_budgets_are_reported(tmp_path):
    cfg = repo(tmp_path, max_files=1)
    _, coverage = scan_repository(cfg, "refund invoice")
    assert coverage["files_scanned"] == 1 and coverage["limit_reached"]
    cfg.search = SearchConfig(max_file_bytes=100)
    (cfg.source_root / "large.py").write_text("refund invoice\n" * 100)
    found, coverage = scan_repository(cfg, "refund invoice")
    assert "large.py" not in {c["path"] for c in found}
    assert coverage["files_skipped"] >= 1


def test_scan_entry_budget_and_empty_terms(tmp_path):
    cfg = repo(tmp_path, max_entries=1)
    _, coverage = scan_repository(cfg, "refund")
    assert coverage["entries_seen"] <= 1 and coverage["limit_reached"]
    for query in ("", "find the relevant files", "x" * 2001):
        with pytest.raises(BridgeError):
            scan_repository(cfg, query)


def test_lexical_mode_makes_no_model_call_and_is_bounded(tmp_path):
    cfg = repo(tmp_path)
    service = Service(cfg, httpx.MockTransport(lambda r: pytest.fail("No model should be called")))
    result = asyncio.run(service.find_context("refund invoice", use_model=False))
    assert result["files"][0]["path"] == "billing.py"
    assert result["_meta"]["model_called"] is False
    assert len(compact(result).encode()) <= cfg.max_output_bytes
    assert service.bridge.store.totals()[0]["total_tokens"] == 0


def test_model_ranking_cannot_invent_files_or_line_numbers(tmp_path):
    cfg = repo(tmp_path)
    def handler(request):
        payload = json.loads(request.content)
        supplied = json.loads(payload["messages"][1]["content"])
        choices = json.loads(supplied["content"])
        assert choices[0]["path"] == "billing.py"
        assert "unrelated.py" not in supplied["content"]
        assert len(supplied["content"]) < cfg.max_input_chars
        answer = {"candidate_ids": [0, 19, 0], "uncertainties": []}
        return httpx.Response(200, content=(json.dumps({"message": {"content": json.dumps(answer)}, "done": True,
                           "prompt_eval_count": 50, "eval_count": 10}) + "\n").encode())
    service = Service(cfg, httpx.MockTransport(handler))
    result = asyncio.run(service.find_context("refund invoice"))
    assert [f["path"] for f in result["files"]] == ["billing.py"]
    assert any("unsupported" in u for u in result["uncertainties"])
    with service.bridge.store.connect() as db:
        row = db.execute("SELECT output_bytes,source_bytes FROM usage").fetchone()
        assert row["output_bytes"] == len(compact(result).encode())
        assert row["source_bytes"] < result["coverage"]["bytes_scanned"] + 500
        assert "refund_invoice" not in "\n".join(db.iterdump())


def test_no_matches_does_not_call_model(tmp_path):
    cfg = repo(tmp_path)
    service = Service(cfg, httpx.MockTransport(lambda r: pytest.fail("No candidates; no model call")))
    result = asyncio.run(service.find_context("nonexistent_identifier"))
    assert result["files"] == [] and result["_meta"]["model_called"] is False


def test_reparse_directory_never_traversed(tmp_path, monkeypatch):
    cfg = repo(tmp_path)
    import os
    original = os.scandir
    class Entry:
        name = "junction"
        def stat(self, **kwargs):
            from types import SimpleNamespace
            return SimpleNamespace(st_file_attributes=0x400)
        def is_symlink(self):
            return False
    class Entries:
        def __enter__(self):
            return iter([Entry()])
        def __exit__(self, *args):
            pass
    def scandir(path):
        if path == cfg.source_root:
            return Entries()
        pytest.fail("Should not traverse a reparse directory")
    monkeypatch.setattr(os, "scandir", scandir)
    found, coverage = scan_repository(cfg, "refund")
    assert found == [] and coverage["files_skipped"] == 1
def test_implementation_path_and_symbol_beat_example_query_text(tmp_path):
    from localagentbridge.config import Config
    from localagentbridge.context import scan_repository
    (tmp_path / "routing.py").write_text('def resolve_model(tool):\n    return "local"\n')
    (tmp_path / "example.py").write_text('# Find model routing and request timeout handling\n# model requests\n# timeout handling\n')
    (tmp_path / "owner.py").write_text('class Store:\n    def report(self, outcomes):\n        return outcomes\n')
    (tmp_path / "imports.py").write_text('# Store report accepted corrected rejected\n# report\n# accepted\n')
    cfg = Config(source_root=tmp_path, data_dir=tmp_path / "data")
    candidates, _ = scan_repository(cfg, "model routing request timeout handling")
    assert candidates[0]["path"] == "routing.py"
    candidates, _ = scan_repository(cfg, "Store report accepted corrected rejected")
    assert candidates[0]["path"] == "owner.py"
