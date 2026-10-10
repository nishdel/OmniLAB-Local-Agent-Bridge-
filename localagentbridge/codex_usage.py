"""Incremental Codex rollout reader: retain counters and lifecycle metadata only."""
from datetime import datetime, timezone
import hashlib
import json
import time
from .telemetry import TOKEN_FIELDS, LOG


def timestamp(value):
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.timestamp()


def counts(value):
    return {k: max(0, int(value[k])) if value.get(k) is not None else None for k in TOKEN_FIELDS}


class RolloutReader:
    def __init__(self, config, store, backfill=False):
        self.config, self.store, self.backfill = config, store, backfill
        self.paths = {}
        self.unchanged = {}
        self.last_discovery = 0

    def discover(self):
        root = self.config.codex_home
        today = datetime.now(timezone.utc).strftime("%Y/%m/%d")
        roots = [root / "sessions" / today]
        if self.backfill:
            roots = [root / "sessions", root / "archived_sessions"]
        for directory in roots:
            for path in directory.rglob("rollout-*.jsonl"):
                self.paths[path.name] = path
        # The app updates this index on older resumed sessions. A cheap periodic
        # scan of names also finds those sessions without parsing their contents.
        if not self.backfill:
            cutoff = time.time() - 86400
            for path in (root / "sessions").rglob("rollout-*.jsonl"):
                try:
                    if path.stat().st_mtime >= cutoff:
                        self.paths[path.name] = path
                except OSError:
                    continue

    def poll(self):
        if time.monotonic() - self.last_discovery >= self.config.discover_seconds:
            self.discover()
            self.last_discovery = time.monotonic()
        # Work is bounded per pass; checkpoints resume even huge rollouts.
        budget = 8 * 1024 * 1024
        for path in list(self.paths.values()):
            if budget <= 0:
                break
            try:
                budget -= self.read(path, min(budget, 1024 * 1024))
            except (OSError, ValueError, TypeError, OverflowError):
                LOG.warning("rollout_read_failed file_id=%s", hashlib.sha256(path.name.encode()).hexdigest()[:12])

    def read(self, path, budget=1024 * 1024):
        stat = path.stat()
        signature = (stat.st_size, stat.st_mtime_ns)
        if self.unchanged.get(path.name) == signature:
            return 0
        key = "rollout:" + hashlib.sha256(path.name.encode()).hexdigest()
        state = self.store.checkpoint(key)
        offset = state.get("offset", 0)
        if stat.st_size == offset:
            self.unchanged[path.name] = signature
            return 0
        if stat.st_size < offset:
            state, offset = {}, 0
        consumed = 0
        with path.open("rb") as f:
            f.seek(offset)
            while consumed < budget:
                before = f.tell()
                line = f.readline(2 * 1024 * 1024)
                if not line:
                    break
                if not line.endswith(b"\n"):
                    if len(line) < 2 * 1024 * 1024:
                        f.seek(before)  # Wait for a complete append; never lose partial JSON.
                        break
                    state["skip_line"] = True
                elif state.pop("skip_line", False):
                    consumed += len(line)
                    continue
                if not state.get("skip_line") and any(t in line for t in (b'"session_meta"', b'"turn_context"', b'"event_msg"')):
                    try:
                        self.ingest(json.loads(line), state, key + ":" + str(before))
                    except (ValueError, TypeError, KeyError, AttributeError):
                        LOG.warning("rollout_event_skipped reason=unsupported_or_invalid_metadata")
                consumed += len(line)
            state["offset"] = f.tell()
        self.store.checkpoint(key, state)
        if state["offset"] == stat.st_size:
            self.unchanged[path.name] = signature
        return consumed

    def ingest(self, event, state, event_id):
        payload = event.get("payload", {})
        kind = event.get("type")
        when = timestamp(event["timestamp"])
        if kind == "session_meta":
            state["session"] = str(payload.get("id") or payload.get("session_id") or event_id)[:160]
        elif kind == "turn_context":
            state["model"] = str(payload.get("model") or "unknown")[:160]
            self.touch(state, when)
        elif kind == "event_msg":
            subtype = payload.get("type")
            if subtype in ("task_started", "turn_started"):
                if state.get("activity"):
                    self.touch(state, state.get("updated", when), "interrupted")
                state.update(activity=str(payload.get("turn_id") or event_id)[:200], started=when, generated=0)
                self.touch(state, when)
            elif subtype in ("task_complete", "turn_complete", "turn_aborted"):
                self.touch(state, when, "aborted" if subtype == "turn_aborted" else "complete")
                state.pop("activity", None)
            elif subtype == "token_count" and isinstance(payload.get("info"), dict):
                info = payload["info"]
                total = counts(info.get("total_token_usage") or {})
                previous = state.get("total", {})
                last = counts(info.get("last_token_usage") or {})
                if total["total_tokens"] is None:
                    return
                if total["total_tokens"] == previous.get("total_tokens"):
                    self.touch(state, when)
                    return  # rate-limit-only / repeated cumulative snapshot
                reset = total["total_tokens"] < previous.get("total_tokens", 0)
                if not previous or reset:
                    # A fork/resume can inherit cumulative usage. Count only its
                    # first observed last response, not its parent's history.
                    # Without a last-response counter, inherited cumulative
                    # history is not attributable to this session.
                    delta = last
                else:
                    delta = {k: max(0, v - previous[k]) if v is not None and previous.get(k) is not None
                             else None for k, v in total.items()}
                state["total"] = total
                if delta["total_tokens"]:
                    self.store.usage(id=event_id, source="rollout", session_id=state.get("session", event_id),
                                     model=state.get("model", "unknown"), started=when,
                                     logical_id=state.get("activity"), **delta)
                    state["generated"] = state.get("generated", 0) + (delta["output_tokens"] or 0)
                self.touch(state, when)
            else:
                self.touch(state, when)

    def touch(self, state, when, status="active"):
        if state.get("activity"):
            state["updated"] = when
            session = state.get("session", "unknown")
            self.store.activity("rollout:" + session + ":" + state["activity"], "rollout", session,
                                state.get("model", "unknown"), state["started"], when, status,
                                output_tokens=state.get("generated"))
