"""Small loopback OTLP/HTTP logs receiver. Discard bodies and unknown fields."""
import gzip
import hashlib
from http.server import BaseHTTPRequestHandler, HTTPServer
import io
import json
import time
from google.protobuf.json_format import MessageToDict
from opentelemetry.proto.collector.logs.v1.logs_service_pb2 import ExportLogsServiceRequest
from .telemetry import LOG

MAX_BODY = 2 * 1024 * 1024


def attributes(items):
    allowed = {"event.name", "event_name", "model", "conversation.id", "conversation_id", "session_id",
               "event.kind", "event_kind", "kind", "response_id", "response.id", "input_token_count",
               "cached_token_count", "output_token_count", "reasoning_token_count", "total_token_count",
               "input_tokens", "cached_input_tokens", "output_tokens", "reasoning_output_tokens", "total_tokens"}
    result = {}
    for item in items:
        key = item.get("key")
        if key in allowed:
            value = item.get("value", {})
            scalar = next((value[k] for k in ("stringValue", "intValue", "doubleValue") if k in value), None)
            if scalar is not None:
                result[key] = scalar
    return result


def ingest_logs(document, store):
    accepted = 0
    for resource in document.get("resourceLogs", []):
        common = attributes(resource.get("resource", {}).get("attributes", []))
        for scope in resource.get("scopeLogs", []):
            for record in scope.get("logRecords", []):
                a = common | attributes(record.get("attributes", []))
                # Some exporters put structured attributes in a kvlist body.
                a.update(attributes(record.get("body", {}).get("kvlistValue", {}).get("values", [])))
                name = record.get("eventName") or a.get("event.name") or a.get("event_name")
                if name not in ("codex.sse_event", "codex.websocket_event"):
                    continue
                kind = a.get("event.kind") or a.get("event_kind") or a.get("kind")
                if kind != "response.completed":
                    continue
                session = a.get("conversation.id") or a.get("conversation_id") or a.get("session_id")
                model = a.get("model")
                if not isinstance(session, str) or not isinstance(model, str):
                    continue  # No safe reconciliation key; rollout remains available.
                values = {}
                aliases = {"input_tokens": "input_token_count", "cached_input_tokens": "cached_token_count",
                           "output_tokens": "output_token_count", "reasoning_output_tokens": "reasoning_token_count",
                           "total_tokens": "total_token_count"}
                try:
                    for key, alias in aliases.items():
                        raw = a.get(key, a.get(alias))
                        values[key] = max(0, int(raw)) if raw is not None else None
                    if values["total_tokens"] is None and values["input_tokens"] is not None and values["output_tokens"] is not None:
                        values["total_tokens"] = values["input_tokens"] + values["output_tokens"]
                    stamp = record.get("timeUnixNano") or record.get("observedTimeUnixNano")
                    if not stamp or values["total_tokens"] is None:
                        continue
                    when = int(stamp) / 1e9
                except (ValueError, TypeError, OverflowError):
                    continue
                identity = a.get("response.id") or a.get("response_id") or str(stamp)
                identity = hashlib.sha256(json.dumps([session, model, identity, values], sort_keys=True).encode()).hexdigest()
                store.usage(id="otel:" + identity, source="otel", session_id=session[:160], model=model,
                            started=when, **values)
                accepted += 1
    return accepted


def make_receiver(store, port):
    class Handler(BaseHTTPRequestHandler):
        def setup(self):
            super().setup()
            self.connection.settimeout(3)

        def log_message(self, *args):
            pass  # Never log request bodies, URLs or headers.

        def do_POST(self):
            if self.path != "/v1/logs":
                self.send_error(404)
                return
            if self.headers.get("Origin") or self.headers.get("Transfer-Encoding"):
                self.send_error(403)
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= MAX_BODY:
                    raise ValueError()
                raw = self.rfile.read(length)
                encoding = self.headers.get("Content-Encoding", "identity")
                if encoding == "gzip":
                    with gzip.GzipFile(fileobj=io.BytesIO(raw)) as zipped:
                        raw = zipped.read(MAX_BODY + 1)
                elif encoding != "identity":
                    raise ValueError()
                if len(raw) > MAX_BODY:
                    raise ValueError()
                content_type = self.headers.get("Content-Type", "").split(";")[0]
                if content_type == "application/x-protobuf":
                    request = ExportLogsServiceRequest()
                    request.ParseFromString(raw)
                    document = MessageToDict(request)
                    reply = b""
                elif content_type == "application/json":
                    document = json.loads(raw)
                    reply = b"{}"
                else:
                    raise ValueError()
                accepted = ingest_logs(document, store)
                if accepted:
                    LOG.info("codex_otel accepted_records=%d", accepted)
                self.send_response(200)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(reply)))
                self.end_headers()
                self.wfile.write(reply)
            except Exception:
                # Untrusted HTTP payload; deliberately omit exception details.
                self.send_error(400, "Invalid telemetry payload")

    server = HTTPServer(("127.0.0.1", port), Handler)
    return server
