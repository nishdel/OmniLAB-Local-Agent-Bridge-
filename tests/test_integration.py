import asyncio
from datetime import timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import sys
import threading
import urllib.request
import pytest
from google.protobuf.json_format import ParseDict
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from opentelemetry.proto.collector.logs.v1.logs_service_pb2 import ExportLogsServiceRequest
from localagentbridge.otel import make_receiver
from localagentbridge.schemas import SCHEMAS
from localagentbridge.smoke import EXAMPLES, CAPABILITIES
from localagentbridge.telemetry import Store
from test_telemetry import otel_document


def test_real_mcp_stdio_roundtrip_with_fake_ollama(tmp_path):
    called = []
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass
        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            called.append(body)
            schema = body["format"]
            result = {key: "low" if key == "confidence" else "Fixture finding" if spec.get("type") == "string" else []
                      for key, spec in schema["properties"].items()}
            data = (json.dumps({"message": {"content": json.dumps(result)}, "done": False}) + "\n" +
                    json.dumps({"done": True, "prompt_eval_count": 50, "eval_count": 15, "eval_duration": 1000000000}) + "\n").encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/x-ndjson")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    env = dict(os.environ, LAB_ENDPOINT=f"http://127.0.0.1:{server.server_port}", LAB_DATA_DIR=str(tmp_path / "data"))
    # Explicit empty v0.1 config keeps the test independent of a developer's
    # auto-discovered config.toml (introduced by the v0.4 setup workflow).
    legacy_config = tmp_path / 'legacy.toml'
    legacy_config.write_text('')
    env['LAB_CONFIG'] = str(legacy_config)
    async def run():
        params = StdioServerParameters(command=sys.executable, args=["-m", "localagentbridge", "server"], env=env)
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write, read_timeout_seconds=timedelta(seconds=20)) as session:
                await session.initialize()
                tools = (await session.list_tools()).tools
                assert {tool.name for tool in tools} == CAPABILITIES
                assert all(tool.annotations.readOnlyHint for tool in tools)
                for name, args in EXAMPLES.items():
                    result = await session.call_tool(name, args)
                    assert not result.isError
                    assert result.structuredContent is None
                    text = result.content[0].text
                    assert len(text.encode()) <= 3000
                    value = json.loads(text)
                    value.pop("truncated")
                    SCHEMAS[name].model_validate(value)
                failed = await session.call_tool("review_diff", {"diff": "x" * 10001})
                assert failed.isError and len(failed.content[0].text) < 250
                failed = await session.call_tool("review_diff", {"diff": "SENSITIVE" * 4000})
                assert failed.isError and len(failed.content[0].text.encode()) <= 3000
    try:
        asyncio.run(run())
    finally:
        server.shutdown()
        server.server_close()
    assert len(called) == 3
    assert Store(tmp_path / "data").totals()[0]["total_tokens"] == 195


@pytest.mark.parametrize("binary", [False, True])
def test_loopback_otlp_json_and_protobuf(tmp_path, binary):
    store = Store(tmp_path)
    server = make_receiver(store, 0)
    assert server.server_address[0] == "127.0.0.1"
    threading.Thread(target=server.serve_forever, daemon=True).start()
    doc = otel_document()
    data = ParseDict(doc, ExportLogsServiceRequest()).SerializeToString() if binary else json.dumps(doc).encode()
    kind = "application/x-protobuf" if binary else "application/json"
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        request = urllib.request.Request(f"http://127.0.0.1:{server.server_port}/v1/logs", data,
                                         headers={"Content-Type": kind})
        with opener.open(request, timeout=5) as response:
            assert response.status == 200
        assert store.totals()[0]["total_tokens"] == 100
    finally:
        server.shutdown()
        server.server_close()
