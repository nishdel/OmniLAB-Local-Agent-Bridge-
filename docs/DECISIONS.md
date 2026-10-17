# Companion architecture decisions

## ADR 1: retain Python and Tk

The candidate retains the existing Python controller, Bridge and telemetry,
SQLite persistence and Tk/pystray UI. There is no C#/C++ runtime dependency or
parallel abandoned prototype. Bridge overhead and Ollama inference are separate;
changing the caller language would not demonstrate faster model inference.

The companion dock is a new view in the same Tk frontend. Existing usage views
remain supported for v0.1/v0.2 configuration and registry users. Unreachable
registry controls inside the legacy view are removed because the view factory
routes those configurations to RegistryDashboard. An installer/visual design
rewrite is not justified by current measurements. Measurements and platform
limitations are reported in RELEASE-READINESS.md rather than inferred.

## ADR 2: durable jobs and conservative terminal review

Reuse the working terminal launcher pattern and documented `codex exec` /
`codex exec resume SESSION_ID`. Create a dedicated persistent session per run;
record the `thread.started.thread_id` accepted by that CLI. Never use `--last`,
an app task ID guessed from a directory, or the old ephemeral benchmark session.
Keep shell/plugins disabled, sandbox read-only, approvals never. This candidate
offers report-only callbacks; integration remains in the supervising session.

SQLite commits a result and its unique outbox event in one transaction. Local
workers are independent of the controller and dock. Kernel locks serialize
workers/controllers; transactions serialize review claims across runs sharing
a managed session in the same store. A claimed invocation after restart becomes
uncertain. Inspection/reconciliation precedes retry. Exactly-once external
delivery is not promised; finalization is one idempotent logical database update.

The public CLI is alpha in the tested installation. Error/reset metadata differs
across versions. Only recognized structured terminal failures trigger retries;
unknown/network reconnect logs stay uncertain. No app-server dependency was
introduced. External clients must not concurrently resume this dedicated session.

## ADR 3: compatibility and packaging

Retain the existing MCP tools, bounded workflows, configuration keys and usage
database migrations. Companion state is a separate schema-v1 database below
`data_dir/companion`; upgrading does not rewrite v0.4.1 usage history. Store
model/digest/options with each submitted job. Changing defaults cannot change
queued work. Preserve benchmark source and evidence; exclude research scripts
and evidence from the wheel. Portable synthetic lifecycle fixtures replace tests'
dependency on one user's benchmark directory.

`psutil` becomes a core dependency because durable workers record process identity;
the redundant benchmark extra is removed. Windows uses pywin32 already required
by the installed MCP stack; the project now declares that dependency explicitly.
Source/wheel installation is supported; a bundled EXE, auto-start service and
installer/uninstaller are not implemented.

## ADR 4: preserve the implemented v0.5 layer

Audit against the hashed pre-companion v0.5 source, not only public v0.4.1.
The existing catalog, workflow, delegation, routing and service implementations
remain authoritative. The original companion's single-model worker bypassed them;
`companion_workflows` now adapts their supported operations to durable jobs.
Do not restore dead duplicate implementations to retain filenames. See the
[matrix](FEATURE-PRESERVATION.md) for reachability evidence.

One workflow step per durable job retains explicit caller control and review
opportunities. Checkpoints require a trusted explicit submission; a model result
cannot advance them. Store bounded handoffs privately with companion results,
preserving the pre-existing digest ordering. Keep catalog and configuration
identity fixed and spend reservations in the existing ledger. The two SQLite
ledgers are not a distributed transaction. Companion-only packets and operation
receipts now commit with workflow transitions; downstream receipt delivery is
idempotent. Partial or never-saved output requires explicit intervention; never
silently replay an uncertain step. See [recovery](RECOVERY.md).

Exact single-model execution and configured routing are distinct explicit
contracts. Preserve Qwen3 14B fallback and independent fixed consensus even when
GPT-OSS is preferred. Local supervisory review is available without sending an
authenticated callback; it cannot conceal uncertain external delivery.

References checked during this implementation:
[Codex non-interactive mode](https://learn.chatgpt.com/docs/non-interactive-mode),
[Codex commands](https://learn.chatgpt.com/docs/developer-commands),
[Ollama inventory](https://docs.ollama.com/api/tags),
[Ollama metadata](https://docs.ollama.com/api-reference/show-model-details).
