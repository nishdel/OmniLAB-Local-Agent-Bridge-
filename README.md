# LocalAgentBridge — v0.5 development

This checkout is **0.5.0.dev0**, unreleased. It adds opt-in skills, advisory roles
and controlled workflows over the existing router. Start with the
[workflow guide](docs/WORKFLOWS.md), [minimal configuration](examples/v0.5/minimal.toml)
and [implementation/validation report](docs/v0.5/IMPLEMENTATION.md).
The published v0.4.1 starter and release instructions below remain the stable path.
Workflow support is off unless explicitly enabled; personal configuration is unchanged.

Adaptive delegation is now available through the
[adaptive guide](docs/ADAPTIVE-DELEGATION.md) and
[4B-only auto configuration](examples/v0.5/adaptive.toml). Auto prefers direct
analysis and adds advisory roles only for a positive specialization case or a
required project review. Existing explicit workflow callers remain compatible.

A small local MCP offloading layer for Codex. Codex remains the primary agent;
Ollama models can handle repository discovery, context compression, summaries,
test-log analysis and first-pass review. Important decisions and final verification
stay with Codex.

LocalAgentBridge explores whether useful local analysis can reduce unnecessary
cloud context. It is not a Codex replacement, autonomous coding agent, guaranteed
cloud-usage reduction, or security boundary for untrusted code. Local output still
requires verification. No cloud LLM API, model shell access, embeddings or vector
store is included.

## How it fits

```text
Codex → stdio MCP → LocalAgentBridge → role/cap/quality gates → local Ollama
                         │
                         └─ metadata ──→ SQLite ← separate usage collector
                                           │        ↑ local Codex telemetry
                                           └─ Windows tray / dashboard
```

See [architecture](docs/ARCHITECTURE.md), [delegation policy](CODEX_POLICY.md),
[dashboard guide](docs/DASHBOARD.md) and [reference benchmarks](docs/benchmarks/README.md).
Upgrade notes are in [MIGRATION-v0.4.1.md](MIGRATION-v0.4.1.md); installation and
test evidence is in [VERIFICATION-v0.4.1.md](VERIFICATION-v0.4.1.md).

## Windows setup

Requirements: Windows, Git, Python 3.11+ with Tcl/Tk and pip, Ollama,
and local Codex. GPU acceleration is optional. Model fit depends on
weights, context length, GPU/RAM and other applications; measure before enabling
heavy escalation. Model downloads need internet, but inference and telemetry stay local.

Install [Git for Windows](https://git-scm.com/downloads/win),
[Python for Windows](https://www.python.org/downloads/windows/) (include pip,
the Python launcher and Tcl/Tk), [Ollama](https://ollama.com/download/windows),
and [Codex](https://learn.chatgpt.com/docs/quickstart). Complete Codex sign-in.
Start Ollama and confirm `ollama --version` and `ollama list` work in PowerShell.
Then install the public starter:

```powershell
git clone --branch v0.4.1 https://github.com/nishdel/LocalAgentBridge.git
cd LocalAgentBridge
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[tray]" -c requirements.lock.txt
Copy-Item config.example.toml config.toml
ollama pull qwen3:4b
.\.venv\Scripts\python.exe -m localagentbridge doctor
```

For development, install `.[tray,dev,benchmark]` with the same constraints.
Activate the venv if you prefer the
short `localagentbridge doctor` command. No PowerShell activation is required above.

`config.toml` in the current directory is selected automatically. Elsewhere, pass
`--config <config-path>` before the command or set `LAB_CONFIG`. Relative paths in
a config are resolved against that file. Set `source_root` to the repository that
Codex is authorized to analyze. `data_dir` contains a fresh SQLite database and
metadata log; neither is distributed. Keep personal config/history out of Git.

The default example uses **one Qwen3 4B model**, about 2.33 GiB of weights. It makes
no large-model downloads or automatic promotions. Optional [Balanced and Quality
profiles](docs/PROFILES.md) add stronger models only when deliberately selected.
Fixed consensus requires distinct models, so it is unavailable in the starter.
To substitute models,
edit config only: tag, roles, display name, architecture, total/active parameters,
quantization, weight size, minimum tier, enabled flag and capability strength.
Models are never silently substituted or automatically downloaded by MCP tools.

## Start the MCP server and dashboard

Codex launches the stdio server when registered. For a manual foreground server:

```powershell
.\.venv\Scripts\python.exe -m localagentbridge --config config.toml server
```

It waits for MCP messages on stdin; it is not an interactive chat prompt.
Run the native tray monitor separately (one collector per data directory):

```powershell
.\.venv\Scripts\python.exe -m localagentbridge --config config.toml dashboard
```

For a hidden terminal-free launcher from the checkout:

```powershell
$labPython = (Resolve-Path .\.venv\Scripts\pythonw.exe).Path
$labConfig = (Resolve-Path .\config.toml).Path
Start-Process -WindowStyle Hidden -FilePath $labPython -ArgumentList ('-m localagentbridge --config "{0}" dashboard' -f $labConfig)
```

The tray menu opens the widget, changes the compute cap, or quits. Settings include
start in tray, keep open, always on top, optional activity/escalation/failure popups,
and auto-hide delay. Defaults avoid intrusive popups. `widget` remains an alias.
For collection without a GUI, run `collector`; `collector --once` performs one scan.

## Connect Codex

Generate the exact TOML for this installation:

```powershell
.\.venv\Scripts\python.exe -m localagentbridge --config config.toml codex-config
```

Merge that output into the local Codex user config (normally `$HOME/.codex/config.toml`).
Do not create a duplicate `mcp_servers.localagentbridge` table. It contains the
absolute interpreter/config paths from *your* installation and a sufficient tool
timeout for bounded escalation/consensus. The helper does not edit Codex settings.
Restart Codex to load the tools. `codex mcp list` checks registration; `/mcp` in the
CLI shows active servers. A running desktop task may need a new session before its
tool catalog changes. Cloud-hosted Codex cannot directly launch this PC's process.

Alternatively, register through the CLI, then set the generated timeout in its config:

```powershell
$labPython = (Resolve-Path .\.venv\Scripts\python.exe).Path
$labConfig = (Resolve-Path .\config.toml).Path
codex mcp add localagentbridge -- $labPython -m localagentbridge --config $labConfig server
```

See [official MCP configuration](https://learn.chatgpt.com/docs/extend/mcp?surface=cli).
`doctor` reports configuration/installation issues; it does not prove that a Codex
turn has invoked a tool. The project policy is an opt-in instruction, not enforcement
inside Codex. Copy the relevant guidance from [CODEX_POLICY.md](CODEX_POLICY.md).

## Verify real local calls

```powershell
.\.venv\Scripts\python.exe -m localagentbridge verify-models
.\.venv\Scripts\python.exe -m localagentbridge smoke --all
.\.venv\Scripts\python.exe -m localagentbridge stats
Get-Content .\data\bridge.log -Tail 20
ollama ps
```

`verify-models` calls each exact role default, subject to the cap. `smoke` is a real
independent stdio MCP client exercising the seven handlers and optional consensus.
A routed handoff is valid protocol output: inspect `_routing.attempts` to distinguish
local inference from a gate returning work to Codex. Neither command certifies
answer correctness. Heavier registered models are tested with the opt-in paired
benchmark, not silently included in ordinary smoke runs.
With a profile containing two distinct consensus role defaults, add `--consensus`.
For the Balanced example use `consensus_roles = ["general", "coding"]`; the Quality
example already uses GPT-OSS and Qwen3 14B as its distinct participants.

To verify **Codex itself** is using Ollama, ask it explicitly to invoke a bridge tool,
look for the actual MCP invocation, then match the returned request ID/model with a
new local log/SQLite record. Successful records include Ollama's final prompt/output
counters and timing. Merely seeing a model loaded in `ollama ps` or a summary in
Codex's prose is insufficient evidence. Live output counts/speed are estimates;
completed Ollama counters replace them.

## Seven tool examples

These are MCP argument objects, not PowerShell commands. Outputs are compact JSON
text, capped at 3,000 UTF-8 bytes by default. Input is at most 10,000 characters,
generation 600 tokens, context 8,192 tokens. Source files are explicitly confined to
`source_root`. Discovery scans bounded file/byte/time limits and returns grounded
paths/symbols/line evidence; `use_model:false` returns lexical evidence without inference.

| Tool | Example arguments |
|---|---|
| `find_relevant_context` | `{"task":"Find the Ollama streaming HTTP request","scope":"localagentbridge","use_model":false}` |
| `summarize_context` | `{"task":"Summarize routing defaults and uncertainties","file_paths":["localagentbridge/routing.py"]}` |
| `analyze_code` | `{"task":"Identify the empty-input failure","text":"def average(xs): return sum(xs) / len(xs)"}` |
| `analyze_test_output` | `{"output":"FAILED test_add: add(2,2) returned 4, expected 5. Contract: ordinary addition."}` |
| `review_diff` | `{"task":"Preserve addition","diff":"@@ -1,2 +1,2 @@\n def add(a,b):\n-    return a+b\n+    return a-b"}` |
| `triage_task` | `{"task":"Add boundary tests for three pure helpers","context_chars":2000,"file_count":3,"risk":"low","complexity":"simple"}` |
| `second_opinion` | `{"question":"Is returning None for empty input safe?","context":"Callers expect a float and add 1 to the result."}` |

Six analysis tools accept optional `routing` hints: `complexity`, `stronger`,
`previous_request_id`, a supported failure `reason`, and `auto_escalate`. Use explicit
feedback via `triage_task` to report accepted/corrected/rejected results. Feedback
is not inferred from confidence. See the live MCP schema for exact enum values.

## Local Compute tiers and measurements

The starter registers **Qwen3 4B only**, even if you raise its compute cap. The
following selection rules apply after opting into the [Quality profile](docs/PROFILES.md):

| Tier | Eligible models | Selection for local work |
|---|---|---|
| Light | Qwen3 4B | Bounded discovery and summaries; substantive work returns to Codex |
| Medium | 4B, Qwen3 14B | Tiny context work uses 4B; substantive work uses 14B |
| Large | 4B, 14B, GPT-OSS 20B | GPT-OSS preferred for substantive work; 4B for tiny context work |
| Maximum | 4B, 14B, GPT-OSS 20B | GPT-OSS preferred; the tiny-summary threshold drops from 1,200 to 256 characters |

Large is the Quality profile default. Maximum uses the same optional models;
it changes selection thresholds. Role, memory, quality and compute-cap gates
still apply. Codex retains implementation, architecture, security and
final-verification responsibility in every tier.

Allow about 2.33 GiB of weight storage for the starter, 10.97 GiB for Balanced,
or 23.81 GiB for Quality. These are storage sizes, **not total runtime RAM/VRAM**.
The example allocation budgets are 6, 12 and 16 GiB respectively, including a
2 GiB reserve per selected model. Context/cache and other applications need
additional headroom. Quality is tight on a 16 GiB system; 6 GiB VRAM does not
hold either larger model fully, and CPU offload can be slow. Check the
[resource guidance](docs/PROFILES.md) before enabling Large/Maximum.

The dashboard lists actual eligible names below Light / Medium / Large / Maximum.
The Models tab explains installed, registered, enabled, cap/resource eligibility
and per-tool quality exclusions separately. Optional quality preferences select a
configured stronger worker for substantive tasks; Maximum lowers the threshold
for stronger summarization while preserving tiny operations on the light model.
Configurations without these preferences retain smallest-first routing. Heavy/experimental profiles
remain blocked unless explicitly enabled and within the current cap/resources.

**Local compression** compares supplied context bytes with returned bytes. Input
excludes the objective, instructions and JSON schema overhead. Final logical
payloads are counted once; legacy/fixed/consensus participant outputs are
shown separately. Negative compression means expansion. Potential avoided context
is `max(0, input - returned)` bytes: **not measured Codex token savings**. This project
has no controlled with/without-delegation experiment proving a cloud token reduction.
Actual token counters measure model usage, not bytes saved. A local call is not
proof that a cloud call was avoided. Handoff envelopes also consume context; a
short handoff or incorrect answer does not establish useful savings. Codex tool
definitions and orchestration overhead are not included in this byte comparison.

## Codex usage collection

The independent collector accepts local OTLP/HTTP completion **log events** (JSON
or protobuf), then uses incremental local rollout telemetry as a fallback. It does
not accept `/v1/metrics` or scrape the Codex graphical UI. It stores allowlisted
counters, timestamps/model and local correlation IDs; prompt bodies and source are
discarded. Optional user-level Codex config, merged into any existing `[otel]` table:

```toml
[otel]
environment = "local"
log_user_prompt = false
exporter = { otlp-http = { endpoint = "http://127.0.0.1:4318/v1/logs", protocol = "binary" } }
```

Start the widget/collector and restart Codex. Set `monitor.otel_port=0` to disable
this listener; fallback rollout collection remains available. No external telemetry
service is used by LocalAgentBridge. Codex's own product settings are separate.
See [official telemetry guidance](https://learn.chatgpt.com/docs/config-file/config-advanced#observability-and-telemetry).

Codex totals mean recorded input plus output, including repeated context on later
requests. Cached input is part of input; reasoning is part of output. Rollout
cumulative totals are differenced, and overlapping OTel/rollout streams are
reconciled per session/model rather than added twice. Missing counters stay unavailable.
Observed Codex activity time is not GPU inference time. Collection begins with
today's rollouts; `collector --backfill` includes retained older files explicitly.

## Troubleshooting

| Symptom | Check / remedy |
|---|---|
| `py` or Tcl/Tk unavailable | Repair the Python installation with the launcher, pip and Tcl/Tk enabled; reopen PowerShell. Use that Python to recreate the venv. |
| Ollama endpoint unavailable | Start the Ollama app (or `ollama serve` in a separate terminal). Check `ollama list` and the loopback endpoint in config. Do not start a second server on the same port. |
| Model missing | Run the exact `ollama pull` command printed by `doctor`. The starter requires only `qwen3:4b`. |
| Codex has no bridge tools | Run `codex-config`, check the interpreter/config paths, merge the single MCP table, and restart Codex. Check `codex mcp list` and rerun `doctor`. |
| Registration warning during first setup | Expected until the MCP table is added; afterward `doctor` should report the matching registration. |
| Timeout or out of memory | Lower the cap, shorten the input/context, or return work to Codex. Optional models need more RAM; never assume weight size alone establishes fit. |
| Cap differs from the config default | The dashboard's saved cap takes precedence. Select the desired tier there after switching profiles. |
| Port 4318 in use / duplicate telemetry | Run one dashboard or collector per data directory. Quit the extra instance or set `monitor.otel_port=0`; stdio MCP does not need this port. |
| Output is wrong, malformed or hands off | Inspect routing attempts, verify the evidence and let Codex finish. Valid JSON does not establish correctness; no stronger eligible model means handoff. |

Current limitations include confident factual errors, invented filenames,
missed requirements, incomplete snippets, and hardware-dependent latency.
Delegated output needs supervision even when confidence is high or models agree.
Report ordinary bugs and feature requests through
[GitHub Issues](https://github.com/nishdel/LocalAgentBridge/issues).
Use [private vulnerability reporting](https://github.com/nishdel/LocalAgentBridge/security/advisories/new)
for sensitive security issues; see [SECURITY.md](SECURITY.md).

## Development, privacy and release

[Contributing](CONTRIBUTING.md) includes tests and lint. [Security](SECURITY.md)
describes local-only operation and private reporting. [Release checklist](PUBLIC-RELEASE-CHECKLIST.md)
records the clean-install, privacy and license audit. Personal histories and raw
benchmarks stay in ignored local folders; anonymized reference aggregates belong
in `docs/benchmarks/`. Public benchmark fixtures contain only this project's own
historical source and synthetic test exercises.

The project uses the MIT license. Ollama and downloaded models have separate
licenses; users must check the licenses for the exact models they install.
No model weights or dependency binaries are included. See [dependency review](docs/DEPENDENCIES.md).
See the [v0.4.1 release](https://github.com/nishdel/LocalAgentBridge/releases/tag/v0.4.1).
