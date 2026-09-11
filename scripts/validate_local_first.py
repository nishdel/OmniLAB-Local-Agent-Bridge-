"""Opt-in real MCP workload. No mocks, model code execution, or automatic acceptance.

Prints bounded results for a human/Codex review; saves metadata only. All inputs
are this project's files or explicit small fixtures.
"""
import argparse
import asyncio
from datetime import timedelta
import json
import os
from pathlib import Path
import sys
import time

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from localagentbridge.config import load_config
from localagentbridge.schemas import compact
from localagentbridge.telemetry import Store


CASES = [
    ("repository_discovery", "find_relevant_context", {
        "task": "Find Ollama streaming requests, model routing and request timeout handling.", "scope": "localagentbridge"}),
    ("code_search", "find_relevant_context", {
        "task": "Find Store.report and the accepted corrected rejected feedback validation and atomic updates.", "scope": "localagentbridge"}),
    ("code_summarization", "summarize_context", {
        "task": "Give three findings: Config.resolve_model role selection; Config.__post_init__ loopback enforcement; DelegationConfig defaults including max_files_for_local_analysis and max_failed_local_attempts. Preserve values and method names.",
        "file_paths": ["localagentbridge/config.py"]}),
    ("simple_analysis", "analyze_code", {
        "text": "def average(xs):\n    return sum(xs) / len(xs)\n", "task": "Identify the empty-input failure and a focused test."}),
    ("implementation_suggestion", "analyze_code", {
        "text": "def retry_delay(attempt, base=0.5, cap=5.0):\n    return max(base * 2 ** attempt, cap)\n",
        "task": "Delay must grow from base and never exceed cap for nonnegative attempt. Give the corrected return expression and boundary tests."}),
    ("coding_task", "analyze_code", {
        "file_paths": ["localagentbridge/routing.py"],
        "task": "Propose compact Python parametrized test cases for canonical, including untagged names, tagged names, and a registry hostname with port. Put literal input/expected pairs in findings."}),
    ("test_failure", "analyze_test_output", {
        "output": "FAILED tests/test_math.py::test_add - assert 4 == 5\nadd(2, 2) returned 4; expected 5\nImplementation: def add(a,b): return a+b\nContract: ordinary integer addition."}),
    ("diff_review", "review_diff", {
        "diff": "--- a/math_utils.py\n+++ b/math_utils.py\n@@ -1,2 +1,2 @@\n def add(a, b):\n-    return a + b\n+    return a - b\n",
        "task": "Preserve ordinary integer addition."}),
    ("general_reasoning", "second_opinion", {
        "question": "Should the dashboard add cached tokens again and show 175 total tokens?",
        "context": "Provider reports input_tokens=100, cached_input_tokens=60, output_tokens=15, total_tokens=115. Cached tokens are a subset of input."}),
    ("task_triage", "triage_task", {
        "task": "Inspect three small pure-function files and propose missing boundary tests; Codex reviews any patch.",
        "context_chars": 4000, "file_count": 3, "capability": "implementation", "complexity": "moderate"}),
    ("consensus_review", "second_opinion", {
        "question": "Is returning None for empty average input safe without changing callers?",
        "context": "Callers expect a float and immediately add 1 to the result. They do not check for None.", "consensus": True}),
    ("small_local_gate", "triage_task", {"task": "Inspect one pure function", "context_chars": 100, "file_count": 1}),
    ("large_context_gate", "triage_task", {"task": "Locate relevant helpers", "context_chars": 50000, "file_count": 1}),
    ("complexity_gate", "triage_task", {"task": "Resolve tightly coupled changes", "complexity": "complex"}),
    ("ambiguity_gate", "triage_task", {"task": "Choose unspecified behavior", "ambiguous": True}),
    ("risk_gate", "triage_task", {"task": "Change an authentication boundary", "risk": "high"}),
    ("capability_gate", "triage_task", {"task": "Choose system architecture", "capability": "architecture"}),
    ("confidence_gate", "triage_task", {"task": "Check an uncertain local result", "confidence": "low"}),
    ("failed_attempts_gate", "triage_task", {"task": "Resolve two failed local attempts", "failed_local_attempts": 2}),
]


async def run(config_path, output, categories):
    cfg = load_config(config_path)
    store = Store(cfg.data_dir)
    report = {"started": time.time(), "config": str(config_path.resolve()), "cases": []}
    args = ["-m", "localagentbridge", "--config", str(config_path.resolve()), "server"]
    params = StdioServerParameters(command=sys.executable, args=args, env=dict(os.environ))
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write, read_timeout_seconds=timedelta(seconds=620)) as session:
            await session.initialize()
            for category, tool, arguments in CASES:
                if categories and category not in categories:
                    continue
                start = time.time()
                reply = await session.call_tool(tool, arguments)
                result = json.loads(reply.content[0].text)
                print(compact({"category": category, "result": result}), flush=True)
                # Query by the serialized run interval so errors also retain request IDs.
                with store.connect() as db:
                    rows = [dict(r) for r in db.execute("SELECT * FROM usage WHERE source='local' AND started>=? AND tool=? ORDER BY started", (start, tool))]
                report["cases"].append({"category": category, "tool": tool, "error": bool(reply.isError),
                    "argument_bytes": len(compact(arguments).encode()), "returned_bytes": len(compact(result).encode()),
                    "latency_seconds": time.time() - start, "agreement": result.get("agreement"),
                    "delegation": result.get("delegation"), "requests": rows})
                report["finished"] = time.time()
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    if any(case["error"] for case in report["cases"]):
        raise SystemExit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("config.toml"))
    parser.add_argument("--output", type=Path, default=Path("data/local-first-validation.json"))
    parser.add_argument("--category", action="append", choices=[c[0] for c in CASES])
    options = parser.parse_args()
    asyncio.run(run(options.config, options.output, options.category))
