from datetime import datetime, timezone
import json
import time
from localagentbridge.codex_usage import RolloutReader
from localagentbridge.config import Config
from localagentbridge.otel import ingest_logs
from localagentbridge.telemetry import Store
from localagentbridge.widget import Visibility, elapsed


def event(kind, payload, when=1000):
    return {"type": kind, "payload": payload,
            "timestamp": datetime.fromtimestamp(when, timezone.utc).isoformat()}


def usage(total, output=10, cached=20, reasoning=3):
    return {"input_tokens": total - output, "output_tokens": output, "cached_input_tokens": cached,
            "reasoning_output_tokens": reasoning, "total_tokens": total}


def token_event(total, last=None, when=1002):
    return event("event_msg", {"type": "token_count", "info": {"total_token_usage": total,
                  "last_token_usage": last or total}}, when)


def reader(tmp_path):
    store = Store(tmp_path / "data")
    return RolloutReader(Config(data_dir=tmp_path / "data", codex_home=tmp_path / "codex", otel_port=0), store), store


def otel_document(session="s1", model="gpt-test", tokens=None, stamp=1002000000000):
    fields = {"event.name": "codex.sse_event", "event.kind": "response.completed",
              "conversation.id": session, "model": model, **(tokens or usage(100)),
              "prompt": "DO_NOT_STORE_PROMPT", "tool_output": "DO_NOT_STORE_SOURCE"}
    return {"resourceLogs": [{"scopeLogs": [{"logRecords": [{"timeUnixNano": str(stamp),
        "attributes": [{"key": k, "value": {"stringValue" if isinstance(v, str) else "intValue": str(v)}} for k, v in fields.items()],
        "body": {"stringValue": "DO_NOT_STORE_BODY"}}]}]}]}


def test_rollout_deltas_duplicates_model_change_reset_and_lifecycle(tmp_path):
    r, store = reader(tmp_path)
    state = {}
    events = [event("session_meta", {"id": "s1", "base_instructions": "secret"}),
              event("event_msg", {"type": "task_started", "turn_id": "t1"}),
              event("turn_context", {"model": "gpt-a"}, 1001), token_event(usage(100)),
              token_event(usage(100)), token_event(usage(200, output=20)),
              event("event_msg", {"type": "task_complete"}, 1010),
              event("event_msg", {"type": "task_started", "turn_id": "t2"}, 1020),
              event("turn_context", {"model": "gpt-b"}, 1020),
              token_event(usage(300, output=30), when=1021),
              token_event(usage(50, output=5), when=1022),
              event("event_msg", {"type": "turn_aborted"}, 1030)]
    for i, e in enumerate(events):
        r.ingest(e, state, str(i))
    totals = {row["model"]: row for row in store.totals()}
    assert totals["gpt-a"]["total_tokens"] == 200
    assert totals["gpt-b"]["total_tokens"] == 150
    assert totals["gpt-a"]["duration"] == 10 and totals["gpt-b"]["duration"] == 10
    assert not store.active()
    assert "secret" not in json.dumps(state)


def test_fork_inherited_counters_not_recounted(tmp_path):
    r, store = reader(tmp_path)
    state = {"session": "child", "model": "gpt-a"}
    r.ingest(token_event(usage(1200), last=usage(200)), state, "e1")
    assert store.totals()[0]["total_tokens"] == 200


def test_incremental_partial_lines_restart_and_replay(tmp_path):
    r, store = reader(tmp_path)
    path = tmp_path / "rollout-test.jsonl"
    lines = [event("session_meta", {"id": "s1"}), event("turn_context", {"model": "gpt-a"}), token_event(usage(100))]
    text = "\n".join(json.dumps(x) for x in lines) + "\n"
    path.write_bytes(text[:-4].encode())
    r.read(path)
    assert store.totals() == []
    with path.open("ab") as f:
        f.write(text[-4:].encode())
    r.read(path)
    assert store.totals()[0]["total_tokens"] == 100
    fresh, _ = reader(tmp_path)
    fresh.read(path)
    assert store.totals()[0]["total_tokens"] == 100
    # Simulate a crash after inserting usage but before checkpointing.
    with store.connect() as db:
        db.execute("DELETE FROM checkpoints")
    fresh.read(path)
    assert store.totals()[0]["total_tokens"] == 100


def test_truncated_rollout_replayed_without_double_count(tmp_path):
    r, store = reader(tmp_path)
    path = tmp_path / "rollout-test.jsonl"
    lines = [event("session_meta", {"id": "s1"}), event("turn_context", {"model": "gpt-a"}), token_event(usage(100))]
    text = "\n".join(json.dumps(x) for x in lines) + "\n"
    path.write_text(text + json.dumps(event("response_item", {"secret": "x" * 1000})) + "\n")
    r.read(path)
    path.write_text(text)
    r.read(path)
    assert store.totals()[0]["total_tokens"] == 100


def test_otel_retries_no_double_count_and_metadata_allowlist(tmp_path):
    store = Store(tmp_path)
    document = otel_document()
    assert ingest_logs(document, store) == 1
    ingest_logs(document, store)
    totals = store.totals()[0]
    assert totals["total_tokens"] == 100 and totals["requests"] == 1
    assert totals["cached_input_tokens"] == 20 and totals["reasoning_output_tokens"] == 3
    with store.connect() as db:
        assert "DO_NOT_STORE" not in "\n".join(db.iterdump())


def test_otel_and_rollout_use_most_complete_stream_not_sum(tmp_path):
    r, store = reader(tmp_path)
    state = {"session": "s1", "model": "gpt-test"}
    r.ingest(token_event(usage(100)), state, "r1")
    ingest_logs(otel_document(), store)
    assert store.totals()[0]["total_tokens"] == 100
    r.ingest(token_event(usage(200, output=20)), state, "r2")
    assert store.totals()[0]["total_tokens"] == 200
    ingest_logs(otel_document(stamp=1003000000000), store)
    assert store.totals()[0]["total_tokens"] == 200
    assert store.totals()[0]["requests"] == 2


def test_unknown_counts_remain_null_and_subsets_not_added(tmp_path):
    store = Store(tmp_path)
    values = {"input_token_count": 100, "output_token_count": 20, "cached_token_count": 50, "reasoning_token_count": 5}
    ingest_logs(otel_document(tokens=values), store)
    assert store.totals()[0]["total_tokens"] == 120
    store.usage(id="local1", source="local", session_id="local1", model="qwen", started=0, status="error")
    assert next(row for row in store.totals() if row["kind"] == "Local")["total_tokens"] is None


def test_missing_native_breakdown_uses_equally_complete_rollout(tmp_path):
    r, store = reader(tmp_path)
    r.ingest(token_event(usage(100)), {"session": "s1", "model": "gpt-test"}, "r1")
    ingest_logs(otel_document(tokens={"input_tokens": 90, "output_tokens": 10, "total_tokens": 100}), store)
    row = store.totals()[0]
    assert row["total_tokens"] == 100
    assert row["cached_input_tokens"] == 20 and row["reasoning_output_tokens"] == 3


def test_stale_activity_does_not_stay_active(tmp_path):
    store = Store(tmp_path)
    now = time.time()
    store.activity("old", "local", "old", "qwen", now - 400, now - 350)
    store.activity("new", "local", "new", "qwen", now, now, "generating", output_tokens=10)
    assert [row["id"] for row in store.active(300)] == ["new"]
    store.activity("new", "local", "new", "qwen", now, now + 1, "complete")
    assert not store.active(300)


def test_widget_auto_show_collapse_and_pin():
    visibility = Visibility(10)
    assert visibility.update(False, 0) is None
    assert visibility.update(True, 1) == "show"
    assert visibility.update(True, 2) is None
    assert visibility.update(False, 11) is None
    assert visibility.update(False, 12) == "hide"
    assert visibility.update(True, 13) == "show"
    visibility.pinned = True
    assert visibility.update(False, 30) is None
    visibility.pinned = False
    assert visibility.update(False, 31) == "hide"
    assert elapsed(3672) == "01:01:12"
