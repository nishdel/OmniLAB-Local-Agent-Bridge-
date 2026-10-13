# Reference benchmarks

For the current offline six-category, four-configuration preparation, use the
[readiness comparison](../SELECTIVE-PILOT.md#readiness-comparison). Its fixtures,
mock runner, energy integration and complete-cost worksheet are new instrumentation;
they contain no measured live comparison. The reference results below remain
unchanged historical evidence.

Reference results describe one Windows test machine and a small, adversarial
LocalAgentBridge workload. They are not universal model scores. GPU, RAM, CPU,
quantization, context length, Ollama version and exact model digest all matter.

See the [v0.4 comparison and routing decision](v0.4-results.md), its
[aggregate measurements](v0.4-results.json), and the preserved
[v0.3 reference aggregates](v0.3-reference.json).

The preserved paired suite has 11 exercises: repository discovery, code search,
configuration summary, an empty-input defect, capped retry-delay implementation,
registry-port test cases, a deliberately incorrect addition test expectation,
an addition-to-subtraction diff, cached-token accounting, boundary-test triage,
and an unsafe None-return proposal. It includes seven MCP output schemas.

Public fixtures are in tests/fixtures/paired_requests.json. They contain only
this project's historical source and synthetic exercises. Source/message hashes,
8K context, 600-token budget, temperature zero and the original think=false setting
are checked by tests. Model names vary; the original task/prompt bodies do not.
Do not overwrite old runs. An explicitly necessary protocol adaptation must be
labelled separately and must not be advertised as identical-prompt protocol pairing.

Run real benchmarks only with an explicit configured model list and a resource
budget/cap that permits those models:

```powershell
.\.venv\Scripts\python.exe scripts/benchmark_v03.py --config config.toml --models qwen3:4b --output benchmarks/v04/my-run
```

The filename is retained for compatibility with existing tooling. Benchmark output
is local and ignored. It includes raw bounded answers and request identifiers for
independent review. Never publish a raw run from a private repository. This directory
contains reviewed anonymized aggregates and explanations only.

Accepted means no substantive correction, corrected means useful but needing
correction, rejected means materially unreliable. A transport/schema success is
not an accepted result. Confidence and local model agreement never determine grades.
Performance aggregates must include missing counters as unavailable, not free calls.
Local compression is input/returned bytes; potential avoided context is not measured
Codex token reduction or proof of avoided cloud requests.
