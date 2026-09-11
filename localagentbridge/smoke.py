"""A real MCP client, no direct bypass of the server's tool handlers."""
import os
from pathlib import Path
import sys
from datetime import timedelta
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

EXAMPLES = {
    "summarize_context": {"task": "Explain how add works and suggest one test.",
                          "files": [{"path": "math_utils.py", "content": "def add(a, b):\n    return a + b\n"}]},
    "analyze_test_output": {"output": "FAILED tests/test_math.py::test_add - assert 4 == 5\nadd(2, 2) returned 4; expected 5"},
    "review_diff": {"diff": "diff --git a/math_utils.py b/math_utils.py\n--- a/math_utils.py\n+++ b/math_utils.py\n@@ -1,2 +1,2 @@\n def add(a, b):\n-    return a + b\n+    return a - b\n", "task": "Preserve addition behavior."},
}

CAPABILITIES = {*EXAMPLES, "find_relevant_context", "analyze_code", "triage_task", "second_opinion"}

V2_EXAMPLES = {
    "find_relevant_context": {"task": "Ollama model routing and request timeout", "scope": "localagentbridge"},
    **EXAMPLES,
    "analyze_code": {"text": "def average(xs):\n    return sum(xs) / len(xs)\n", "task": "Find the empty-input edge case."},
    "triage_task": {"task": "Investigate repeated test failures and identify the smallest code area to inspect.", "context_chars": 4000, "file_count": 4},
    "second_opinion": {"question": "Is returning None for an empty average input a safe change?", "context": "Current callers expect a float; they do not check for None."},
}


async def smoke(config_path=None, all_tools=False, consensus=False):
    args = ["-m", "localagentbridge"]
    if config_path:
        args += ["--config", str(Path(config_path).resolve())]
    args += ["server"]
    params = StdioServerParameters(command=sys.executable, args=args, env=dict(os.environ))
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write, read_timeout_seconds=timedelta(seconds=620)) as session:
            await session.initialize()
            names = {t.name for t in (await session.list_tools()).tools}
            assert names == CAPABILITIES, names
            examples = V2_EXAMPLES if all_tools else EXAMPLES
            for name, arguments in examples.items():
                result = await session.call_tool(name, arguments)
                print(name + ":", flush=True)
                for block in result.content:
                    if block.type == "text":
                        print(block.text, flush=True)
                if result.isError:
                    raise RuntimeError(f"Smoke test failed: {name}")
            if consensus:
                args = dict(V2_EXAMPLES["second_opinion"], consensus=True)
                result = await session.call_tool("second_opinion", args)
                if result.isError:
                    raise RuntimeError(result.content[0].text)
                print("second_opinion consensus:", result.content[0].text, flush=True)
    print("PASS: seven MCP capabilities verified." if all_tools else "PASS: three MCP tools called the configured Ollama model.", flush=True)
