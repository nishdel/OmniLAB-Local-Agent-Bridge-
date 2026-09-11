"""All seven tools and feedback/consensus through a real MCP stdio connection."""
import asyncio
from datetime import timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
import sys
import threading
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from localagentbridge.smoke import CAPABILITIES
from localagentbridge.telemetry import Store
from test_bridge import SUMMARY
from test_v2_routing import ROLES, OPINION


def test_all_capabilities_over_mcp(tmp_path):
    chats = []
    answers = {
        "Summary": SUMMARY,
        "ContextSelection": {"candidate_ids": [0], "uncertainties": []},
        "CodeAnalysis": {"behavior": "Adds inputs", "findings": [], "uncertainties": [], "recommended_tests": ["Test zero"], "confidence": "high"},
        "TestAnalysis": {"failing_tests_errors": ["test_add"], "likely_cause": "Bad expectation", "likely_affected_components": ["math.py"], "confidence": "high", "recommended_investigation": ["Check expectation"]},
        "DiffReview": {"possible_bugs": ["Subtraction replaces addition"], "regressions": [], "suspicious_logic": [], "missing_tests": [], "confidence": "high"},
        "Triage": {"task_type": "coding", "risk": "low", "local_steps": ["Inspect helper"], "codex_decisions": ["Choose fix"], "confidence": "high"},
        "Opinion": OPINION,
    }
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass
        def send(self, body):
            self.send_response(200)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        def do_GET(self):
            self.send(json.dumps({"models": [{"name": m if ":" in m else m + ":latest"} for m in ROLES.values()]}).encode())
        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            chats.append(body)
            answer = answers[body["format"]["title"]]
            self.send((json.dumps({"message": {"content": json.dumps(answer)}, "done": True,
                       "prompt_eval_count": 50, "eval_count": 10, "eval_duration": 1000000000}) + "\n").encode())
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    root = tmp_path / "repo"
    root.mkdir()
    (root / "math.py").write_text("def add_numbers(a, b):\n    return a + b\n")
    config = tmp_path / "config.toml"
    config.write_text("source_root='repo'\ndata_dir='data'\n[roles]\n" + "\n".join(f'{k}="{v}"' for k, v in ROLES.items()))
    env = {k: v for k, v in os.environ.items() if not k.startswith("LAB_")}
    env.update(LAB_CONFIG=str(config), LAB_ENDPOINT=f"http://127.0.0.1:{server.server_port}")
    calls = {
        "find_relevant_context": {"task": "add numbers"},
        "summarize_context": {"task": "Summarize helper", "file_paths": ["math.py"]},
        "analyze_code": {"file_paths": ["math.py"]},
        "analyze_test_output": {"output": "test_add failed"},
        "review_diff": {"diff": "- return a+b\n+ return a-b"},
        "triage_task": {"task": "Inspect math helpers", "context_chars": 4000, "file_count": 4},
        "second_opinion": {"question": "Preserve addition?", "context": "Callers rely on addition."},
    }
    async def run():
        params = StdioServerParameters(command=sys.executable, args=["-m", "localagentbridge", "server"], env=env)
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write, read_timeout_seconds=timedelta(seconds=20)) as session:
                await session.initialize()
                assert {tool.name for tool in (await session.list_tools()).tools} == CAPABILITIES
                ids = []
                for tool, arguments in calls.items():
                    result = await session.call_tool(tool, arguments)
                    assert not result.isError, result
                    data = json.loads(result.content[0].text)
                    assert len(result.content[0].text.encode()) <= 3000
                    ids.append(data["_meta"]["request_id"])
                result = await session.call_tool("triage_task", {"feedback": [{"request_id": id, "outcome": "accepted"} for id in ids]})
                assert not result.isError
                assert json.loads(result.content[0].text)["feedback_recorded"] == 7
                result = await session.call_tool("second_opinion", dict(calls["second_opinion"], consensus=True))
                assert not result.isError and len(result.content[0].text.encode()) <= 3000
                assert len(json.loads(result.content[0].text)["opinions"]) == 2
    try:
        asyncio.run(run())
    finally:
        server.shutdown()
        server.server_close()
    assert len(chats) == 9
    with Store(tmp_path / "data").connect() as db:
        assert db.execute("SELECT COUNT(*) FROM usage WHERE outcome='accepted'").fetchone()[0] == 7
