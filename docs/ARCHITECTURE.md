# Architecture

```mermaid
flowchart TD
  C[Codex: orchestration and final decisions] -->|stdio MCP| S[Seven bounded analysis tools]
  S --> D[Confined lexical repository discovery]
  S --> R[Explicit roles, compute cap, quality and resource gates]
  R -->|loopback HTTP, bounded JSON| O[Local Ollama models]
  S -->|metadata only| U[Usage store]
  C -->|local OTLP logs / incremental rollout fallback| T[Separate usage collector]
  T --> U
  U --> Q[(Local SQLite)]
  Q --> W[Native Tk / system tray widget]
```

`server.py` declares MCP schemas; `service.py` prepares bounded content and evidence.
`context.py` performs lexical discovery without embeddings. `adaptive.py` chooses
the smallest eligible capability strength; `models.py` provides shared gates used
by the dashboard. A compute cap is a ceiling, never a command to run the largest
model. Missing models produce explicit installation advice, never substitutions.

At most two attempts by default, with a configurable maximum of three. Stronger
attempts receive the original bounded evidence, not the prior model's answer.
Complex work, risk/ambiguity triage, exhausted attempts, confidence/format failures,
capability, memory and reviewed-quality limits can return work to Codex. A handoff
is a recommendation, not an automatically executed cloud request.

`bridge.py` serializes calls within each server instance and streams Ollama output.
Different MCP instances are not globally serialized; avoid concurrent heavy runs
on constrained hardware. It never executes generated code or model tool calls.
Fixed consensus is two or three configured roles, with Codex resolving disagreement.

`telemetry.py` writes allowlisted metadata to SQLite, including logical task IDs,
intermediate attempts and final returned payload sizes. These are distinct accounting
units. `collector.py`, `otel.py` and `codex_usage.py` run independently of MCP.
`dashboard_state.py` derives readable model states; `dashboard.py` uses native tabs.
Hardware performance sampling remains opt-in; companion workers also record their own process identity.

Older single-model configs and v0.1 tool arguments remain supported. SQLite
migrations only add tables/columns; a new checkout creates an empty local database.

## Opt-in v0.5 workflow layer

```mermaid
flowchart TD
  T[Typed task and evidence] --> P[Validated workflow and project profile]
  P --> S[Next sequential role stage]
  S --> K[Approved declarative skills]
  K --> R[Existing adaptive router and compute/resource gates]
  R --> B[Existing Bridge and bounded Ollama transport]
  B --> E[Validated advisory results and usage]
  E --> H[Hash-checked handoff to a declared next stage]
  E --> C[Explicit Codex implementation or decision checkpoint]
  C -->|supplied revised evidence, remaining budget| S
  S --> L[(Shared workflow ledger in usage.sqlite3)]
  B --> L
  C --> L
```

`catalog.py` validates data-only TOML skills, semantic roles, sequential workflows
and project profiles. These semantic roles are distinct from the legacy
general/coding/reasoning model bindings. Profiles can narrow requirements and
budgets, replace/remove local stages, and explicitly constrain model candidates.
They cannot remove Codex checkpoints or bypass the router's gates.

`workflow.py` advances one role or checkpoint per caller request. It supplies
bounded evidence to existing analysis adapters, adds an implementation-plan
schema, and prevents local output from performing actions. Every workflow ends
with a caller-recorded Codex decision. An implementation checkpoint accepts actual
diff/test evidence supplied after Codex performs the work. No model edits files,
runs tests, invokes tools, creates agents, or dispatches cloud work.

`workflow_store.py` adds a durable ledger to the existing metadata database.
Generations reserve shared attempts, corrections, context/output allowances and
active execution time. Stable task IDs, version checks, evidence/configuration
digests and a per-data-directory workflow lease prevent silent replay or overlap.
Raw task text, prompts, model results and checkpoint notes are not persisted by
the workflow ledger. Callers retain returned handoffs and re-supply them after a
restart. Routing metadata stays visible to Codex but is excluded from subsequent
model prompts. Revision invalidates prior result references without refunding
attempts or time.

The lease covers workflow execution sharing one data directory; legacy calls
remain serialized only within each Bridge instance. This is cooperative local
orchestration, not an OS resource governor or authentication boundary. Native
usage cards continue to show existing generation telemetry; workflow status is
available through MCP and CLI. See [WORKFLOWS.md](WORKFLOWS.md) for contracts,
accounting semantics and limitations.

## Durable companion path (candidate)

`companion_cli` and `dock` use `CompanionStore` as the local-user controller
interface. No HTTP control server is exposed. `companion.py` owns scheduling;
the dock owns no worker lifecycle. A controller lifetime kernel lock prevents
competing schedulers in one state directory, and a worker lock serializes model
calls. Detached workers use the controller runtime directory, not source_root.

Submission checks worktree HEAD, source_root, inventory and exact model selection;
SQLite persists the input excerpt, digest/options and task key. Workers revalidate
HEAD and model digest. Exact jobs invoke Bridge; routed jobs preserve the full
configuration through Service. `companion_workflows.py` invokes one existing
WorkflowEngine step/checkpoint per job, preserving versions, budgets and bounded
handoffs across process restarts. For companion jobs, exact private packets and
operation receipts commit with the corresponding workflow ledger transitions.
The companion then copies each receipt, result and unique completion event in
one transaction and acknowledges it afterward. Startup replays this database
copy idempotently, not the work. Acquiring the old worker lock permits retaining
partial evidence and marking unfinished attempts interrupted, never resuming
tokens. See [recovery](RECOVERY.md) for authority, ordering and legacy cases.

`callbacks.py` validates repository identity and resumes a dedicated Codex CLI
session using its exact returned identifier. The outbox claims one callback per
session. A crash after claim is uncertain, requiring explicit reconciliation.
Recorded accepted/corrected/rejected/further_work decisions carry validation
notes. Only resolved jobs/reviews permit idempotent finalization; failures cannot
become completed. The current callback is report-only and cannot apply patches.
Local supervising review can be recorded with `decide --local` without dispatch.
Successful finalization also requires every attached workflow checkpoint resolved.

State flow: queued → running → succeeded/failed/cancelled/interrupted → pending
review → dispatching → awaiting_decision/retry/blocked/uncertain → reviewed →
validating → completed/blocked/cancelled. Queue pause only gates admission.

Data includes authorized task excerpts/results in companion storage and its
workflow recovery tables; ordinary telemetry stays metadata-only. See SECURITY.md for private storage
and cloud callback flow, and DECISIONS.md for compatibility decisions.
