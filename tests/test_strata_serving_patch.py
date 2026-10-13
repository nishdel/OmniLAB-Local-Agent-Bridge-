"""Opt-in offline tests against the pinned, separately patched Strata source.

Set LAB_STRATA_SERVING_SOURCE to that copy; no downloads or model loading.
The ordinary suite still tests rejection of unknown upstream bytes.
"""

import asyncio
import hashlib
import importlib
import json
import os
import queue
import io
import socket
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from localagentbridge.inference import ChatProvider, ProviderError
from localagentbridge.task_contract import TaskLimits
from scripts.strata_serving_patch import patch_server


def test_unknown_source_is_rejected():
    with pytest.raises(ValueError, match="reviewed upstream"):
        patch_server(b"unreviewed source")


@pytest.fixture
def upstream(monkeypatch):
    source = os.environ.get("LAB_STRATA_SERVING_SOURCE")
    if not source:
        pytest.skip("separate pinned Strata serving copy not supplied")
    root = Path(source).resolve(strict=True)
    provenance = json.loads((Path(__file__).parents[1] /
        "docs/qualification/strata-serving-provenance.json").read_text())
    assert hashlib.sha256((root / "serve/server.py").read_bytes()).hexdigest() == provenance["patched_server_sha256"]
    monkeypatch.syspath_prepend(str(root))
    server = importlib.import_module("serve.server")
    assert Path(server.__file__).resolve() == root / "serve/server.py"
    fakes = importlib.import_module("serve.test_server")
    return server, fakes


@pytest.fixture
def service(upstream):
    server, fakes = upstream
    tok = server.ByteTokenizer()
    engine = fakes.NonFiniteEngine(tok, "hello world", max_context=4096)
    svc = server.Service(engine, tok, fakes.ChatTemplate(fakes.ROOT / "serve/chat_template.jinja"))
    httpd = server.serve(svc, port=0)
    try:
        yield svc, f"http://127.0.0.1:{httpd.server_address[1]}"
    finally:
        httpd.shutdown()
        httpd.server_close()


def request(base, path, body=None):
    req = urllib.request.Request(base + path, data=None if body is None else json.dumps(body).encode(),
        headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.status, response.read().decode()
    except urllib.error.HTTPError as error:
        with error:
            return error.code, error.read().decode()


def payload(path, stream):
    if path == "/v1/responses":
        return {"model": "m", "input": "hi", "stream": stream, "max_output_tokens": 64}
    return {"model": "m", "messages": [{"role": "user", "content": "hi"}],
        "stream": stream, "max_tokens": 64}


@pytest.mark.parametrize("path", ["/v1/chat/completions", "/v1/responses", "/v1/messages"])
@pytest.mark.parametrize("stream", [False, True])
@pytest.mark.parametrize("cut", [None, 0, 3])
def test_normal_and_nonfinite_http(service, path, stream, cut):
    svc, base = service
    svc.engine.plan = [cut]
    code, text = request(base, path, payload(path, stream))
    assert len(svc.engine.calls) == 1
    if cut is None:
        assert code == 200
        if not stream:
            assert "hello world" in text
        else:
            values = [json.loads(line[6:]) for line in text.splitlines()
                if line.startswith("data: ") and line != "data: [DONE]"]
            if path == "/v1/chat/completions":
                assert "".join(v["choices"][0]["delta"].get("content", "") or
                    v["choices"][0]["delta"].get("reasoning_content", "")
                    for v in values if v.get("choices")) == "hello world"
            elif path == "/v1/messages":
                assert "".join(v.get("delta", {}).get("text", "") or
                    v.get("delta", {}).get("thinking", "") for v in values) == "hello world"
            else:
                assert "hello world" in text
        assert svc.metrics()["requests"][0]["finish"] == "stop"
    else:
        assert code == (200 if stream else 503)
        assert "non-finite" in text and '"error"' in text
        assert svc.metrics()["requests"][0]["finish"] == "error"
        assert '"finish_reason": "stop"' not in text
        assert '"finish_reason": "length"' not in text
        assert "event: response.completed" not in text
        assert "event: message_stop" not in text


@pytest.mark.parametrize("stream", [False, True])
@pytest.mark.parametrize("cut", [0, 3])
def test_lab_withholds_failed_response(service, monkeypatch, stream, cut):
    svc, base = service
    svc.engine.plan = [cut]
    provider = ChatProvider("strata", {"endpoint": base, "enabled": True})
    monkeypatch.setattr(provider, "inspect", AsyncMock(return_value={
        "ready": True, "identity_verified": True, "context_tokens": 4096,
        "tools_advertised": True,
    }))  # Fake transport test only; live admission must verify the complete binding.
    limits = TaskLimits(context_tokens=4096, output_tokens=64, output_bytes=16384,
        transport_retries=0, inference_deadline_seconds=10)
    with pytest.raises(ProviderError):
        asyncio.run(provider.chat("m", [{"role": "user", "content": "hi"}], limits, stream=stream))
    assert len(svc.engine.calls) == 1
    assert provider.last_usage is None


def test_dead_engine_cannot_reload(service, upstream):
    svc, base = service
    server, fakes = upstream
    svc.engine = fakes.DyingEngine(svc.tok, "hello world", max_context=4096)
    code, text = request(base, "/v1/chat/completions", payload("/v1/chat/completions", True))
    assert code == 200 and '"error"' in text
    for _ in range(2):
        code, text = request(base, "/v1/chat/completions", payload("/v1/chat/completions", False))
        assert code == 503 and "automatic restart disabled" in text
        assert json.loads(request(base, "/health")[1])["loaded"] is False
        with pytest.raises(server.EngineDied):
            svc.ensure_loaded()
        with pytest.raises(server.EngineDied):
            svc.load()
    assert svc.engine.restarts == 0


def test_lab_never_returns_partial_tool_call(service, upstream, monkeypatch):
    svc, base = service
    _, fakes = upstream
    script = '</think><tool_call><function=edit><parameter=text>partial'
    svc.engine = fakes.NonFiniteEngine(svc.tok, script, max_context=4096)
    svc.engine.plan = [len(svc.engine.script) - 1]  # Fail before the end-of-turn token.
    provider = ChatProvider("strata", {"endpoint": base, "enabled": True})
    monkeypatch.setattr(provider, "inspect", AsyncMock(return_value={
        "ready": True, "identity_verified": True, "context_tokens": 4096,
        "tools_advertised": True,
    }))
    tools = [{"type": "function", "function": {"name": "edit", "parameters": {
        "type": "object", "properties": {"text": {"type": "string"}}}}}]
    with pytest.raises(ProviderError):
        asyncio.run(provider.chat("m", [{"role": "user", "content": "hi"}],
            TaskLimits(context_tokens=4096, output_tokens=256, output_bytes=16384,
                transport_retries=0, inference_deadline_seconds=10), tools=tools))
    assert len(svc.engine.calls) == 1
    assert svc.metrics()["requests"][0]["finish"] == "error"


@pytest.mark.parametrize("ready", [False, True])
def test_one_native_start_with_real_child(upstream, monkeypatch, ready):
    server, _ = upstream
    monkeypatch.setattr(server.StrataEngine, "_lab_start_claimed", False)
    starts = []
    # A real owned Python child stands in for the native executable; never touches a GPU.
    code = "print('READY 4096 stop', flush=True); input()" if ready else "raise SystemExit(17)"

    def spawn(label, argv, **kwargs):
        proc = subprocess.Popen([sys.executable, "-I", "-B", "-u", "-c", code], **kwargs)
        starts.append(proc)
        return proc

    monkeypatch.setattr(server, "popen", spawn)
    engine = None
    try:
        if ready:
            engine = server.StrataEngine(sys.executable, [])
            assert engine.alive()
            # Natural child exit after receiving one protocol command.
            engine.proc.stdin.write("GEN 1 1\n")
            engine.proc.stdin.flush()
            engine.proc.wait(timeout=5)
            with pytest.raises(server.EngineDied, match="restart disabled"):
                engine.restart()
        else:
            with pytest.raises(server.EngineDied, match="before it was ready"):
                server.StrataEngine(sys.executable, [])
        with pytest.raises(server.EngineDied, match="start already consumed"):
            server.StrataEngine(sys.executable, [])
        assert len(starts) == 1
    finally:
        if engine:
            engine.close()
        for proc in starts:
            if proc.poll() is None:
                proc.kill()
            proc.wait(timeout=5)
        assert all(proc.poll() is not None for proc in starts)


@pytest.mark.parametrize("stream", [False, True])
def test_disconnect_cancels_once(service, upstream, stream):
    svc, base = service
    _, fakes = upstream

    class CountedSlow(fakes.SlowPromptEngine):
        calls = 0
        cancelled_after = None

        def generate(self, *args, **kwargs):
            self.calls += 1
            yield from super().generate(*args, **kwargs)

    svc.engine = CountedSlow(svc.tok, "hello", max_context=4096)
    body = json.dumps(payload("/v1/chat/completions", stream)).encode()
    with socket.create_connection(("127.0.0.1", int(base.rsplit(":", 1)[1])), timeout=5) as conn:
        conn.sendall(b"POST /v1/chat/completions HTTP/1.1\r\nHost: localhost\r\nContent-Type: application/json\r\n"
            b"Content-Length: " + str(len(body)).encode() + b"\r\n\r\n" + body)
        deadline = time.monotonic() + 3
        while not svc.engine.calls and time.monotonic() < deadline:
            time.sleep(.01)
        assert svc.engine.calls == 1
    deadline = time.monotonic() + 5
    while not svc.metrics()["requests"] and time.monotonic() < deadline:
        time.sleep(.05)
    assert svc.engine.cancelled_after is not None
    assert svc.metrics()["requests"][0]["finish"] in ("cancel", "disconnect")
    assert svc.engine.calls == 1


def test_native_detection_remains(upstream):
    _, fakes = upstream
    fakes.NonFiniteLogits("test_engine_done_line_raises").test_engine_done_line_raises()


@pytest.mark.parametrize("terminal", ["DONE 2 3 1.0 2.0 nonfinite 0 0 0", "ERR numerical error", None])
def test_failed_stop_drain_is_not_success(upstream, terminal):
    from types import SimpleNamespace

    server, fakes = upstream
    engine = object.__new__(server.StrataEngine)
    engine.lines = queue.Queue()
    tok = server.ByteTokenizer()
    for token in tok.encode("hello") + list(server.EOS_IDS)[:1]:
        engine.lines.put("T " + str(token))
    engine.lines.put(terminal)
    engine.proc = SimpleNamespace(stdin=io.StringIO())
    engine.alive = lambda: True
    engine.silence_s, engine.can_stop, engine.last = 0, True, None
    engine.max_context = 4096
    svc = server.Service(engine, tok, fakes.ChatTemplate(fakes.ROOT / "serve/chat_template.jinja"))
    events = []
    with pytest.raises((ValueError, server.EngineDied)):
        for event in svc.run(tok.encode("hi"), False, None, 64, {}, threading.Event()):
            events.append(event)
    assert not any(kind == "done" for kind, _ in events)
    assert svc.metrics()["requests"][0]["finish"] == "error"
    assert engine.proc.stdin.getvalue().count("GEN ") == 1


def test_service_cancel_not_success(service):
    svc, _ = service
    cancel = threading.Event()
    cancel.set()
    with pytest.raises(ValueError, match="generation cancelled"):
        list(svc.run(svc.tok.encode("hi"), False, None, 64, {}, cancel))
    assert len(svc.engine.calls) <= 1


@pytest.mark.parametrize("path", ["/v1/chat/completions", "/v1/responses", "/v1/messages"])
@pytest.mark.parametrize("stream", [False, True])
def test_cancelled_http_never_reports_success(service, upstream, path, stream):
    svc, base = service
    server, _ = upstream

    class CancelAfterPartial(server.MockEngine):
        calls = 0

        def generate(self, ids, max_new, sampling, cancel, embeddings=None):
            self.calls += 1
            yield from self.tok.encode("part")
            cancel.set()

    svc.engine = CancelAfterPartial(svc.tok, "unused", max_context=4096)
    code, text = request(base, path, payload(path, stream))
    assert code == (200 if stream else 503)
    assert '"error"' in text and "generation cancelled" in text
    assert '"finish_reason": "stop"' not in text
    assert "event: response.completed" not in text
    assert "event: message_stop" not in text
    assert svc.metrics()["requests"][0]["finish"] == "cancel"
    assert svc.engine.calls == 1


def test_cancelled_queue_never_starts_generation(service):
    svc, _ = service
    cancel = threading.Event()
    cancel.set()
    with svc.fifo:
        with pytest.raises(ValueError, match="cancelled while queued"):
            list(svc.run(svc.tok.encode("hi"), False, None, 64, {}, cancel))
    assert not svc.engine.calls
    assert svc.status["queued"] == 0
