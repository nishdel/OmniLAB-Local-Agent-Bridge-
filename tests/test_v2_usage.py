import asyncio
import sqlite3
import httpx
import pytest
from localagentbridge.config import Config
from localagentbridge.service import Service
from localagentbridge.telemetry import Store


def test_additive_migration_preserves_v01_rows(tmp_path):
    db = sqlite3.connect(tmp_path / "usage.sqlite3")
    db.execute("""CREATE TABLE usage (id TEXT PRIMARY KEY,source TEXT,session_id TEXT,model TEXT,tool TEXT,
        started REAL,duration REAL,input_tokens INTEGER,cached_input_tokens INTEGER,output_tokens INTEGER,
        reasoning_output_tokens INTEGER,total_tokens INTEGER,tokens_per_second REAL,input_chars INTEGER,
        output_bytes INTEGER,status TEXT)""")
    db.execute("INSERT INTO usage(id,source,session_id,model,started,total_tokens,status) VALUES('old','local','old','qwen',0,120,'ok')")
    db.commit()
    db.close()
    store = Store(tmp_path)
    Store(tmp_path)  # Migration is idempotent.
    with store.connect() as db:
        row = db.execute("SELECT * FROM usage").fetchone()
        assert row["total_tokens"] == 120 and row["outcome"] is None and row["context_compression"] is None


def test_feedback_only_no_inference_private_and_atomic(tmp_path):
    service = Service(Config(data_dir=tmp_path), httpx.MockTransport(lambda r: pytest.fail("No model call")))
    store = service.bridge.store
    store.usage(id="one", source="local", session_id="one", model="qwen", started=0)
    report = {"request_id": "one", "outcome": "accepted"}
    result = asyncio.run(service.triage(feedback=[report]))
    assert result == {"feedback_recorded": 1, "model_called": False}
    with pytest.raises(ValueError):
        store.report([report | {"outcome": "rejected"}, {"request_id": "missing", "outcome": "corrected"}])
    with store.connect() as db:
        assert db.execute("SELECT outcome FROM usage WHERE id='one'").fetchone()[0] == "accepted"


def test_compression_weighted_by_bytes_not_average_percent(tmp_path):
    store = Store(tmp_path)
    for id, before, after in (("a", 1000, 100), ("b", 100, 200)):
        store.usage(id=id, source="local", session_id=id, model="qwen", started=0, source_bytes=before, output_bytes=after)
    store.usage(id="failed", source="local", session_id="failed", model="qwen", started=0, source_bytes=9999, output_bytes=0, status="error")
    row = store.totals()[0]
    assert row["requests"] == 3
    assert row["compression_estimate"] == pytest.approx(1 - 300 / 1100)


def test_cannot_accept_a_failed_request(tmp_path):
    store = Store(tmp_path)
    store.usage(id="failed", source="local", session_id="failed", model="qwen", started=0, status="error")
    with pytest.raises(ValueError):
        store.report([{"request_id": "failed", "outcome": "accepted"}])
    store.report([{"request_id": "failed", "outcome": "rejected"}])
