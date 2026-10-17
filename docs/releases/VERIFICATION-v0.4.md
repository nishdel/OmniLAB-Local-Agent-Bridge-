# v0.4 verification evidence

Reference checks ran on Windows with Python 3.13, Tcl/Tk, Ollama 0.32.5 and
the dependencies constrained in requirements.lock.txt. A separate clean directory
and virtual environment were created from the public source allowlist; no personal
config or usage history was copied. This is a same-PC clean-install check, not a
claim of testing a second physical Windows machine.

## Installation and MCP

- Installed the source with tray/dev/benchmark extras into the clean environment.
- Copied config.example.toml and generated a fresh SQLite database.
- doctor verified runtime dependencies, writable data, loopback Ollama and all
  three configured role defaults. Missing global registration is a diagnostic
  warning, not a failed Ollama connection.
- verify-models made three successful real calls: Qwen3 4B general, Coder7 coding,
  Phi4 Mini reasoning. No model substitution.
- smoke --all --consensus exercised all seven handlers and the additional
  two-participant consensus: nine successful local model calls, no handoffs/errors.
- Generated codex-config output was loaded by the installed Codex CLI with an
  isolated CODEX_HOME. codex mcp get localagentbridge --json confirmed the enabled
  stdio registration and exact clean-environment command. Global Codex settings
  were not changed.
- This proves configuration acceptance and real MCP-to-Ollama execution. It does
  not claim that a Codex reasoning turn chose to invoke a tool automatically. The
  README explains how to correlate an actual Codex invocation with local telemetry.

Final artifact verification is recorded in the public release checklist.
The final clean source copy repeated the three-model verification and all-tool
consensus smoke successfully: another 12 real local calls. Both clean runs retained
provider counters and model names; they are separate from quality-scored benchmarks.

## Regression and native UI

Final workspace regression: **126 passed, 1 skipped**, 29.04 seconds; lint passed.
Final clean-copy regression: **126 passed, 1 skipped**, 30.34 seconds; lint and
pip check passed. The final package was also built as a non-editable wheel and
inspected for packaged files and privacy-sensitive artifacts.
The skip is the Windows Developer-Mode symlink case. One intermediate run reported
an intermittent Tcl library lookup failure while heavy inference was running; the
file was present, and the subsequent complete run passed. Its cause was not established.

Tests cover legacy single-model behavior, all seven MCP handlers, response budgets,
repository boundaries/ignore rules, role/cap/resource/quality routing, bounded
escalation, feedback, additive migrations, Codex counter reconciliation, setup
diagnostics and release allowlist guards. GUI tests cover immediate tier updates,
missing/disabled/unregistered models, a fresh database, routing facts, correct
compression, local activity visibility and the first fixed-call failure popup.
Native focus checks verify SW_SHOWNOACTIVATE; repeated polls do not repeat a failure
popup. Existing v0.1–v0.3 tests remain in the suite.

Simulated Tk scaling of 100%, 125% and 150% passed. Synthetic screenshots at 100%
and 150% were inspected for readable wrapping and no normal horizontal scrolling.
This does not replace checks on every monitor, DPI configuration or Windows build.

## Resource use and local boundaries

The native stack uses Tk/pystray, without Electron or a web dashboard. A synthetic
hidden widget measured about 0.47% of one CPU core and 47 MiB working set over
20 seconds. Actual tray-plus-collector samples after grouped-query optimization
measured 2.60–4.10% of one core and 64–71 MiB over separate 45-second windows while
Codex telemetry activity varied (roughly 0.22–0.34% of this 12-thread system).
These short observations are not controlled proof of a fixed idle ceiling.
The final refreshed tray/collector measured **2.53% of one core and 60.1 MiB**
over another 45-second window while Codex activity and separate smoke calls continued.
Metadata inventory is infrequent; hidden aggregate rendering pauses.

The production telemetry listener was checked at 127.0.0.1:4318 only. MCP uses stdio.
No cloud telemetry, model shell tool, vector store, autonomous loop or public server
was introduced. Private benchmark/store/config material remains local and excluded.

## Model evidence

The v0.4 validation stores record **69 real local calls** (historical baseline
requests are excluded from this count):

| Model | Calls |
|---|---:|
| qwen3:4b | 6 |
| qwen2.5-coder:7b | 10 |
| phi4-mini | 8 |
| qwen3.5:9b-q4_K_M | 11 |
| qwen2.5-coder:14b-instruct-q4_K_M | 11 |
| gpt-oss:20b | 23 |

There were 11 failures, all from the preserved GPT-OSS think=false protocol.
The compatible low-thinking suite had no API/schema failures. These are local
request counts, not cloud calls avoided. Measured cloud calls/token reduction
remain unavailable. Benchmark payload compression is reported separately below.

See the [complete paired comparison](../benchmarks/v0.4-results.md) for exact tags,
protocol compatibility, independently reviewed A/C/R grades, failures, token/time
measurements, sampled memory, byte compression and routing recommendations.
The five historical baseline results are preserved. New calls are separate records.
No public release, GitHub push or unrelated project modification was performed.
