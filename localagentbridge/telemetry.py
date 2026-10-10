"""Metadata-only usage collection. Independent of MCP and the tray UI."""
from contextlib import contextmanager
import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import sqlite3
import time
import uuid

LOG = logging.getLogger("localagentbridge")
TOKEN_FIELDS = ("input_tokens", "cached_input_tokens", "output_tokens", "reasoning_output_tokens", "cache_write_input_tokens", "total_tokens")


def configure_logging(config):
    config.data_dir.mkdir(parents=True, exist_ok=True)
    LOG.setLevel(logging.INFO)
    if not LOG.handlers:
        handler = RotatingFileHandler(config.data_dir / "bridge.log", maxBytes=1_000_000, backupCount=2, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        LOG.addHandler(handler)
        stream = logging.StreamHandler()  # stderr; stdout belongs to MCP.
        stream.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
        LOG.addHandler(stream)
    LOG.propagate = False


class Store:
    def __init__(self, directory):
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        self.path = directory / "usage.sqlite3"
        with self.connect() as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.executescript("""
                CREATE TABLE IF NOT EXISTS usage (
                  id TEXT PRIMARY KEY, source TEXT NOT NULL, session_id TEXT NOT NULL,
                  model TEXT NOT NULL, tool TEXT, started REAL NOT NULL, duration REAL,
                  input_tokens INTEGER, cached_input_tokens INTEGER, output_tokens INTEGER,
                  reasoning_output_tokens INTEGER, total_tokens INTEGER, tokens_per_second REAL,
                  input_chars INTEGER, output_bytes INTEGER, status TEXT NOT NULL);
                CREATE INDEX IF NOT EXISTS usage_group ON usage(session_id,model,source);
                CREATE TABLE IF NOT EXISTS usage_bindings (
                  kind TEXT NOT NULL, session_id TEXT NOT NULL, logical_id TEXT NOT NULL,
                  run_id TEXT NOT NULL, task_id TEXT, category TEXT NOT NULL,
                  evidence TEXT NOT NULL, created REAL NOT NULL,
                  PRIMARY KEY(kind,session_id,logical_id));
                CREATE TABLE IF NOT EXISTS activity (
                  id TEXT PRIMARY KEY, source TEXT NOT NULL, session_id TEXT NOT NULL,
                  model TEXT NOT NULL, started REAL NOT NULL, updated REAL NOT NULL,
                  status TEXT NOT NULL, output_tokens INTEGER, chunks INTEGER NOT NULL DEFAULT 0);
                CREATE TABLE IF NOT EXISTS checkpoints (id TEXT PRIMARY KEY, state TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS decisions (
                  id TEXT PRIMARY KEY, created REAL NOT NULL, delegation TEXT NOT NULL,
                  request_id TEXT, context_chars INTEGER, file_count INTEGER, risk TEXT,
                  confidence TEXT, complexity TEXT, ambiguous INTEGER, capability TEXT,
                  failed_local_attempts INTEGER);
                CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS route_events (
                  id TEXT PRIMARY KEY, created REAL NOT NULL, logical_id TEXT,
                  previous_model TEXT, selected_model TEXT, reason TEXT, cap TEXT);
                CREATE TABLE IF NOT EXISTS benchmark_reviews (
                  request_id TEXT PRIMARY KEY, run_id TEXT, case_id TEXT, tool TEXT,
                  model TEXT, outcome TEXT, factual_errors INTEGER, missed_requirements INTEGER,
                  unsupported_claims INTEGER, incorrect_identification INTEGER);
                CREATE TABLE IF NOT EXISTS route_results (
                  logical_id TEXT PRIMARY KEY, finished REAL, source_bytes INTEGER,
                  returned_bytes INTEGER, handoff INTEGER, reason TEXT);
            """)
            # Additive v0.2 migration: v0.1 readers/writers remain compatible.
            db.execute("BEGIN IMMEDIATE")
            columns = {row[1] for row in db.execute("PRAGMA table_info(usage)")}
            for name, kind in {"cache_write_input_tokens": "INTEGER", "role": "TEXT", "source_bytes": "INTEGER", "context_compression": "REAL",
                               "outcome": "TEXT", "outcome_at": "REAL", "group_id": "TEXT",
                               "generation_seconds": "REAL", "load_seconds": "REAL",
                               "logical_id": "TEXT", "escalated_from": "TEXT", "escalation_reason": "TEXT",
                               "route_cap": "TEXT", "selection_reason": "TEXT"}.items():
                if name not in columns:
                    db.execute(f"ALTER TABLE usage ADD COLUMN {name} {kind}")
            columns = {row[1] for row in db.execute('PRAGMA table_info(activity)')}
            for name in ('role', 'escalated_from', 'escalation_reason', 'tool', 'route_cap', 'selection_reason'):
                if name not in columns:
                    db.execute(f'ALTER TABLE activity ADD COLUMN {name} TEXT')
            columns = {row[1] for row in db.execute('PRAGMA table_info(route_events)')}
            for name in ('tool', 'role', 'selection_reason'):
                if name not in columns:
                    db.execute(f'ALTER TABLE route_events ADD COLUMN {name} TEXT')
            db.execute('CREATE INDEX IF NOT EXISTS usage_model ON usage(source,model)')
            db.execute('CREATE INDEX IF NOT EXISTS usage_logical ON usage(logical_id,model,started)')
            db.execute('CREATE INDEX IF NOT EXISTS review_model ON benchmark_reviews(model,tool)')
            db.execute('CREATE INDEX IF NOT EXISTS route_created ON route_events(created)')
            db.execute('CREATE INDEX IF NOT EXISTS usage_failure ON usage(source,status,started)')

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=5)
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA synchronous=FULL')
        try:
            with db:
                yield db
        finally:
            db.close()

    def usage(self, *, id, source, session_id, model, started, status="ok", **metadata):
        allowed = {"tool", "duration", *TOKEN_FIELDS, "tokens_per_second", "input_chars", "output_bytes",
                   "role", "source_bytes", "context_compression", "group_id", "generation_seconds", "load_seconds",
                   "logical_id", "escalated_from", "escalation_reason", "route_cap", "selection_reason"}
        row = dict(id=id, source=source, session_id=session_id, model=model[:160], started=started, status=status)
        row.update({k: v for k, v in metadata.items() if k in allowed})
        with self.connect() as db:
            db.execute(f"INSERT OR IGNORE INTO usage ({','.join(row)}) VALUES ({','.join('?' for _ in row)})", tuple(row.values()))

    def report(self, reports):
        """Explicit Codex feedback only; update atomically without retaining notes."""
        with self.connect() as db:
            for report in reports:
                if report["outcome"] not in ("accepted", "corrected", "rejected"):
                    raise ValueError("Invalid outcome")
                row = db.execute("SELECT status FROM usage WHERE id=? AND source='local'", (report["request_id"],)).fetchone()
                if not row:
                    raise ValueError("Unknown local request_id; no outcomes changed")
                if row[0] != "ok" and report["outcome"] != "rejected":
                    raise ValueError("Only successful local results can be accepted or corrected")
            for report in reports:
                db.execute("UPDATE usage SET outcome=?,outcome_at=? WHERE id=? AND source='local'",
                           (report["outcome"], time.time(), report["request_id"]))
                LOG.info("result_feedback request=%s outcome=%s", report["request_id"], report["outcome"])
        return len(reports)

    def decision(self, delegation, *, request_id=None, **hints):
        """Policy recommendations, not model calls or proof of cloud escalation."""
        allowed = ("context_chars", "file_count", "risk", "confidence", "complexity", "ambiguous", "capability", "failed_local_attempts")
        row = dict(id=str(uuid.uuid4()), created=time.time(), delegation=delegation, request_id=request_id)
        row.update({key: hints.get(key) for key in allowed})
        with self.connect() as db:
            db.execute(f"INSERT INTO decisions ({','.join(row)}) VALUES ({','.join('?' for _ in row)})", tuple(row.values()))
        LOG.info("delegation=%s request=%s complexity=%s failed_attempts=%s", delegation, request_id, hints.get("complexity"), hints.get("failed_local_attempts"))

    def activity(self, id, source, session_id, model, started, updated=None, status="active", output_tokens=None, chunks=0,
                 role=None, escalated_from=None, escalation_reason=None, tool=None, route_cap=None, selection_reason=None):
        with self.connect() as db:
            db.execute("""INSERT INTO activity (id,source,session_id,model,started,updated,status,output_tokens,chunks,role,escalated_from,escalation_reason)
              VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
              ON CONFLICT(id) DO UPDATE SET model=excluded.model, updated=excluded.updated,
              status=excluded.status, output_tokens=excluded.output_tokens, chunks=excluded.chunks,
              role=excluded.role,escalated_from=excluded.escalated_from,escalation_reason=excluded.escalation_reason""",
                       (id, source, session_id, model[:160], started, updated or started, status, output_tokens, chunks,role,escalated_from,escalation_reason))
            db.execute('UPDATE activity SET tool=?,route_cap=?,selection_reason=? WHERE id=?',
                       (tool, route_cap, selection_reason, id))

    def compute_cap(self, default='Medium', value=None):
        from .models import TIERS
        with self.connect() as db:
            if value is not None:
                if value not in TIERS:
                    raise ValueError('Unknown compute cap')
                db.execute("INSERT OR REPLACE INTO settings VALUES ('compute_cap',?)", (value,))
                LOG.info('compute_cap=%s',value)
                return value
            row = db.execute("SELECT value FROM settings WHERE key='compute_cap'").fetchone()
            return row[0] if row and row[0] in TIERS else default

    def route_event(self, logical_id, previous_model, selected_model, reason, cap, *, tool=None, role=None, selection_reason=None):
        with self.connect() as db:
            db.execute('INSERT INTO route_events (id,created,logical_id,previous_model,selected_model,reason,cap,tool,role,selection_reason) VALUES (?,?,?,?,?,?,?,?,?,?)',
                       (str(uuid.uuid4()),time.time(),logical_id,previous_model,selected_model,reason,cap,tool,role,selection_reason))
        LOG.info('routing logical=%s from=%s to=%s reason=%s cap=%s',logical_id,previous_model,selected_model,reason,cap)

    def recent_routes(self, limit=15):
        with self.connect() as db:
            return [dict(r) for r in db.execute('''SELECT r.created,r.previous_model,r.selected_model,r.reason,r.cap,
              r.tool,r.role,r.selection_reason,
              (SELECT COALESCE(u.outcome,u.status) FROM usage u WHERE u.logical_id=r.logical_id AND u.model=r.selected_model
               ORDER BY u.started DESC LIMIT 1) outcome FROM route_events r ORDER BY r.created DESC LIMIT ?''', (min(20, max(1, limit)),))]

    def latest_local_failure(self):
        with self.connect() as db:
            row = db.execute("SELECT id FROM usage WHERE source='local' AND status='error' ORDER BY started DESC LIMIT 1").fetchone()
            return row[0] if row else None

    def compression(self, model=None):
        """Final logical envelopes where recorded; otherwise legacy final tool payloads.

        Attribute an escalated logical task once to its last local model. Failed
        handoffs remain included: their envelopes also consume Codex context.
        Consensus/v0.2 calls without final-envelope records are labelled separately.
        """
        with self.connect() as db:
            row = db.execute('''SELECT SUM(source_bytes) original,SUM(returned_bytes) returned,COUNT(*) calls
              FROM route_results r WHERE (? IS NULL OR ?=(SELECT model FROM usage u
              WHERE u.logical_id=r.logical_id ORDER BY started DESC LIMIT 1))''', (model, model)).fetchone()
            legacy = db.execute('''SELECT SUM(source_bytes) original,SUM(output_bytes) returned,COUNT(*) calls
              FROM usage u WHERE source='local' AND status='ok' AND source_bytes>0 AND output_bytes>0
              AND (? IS NULL OR model=?) AND NOT EXISTS
              (SELECT 1 FROM route_results r WHERE r.logical_id=u.logical_id)''', (model, model)).fetchone()
        def result(r):
            a, b = r['original'], r['returned']
            return dict(input_bytes=a, returned_bytes=b, calls=r['calls'],
                        reduction=1-b/a if a else None, potential_bytes=max(0, a-b) if a else None)
        return {'final_tasks': result(row), 'individual_outputs': result(legacy)}

    def model_metrics(self, model, tool=None):
        with self.connect() as db:
            row = dict(db.execute("""SELECT COUNT(*) calls,AVG(duration) average_latency,
              SUM(CASE WHEN generation_seconds>0 THEN output_tokens ELSE NULL END)/NULLIF(SUM(generation_seconds),0) tokens_per_second,
              SUM(CASE WHEN outcome='accepted' THEN 1 ELSE 0 END) accepted,
              SUM(CASE WHEN outcome='corrected' THEN 1 ELSE 0 END) corrected,
              SUM(CASE WHEN outcome='rejected' THEN 1 ELSE 0 END) rejected
              FROM usage WHERE source='local' AND model=?""",(model,)).fetchone())
            grades = db.execute('SELECT outcome FROM benchmark_reviews WHERE model=? AND (? IS NULL OR tool=?)', (model,tool,tool)).fetchall()
            row['reviewed_cases'] = len(grades)
            row['accepted_rate'] = sum(r[0]=='accepted' for r in grades)/len(grades) if grades else None
            row['rejected_rate'] = sum(r[0]=='rejected' for r in grades)/len(grades) if grades else None
            measurement = self.checkpoint('model-measurement:'+model)
            return row | measurement

    def registry_metrics(self):
        """One connection and grouped reads for a dashboard refresh, not N models × N tools."""
        with self.connect() as db:
            usage={r['model']:dict(r) for r in db.execute('''SELECT model,COUNT(*) calls,AVG(duration) average_latency,
              SUM(CASE WHEN generation_seconds>0 THEN output_tokens ELSE NULL END)/NULLIF(SUM(generation_seconds),0) tokens_per_second,
              SUM(CASE WHEN outcome='accepted' THEN 1 ELSE 0 END) accepted,
              SUM(CASE WHEN outcome='corrected' THEN 1 ELSE 0 END) corrected,
              SUM(CASE WHEN outcome='rejected' THEN 1 ELSE 0 END) rejected
              FROM usage WHERE source='local' GROUP BY model''')}
            grades=[dict(r) for r in db.execute('''SELECT model,tool,COUNT(*) reviewed_cases,
              SUM(outcome='accepted') accepted,SUM(outcome='rejected') rejected
              FROM benchmark_reviews GROUP BY model,tool''')]
            measured={r['id'][len('model-measurement:'):]:json.loads(r['state']) for r in db.execute(
                "SELECT id,state FROM checkpoints WHERE id LIKE 'model-measurement:%'")}
        result={}
        for name in set(usage) | set(measured) | {g['model'] for g in grades}:
            base=usage.get(name,dict(calls=0,average_latency=None,tokens_per_second=None,accepted=None,corrected=None,rejected=None)) | measured.get(name,{})
            subset=[g for g in grades if g['model']==name]
            for tool in [None,*{g['tool'] for g in subset}]:
                selected=[g for g in subset if tool is None or g['tool']==tool]
                count=sum(g['reviewed_cases'] for g in selected)
                result[name,tool]=base | dict(reviewed_cases=count,
                    accepted_rate=sum(g['accepted'] for g in selected)/count if count else None,
                    rejected_rate=sum(g['rejected'] for g in selected)/count if count else None)
        return result

    def route_result(self, logical_id, source_bytes, returned_bytes, handoff, reason):
        # One final envelope per logical task, separate from intermediate model outputs.
        with self.connect() as db:
            db.execute('INSERT OR REPLACE INTO route_results VALUES (?,?,?,?,?,?)',
                       (logical_id,time.time(),source_bytes,returned_bytes,int(handoff),reason))

    def checkpoint(self, id, state=None):
        with self.connect() as db:
            if state is not None:
                db.execute("INSERT OR REPLACE INTO checkpoints VALUES (?,?)", (id, json.dumps(state)))
            else:
                row = db.execute("SELECT state FROM checkpoints WHERE id=?", (id,)).fetchone()
                return json.loads(row[0]) if row else {}

    def active(self, stale_seconds=300):
        with self.connect() as db:
            return [dict(r) for r in db.execute("""SELECT * FROM activity a
              WHERE status IN ('active','loading','generating') AND updated>?
              AND (source != 'otel' OR NOT EXISTS
                (SELECT 1 FROM activity b WHERE b.session_id=a.session_id AND b.source='rollout'))
              ORDER BY started""", (time.time() - stale_seconds,))]

    def totals(self):
        # Independent copies of Codex usage are NEVER added together. Choose the
        # stream with most observed tokens per session/model; prefer OTel on ties.
        with self.connect() as db:
            rows = db.execute("""WITH streams AS (
              SELECT source,session_id,model,SUM(input_tokens) input_tokens,
                SUM(cached_input_tokens) cached_input_tokens,SUM(output_tokens) output_tokens,
                SUM(reasoning_output_tokens) reasoning_output_tokens,SUM(total_tokens) total_tokens,
                COUNT(*) requests,SUM(duration) duration,AVG(tokens_per_second) tokens_per_second
              FROM usage GROUP BY source,session_id,model), ranked AS (
              SELECT *,ROW_NUMBER() OVER (PARTITION BY session_id,model
                ORDER BY COALESCE(total_tokens,0) DESC,(source='otel') DESC) choice FROM streams)
              , enriched AS (
                SELECT r.*,COALESCE(r.cached_input_tokens,(SELECT s.cached_input_tokens FROM streams s
                  WHERE s.session_id=r.session_id AND s.model=r.model AND s.total_tokens=r.total_tokens
                  AND s.cached_input_tokens IS NOT NULL LIMIT 1)) effective_cached,
                  COALESCE(r.reasoning_output_tokens,(SELECT s.reasoning_output_tokens FROM streams s
                  WHERE s.session_id=r.session_id AND s.model=r.model AND s.total_tokens=r.total_tokens
                  AND s.reasoning_output_tokens IS NOT NULL LIMIT 1)) effective_reasoning
                FROM ranked r WHERE choice=1)
              SELECT CASE WHEN source='local' THEN 'Local' ELSE 'Codex' END kind,model,
                SUM(input_tokens) input_tokens,SUM(effective_cached) cached_input_tokens,
                SUM(output_tokens) output_tokens,SUM(effective_reasoning) reasoning_output_tokens,
                SUM(total_tokens) total_tokens,SUM(requests) requests,
                SUM(CASE WHEN source='local' THEN duration ELSE NULL END) duration,
                AVG(tokens_per_second) tokens_per_second
              FROM enriched GROUP BY kind,model ORDER BY kind,model""").fetchall()
            result = {(r["kind"], r["model"]): dict(r) for r in rows}
            durations = db.execute("""SELECT model,SUM(MAX(0,updated-started)) seconds FROM activity a
              WHERE source='rollout' OR (source='otel' AND NOT EXISTS
                (SELECT 1 FROM activity b WHERE b.source='rollout' AND b.session_id=a.session_id))
              GROUP BY model""").fetchall()
            for row in durations:
                key = ("Codex", row["model"])
                if key in result:
                    result[key]["duration"] = row["seconds"]
            compression = db.execute("""SELECT model,SUM(source_bytes) original,SUM(output_bytes) returned
              FROM usage WHERE source='local' AND status='ok' AND source_bytes>0 AND output_bytes>0
              GROUP BY model""").fetchall()
            for row in result.values():
                row["compression_estimate"] = None
            for row in compression:
                key = ("Local", row["model"])
                if key in result:
                    result[key]["compression_estimate"] = 1 - row["returned"] / row["original"]
            return list(result.values())


class Recorder:
    """An Ollama request's metadata sink; telemetry failure must not break analysis."""
    def __init__(self, store, tool, model, input_chars, *, role=None, source_bytes=None, group_id=None,
                 logical_id=None, escalated_from=None, escalation_reason=None, route_cap=None, selection_reason=None):
        self.store, self.tool, self.model, self.input_chars = store, tool, model, input_chars
        self.id = str(uuid.uuid4())
        self.role, self.source_bytes, self.group_id = role, source_bytes, group_id
        self.route = dict(logical_id=logical_id,escalated_from=escalated_from,escalation_reason=escalation_reason,
                          route_cap=route_cap,selection_reason=selection_reason)
        self.active_route = dict(role=role,tool=tool,escalated_from=escalated_from,escalation_reason=escalation_reason,
                                 route_cap=route_cap,selection_reason=selection_reason)
        self.started = time.time()
        self.tick = time.monotonic()
        self.last_progress = 0
        self.progress(0, force=True)
        LOG.info("request=%s tool=%s model=%s input_chars=%d", self.id, tool, model, input_chars)

    def safe(self, function, **kwargs):
        try:
            function(**kwargs)
        except (sqlite3.Error, OSError):
            LOG.warning("telemetry_write_failed request=%s", self.id)

    def progress(self, chunks, force=False, generated_chars=0):
        now = time.monotonic()
        if force or now - self.last_progress >= 1:
            self.last_progress = now
            self.safe(self.store.activity, id=self.id, source="local", session_id=self.id,
                      model=self.model, started=self.started, updated=time.time(),
                      status="generating" if chunks else "loading", chunks=chunks,
                      output_tokens=(generated_chars + 3) // 4 if chunks else None, **self.active_route)

    def finish(self, final, output_bytes, status):
        duration = time.monotonic() - self.tick
        def count(key):
            value = final.get(key)
            return value if type(value) is int and 0 <= value < 2 ** 63 else None
        input_tokens, output_tokens = count("prompt_eval_count"), count("eval_count")
        seconds = (count("eval_duration") or 0) / 1e9
        tokens = dict(input_tokens=input_tokens, output_tokens=output_tokens,
                      cached_input_tokens=count("prompt_eval_cached_count"),
                      total_tokens=(input_tokens + output_tokens) if input_tokens is not None and output_tokens is not None else None)
        compression = 1 - output_bytes / self.source_bytes if status == "ok" and self.source_bytes and output_bytes else None
        self.safe(self.store.usage, id=self.id, source="local", session_id=self.id, model=self.model,
                  tool=self.tool, started=self.started, duration=duration, **tokens,
                  tokens_per_second=output_tokens / seconds if seconds and output_tokens is not None else None,
                  input_chars=self.input_chars, output_bytes=output_bytes, status=status,
                  role=self.role, source_bytes=self.source_bytes, context_compression=compression, group_id=self.group_id,
                  generation_seconds=seconds or None,load_seconds=(count('load_duration') or 0)/1e9, **self.route)
        self.safe(self.store.activity, id=self.id, source="local", session_id=self.id, model=self.model,
                  started=self.started, updated=time.time(), status=status, output_tokens=output_tokens, **self.active_route)
        LOG.info("request=%s tool=%s model=%s output_bytes=%d duration=%.2fs input_tokens=%s output_tokens=%s compression=%s status=%s",
                 self.id, self.tool, self.model, output_bytes, duration, input_tokens, output_tokens, compression, status)
