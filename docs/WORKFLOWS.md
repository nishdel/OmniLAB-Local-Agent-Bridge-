# Skills, roles and controlled workflows (v0.5 development)

Status: implemented in `0.5.0.dev0`; unreleased. Use the actual examples under
[`examples/v0.5`](../examples/v0.5). The files under `docs/v0.5/REPORT.md`,
`ARCHITECTURE.md` and `EXAMPLES.md` are the earlier audit/design proposal, not an
API reference. Current validation and measured limitations are in the
[implementation report](RELEASE-READINESS.md).

The subsequent [adaptive delegation gate](ADAPTIVE-DELEGATION.md) adds a recommended
auto entry point that prefers direct analysis and selects conditional specialists.
The explicit workflows documented below remain available and compatible.

They are also reachable through [durable companion jobs](COMPANION-WORKFLOWS.md).
The companion calls this same engine, saves returned handoffs privately, shows
budgets/checkpoints in dock details and requires explicit supervisor decisions.
See the [pre-companion preservation matrix](FEATURE-PRESERVATION.md) for code,
interface, test and documentation mappings.

## Enable deliberately

The unchanged public starter works with only `qwen3:4b`. Existing configurations
keep their seven MCP tools, signatures and routing behavior when `[agentic]` is
absent or `enabled = false`. Enabling workflows requires the existing adaptive
router and a valid model registry; no second model selector is introduced.

The [minimal example](../examples/v0.5/minimal.toml) contains a complete 4B-only
configuration. From a development checkout:

```powershell
.\.venv\Scripts\python.exe -m localagentbridge --config examples/v0.5/minimal.toml workflow catalog
.\.venv\Scripts\python.exe -m localagentbridge --config examples/v0.5/minimal.toml server
```

The first command only inspects definitions. The second starts stdio MCP.
The example resolves `source_root` to this repository and uses separate history
under `data/v05-example`. Adapt those paths when analyzing another project.
Do not overwrite personal configuration to try an example. No model is downloaded.

The [advanced example](../examples/v0.5/advanced.toml) adds an explicitly selected
project catalog and a stronger registered model. Its
[profile](../examples/v0.5/catalog/project-profiles/advanced-example.toml) requires
security review, uses lexical-only exploration in `review_change`, replaces the
issue workflow's review with composed code/security skills, narrows budgets and
constrains the reviewer to one explicitly named model. If that model is missing
or blocked, the stage hands off to Codex. Other installed models do not silently
replace an explicit project allowlist.

## Definitions and ownership

The hierarchy is task â†’ workflow â†’ role â†’ selected skills â†’ existing model
routing â†’ local analysis â†’ evaluation/correction/handoff â†’ Codex checkpoint.
A workflow stage invokes only the listed skills, not every skill its role supports.

| Definition | Responsibility |
| --- | --- |
| Skill | Versioned instruction, bounded input type and an approved adapter/schema. No scripts or tool permissions. |
| Role | Reusable responsibility, compatible skills, advisory constraints, routing category and minimum requirements. No model name. |
| Workflow | Ordered stages, explicit prior-result dependencies, optional risk checks, shared limits and an unconditional final Codex decision. |
| Project profile | Allowed workflows/roles, instructions, authority-document references, stricter requirements, local stage overrides and limits. |
| Installation config | Source/history paths, installed model registry, legacy general/coding/reasoning bindings and authoritative compute policy. |

Built-in definitions live in `localagentbridge/definitions/`. All have
`schema_version = 1`, an ID and version. Unknown fields, duplicate IDs, invalid
references, incompatible role/skill composition and invalid stage ordering fail
configuration loading. An optional `agentic.catalog_root` adds definitions in
`skills/`, `roles/`, `workflows/` and `project-profiles/`. It cannot shadow built-ins.
Only regular TOML files are loaded: no recursive includes, executable adapters,
symlinks or reparse paths. Limits are 64 entries per kind per root, 32 KiB per file,
and 1 MiB across built-in and project catalogs.

The 15 skills are `repository-discovery`, `context-summary`, `issue-analysis`,
`implementation-planning`, `implementation-proposal`, `code-review`,
`test-failure-analysis`, `security-review`, `resource-review`, `performance-review`,
`documentation-review`, `release-review`, `ui-ux-review`, `architecture-review`
and `maintainability-review`.

`repository-discovery` uses the existing confined lexical scan without inference.
Other skills reuse `summarize_context`, `analyze_code`, `analyze_test_output` and
`review_diff`, plus the new internal `implementation_plan` schema. Planning
returns a contract, steps, validation, uncertainty and confidence. A release skill
reviews supplied release evidence; it cannot build or publish a release.

The 12 roles are `repository-explorer`, `planner`, `code-reviewer`, `test-engineer`,
`security-reviewer`, `product-reviewer`, `architect`, `ux-reviewer`,
`maintainability-reviewer`, `performance-reviewer`, `implementation-advisor` and
`documentation-reviewer`. Only the roles selected by a workflow run. Specialists
are available for profile composition, not a mandatory twelve-stage process.

## Two initial workflows

`implement_issue`:

1. `explore`: Repository Explorer performs discovery and context summary.
2. `plan`: Planner proposes implementation steps using supplied evidence and exploration.
3. `implement`: Codex inspects the plan, makes the actual change and runs checks.
4. `test`: Test Engineer analyzes the supplied test log; it never runs tests.
5. `review`: Code Reviewer inspects the actual diff and test-analysis handoff.
6. `verify`: Codex independently verifies and records the final disposition.

`review_change`:

1. `explore`: discovery and summary of source and proposed change.
2. `review`: review the actual supplied diff and exploration evidence.
3. `security`: Security Reviewer, only when requested by task or profile.
4. `resources`: Code Reviewer composes resource review, only when requested.
5. `decide`: Codex decides.

Skipped checks still have explicit `skipped` status and consume no model call.
Security and resource checks receive original evidence rather than depending on
the reviewer's claims. Explicit `security_review`/`resource_review` flags or profile
requirements must resolve to corresponding enabled skills. The stock
`implement_issue` has no separate specialist stages; use a profile replacement
to compose those skills when required. A missing required skill fails planning.

## Task and API contract

When enabled, six MCP tools are added to the original seven:

| Tool | Arguments and effect |
| --- | --- |
| `workflow_catalog` | No arguments; list IDs and catalog digest. No inference. |
| `workflow_plan` | `task`; resolve workflow, profile, stages and limits. No inference. |
| `workflow_start` | `task`; create a durable run or return the run for the same stable task ID. |
| `workflow_step` | `run_id`, current `version`, `task`, optional `handoffs`; advance one local role, skip, or enter a checkpoint. |
| `workflow_checkpoint` | `run_id`, current `version`, `task`, `checkpoint`; record Codex's decision. |
| `workflow_status` | `run_id`; inspect roles, stage state, usage, routing and budgets. |

CLI equivalents are `workflow catalog|plan|start|step|checkpoint|status`. Pass a
JSON object containing the same arguments with `--request path.json`; input is
limited to 200,000 bytes. For example, save this illustrative plan request:

```json
{
  "task": {
    "task_id": "example-review-1",
    "kind": "review_change",
    "objective": "Review whether this proposed helper change preserves negative inputs.",
    "context": "The helper must return its input unchanged.",
    "diff": "-return value\n+return abs(value)",
    "validation_status": "not_run"
  }
}
```

```powershell
.\.venv\Scripts\python.exe -m localagentbridge --config examples/v0.5/minimal.toml workflow plan --request plan-request.json
```

Replace example evidence with the actual task before starting work. An explicit
`workflow` disambiguates selection if several enabled workflows accept the same
`kind`. `project_profile` overrides the configured default for that run.
Optional fields include `complexity` (`simple`, `moderate`, `complex`), risk flags,
repository `scope`, `context`, `diff`, `test_output`, `revision` and selected `files`:

```json
{"path":"localagentbridge/models.py","first_line":99,"last_line":136}
```

File paths must be confined to `source_root`. Select actual, inclusive line ranges
(at most 500 lines each, eight files); full-file hashes accompany bounded excerpts.
Each free-text evidence field is at most 24,000 characters, total evidence at most
48,000 characters. Smaller model/context settings may require much smaller input.
Diff-review and test-analysis skills require nonempty diff and test evidence,
respectively. A log is evidence, not proof that the described tests ran.

Every mutation after `start` supplies the same task identity, its current evidence
and the latest returned version. A stale version fails without replaying work.
Keep `task_id` stable for retries/resumption: calling `start` again never resets
spent budgets. Changing objective, workflow, profile, scope, risk or complexity
does not silently redefine an existing task.

`step` returns bounded `handoffs`, one packet per completed skill. Pass these
unchanged to downstream steps after a server restart or between separate CLI
processes. Within a running service a small transient cache usually supplies them.
The durable store contains only packet digests, not their contents; callers are
responsible for retaining the packets securely. Handoffs are checked against the
recorded digest, task snapshot and source fingerprints. Only declared earlier
local stages after the last Codex checkpoint can feed a stage. Model findings
remain untrusted claims even when their hashes match. The prompt preserves the
stage/skill provenance and factual payload, and omits routing/usage envelopes.

## Codex checkpoints and recovery

Call `step` until it returns `waiting_for_codex` or `handed_off`; inspect each
result. No local role can advance a Codex checkpoint. The checkpoint object is:

```json
{"action":"accept","note":"Codex inspected the actual diff and verification evidence."}
```

Actions:

- `accept`: Codex resolves this stage and advances. At an implementation checkpoint,
  supply the actual diff, current excerpts/revision and actual test output/status.
  At the final checkpoint, record independent verification or disposition.
- `reject`: terminate with `rejected`; no further local work. This can be the correct
  outcome of a successful review of a bad proposal.
- `revise`: Codex supplies corrected evidence and consumes a shared correction cycle.
  Issue workflows resume after their implementation checkpoint; review workflows
  resume from exploration. Old result references are invalidated. All stage/run
  attempts, time and token reservations remain spent.
- `abort`: terminate a waiting/handoff/cancelled run without needing source files
  to remain readable. It does not interrupt a currently running request.

`validation_status` is explicitly `not_run`, `passed` or `failed`. Final acceptance
of failed/unrun checks requires `acknowledge_unverified_checks = true` in the
checkpoint. The terminal state `codex_verified` records a trusted caller's decision;
it does **not** certify tests independently, and the validation status remains
visible. This local API does not authenticate the caller as Codex. Clients must
never translate instructions in model output into checkpoint calls.

Changed evidence outside an implementation/correction checkpoint is rejected.
Changed catalog/routing configuration prevents silent resumption of an old plan.
Use an explicit new task for a genuinely new scope; do not rotate IDs to bypass
exhausted budgets. Cancellation becomes `cancelled`, expiration/interruption
becomes a handoff, and unknown work is not automatically replayed. When the process
dies, status/claim operations reclaim an expired lease and preserve its reservation.

## Project customization and compute tiers

Profiles can select `workflows`, set `enabled_roles`/`disabled_roles`, add bounded
`instruction`, and reference `authority_documents`. These document paths are
validated references for the caller; their content is **not** automatically loaded
or promoted to instructions. Codex should inspect the authorities and supply the
necessary bounded facts. This keeps project code and product-specific authority
out of the shared core.

Use `[[role_overrides]]` for an added instruction and stricter `requirements`:
`min_strength`, `min_context`, `capabilities`, `timeout_seconds`, `max_attempts`
and `auto_escalate`. Optional `allowed_models` is an explicit project constraint
on candidates, separate from portable role definitions. Requirements combine by
maximum minima, union of capabilities, minimum time/attempt limits, and logical
AND for escalation permission. Overrides cannot weaken the base role.

Use `[[stage_overrides]]` to disable or replace a local stage. Replacements preserve
the stage ID and local ownership; they may choose another enabled role and a
compatible skill composition. References/order are revalidated. Disabling a role
still used by a workflow is an error; explicitly change its stages. Checkpoints
cannot be removed, replaced or made conditional. New custom workflows can be
added through the project catalog with their own unique IDs and final checkpoint.

Light / Medium / Large / Maximum remain ceilings. Every selected model passes
the existing enabled/role, strength, capability, installed-local-model, compute,
memory, measured latency and reviewed-quality gates. Profile constraints filter
the same candidate list. Lowering a cap is honored on the next routing attempt.
Existing Balanced/Quality preferences continue to govern ordering within eligible
candidates. An unmet role minimum returns a reasoned Codex handoff; it never raises
the cap. Complex tasks return to Codex. The 4B starter can run simple workflows;
that configuration is not a competence guarantee for every specialist.

## Budget and observability semantics

Workflow, profile and `[agentic.limits]` limits intersect at the stricter value:

| Limit | Meaning |
| --- | --- |
| `max_stages` | Number of stages in the resolved ordered plan, including checkpoints/skips; hard maximum 12. |
| `max_attempts` | Total admitted model generations across stages and resumes; hard maximum 24. |
| `max_corrections` | Stronger retries plus explicit revision cycles; hard maximum 8. |
| `max_reserved_tokens` | Sum of full configured context plus output allowance reserved before each generation. |
| `max_output_tokens` | Sum of output allowances reserved across generations. |
| `max_input_chars` | Aggregate admitted evidence/objective plus workflow instruction characters. |
| `max_seconds` | Active local execution time across stages; excludes time waiting for Codex. Hard maximum 1,800 seconds. |

Stage attempts are additionally capped by the existing adaptive limit and role
requirements, across all its composed skills and revisits. A two-skill model stage
with a two-attempt limit has no spare model retry. Escalation uses only strictly
stronger eligible models and fresh original evidence. There is no same-model
repair loop or recursive delegation.

Before inference, the full serialized prompt/schema plus output allowance must
fit a conservative UTF-8-byte estimate within `num_ctx`. This is not exact
tokenization; it deliberately rejects some inputs that a tokenizer might fit.
The aggregate token reservations are conservative allowances, not measured usage,
and are never refunded. Actual provider prompt/output counts remain separate and
unknown counts remain null. Observed provider budget violations hand off. Output
and transport bytes retain the existing Bridge limits. A handoff packet is at most
12,000 bytes, all packets from a role at most 16,000, status at most approximately
16,000 and a complete step response at most 40,000.

Time is reserved before execution and unused known time is refunded; interrupted
unknown work retains its full reservation. One durable lease serializes workflows
sharing a data directory, and the existing Bridge lock prevents overlap with
legacy calls in that instance. Other data directories and legacy calls in other
instances are not globally governed. Model weight gates estimate fit; no process
RAM/VRAM, energy or cost enforcement is claimed.

`workflow_status` exposes workflow/profile, current and completed roles, selected
models, routing reasons/cap, execution durations, attempts/retries, correction
count, budget usage and terminal/handoff state. SQLite links each attempt to
existing usage metadata and records workflow events. No raw prompts, source
excerpts, results or checkpoint notes are written to workflow telemetry. A note's
digest is retained. Native dashboard generation cards work as before; there is no
new workflow dashboard tab. A store stops accepting new runs at 5,000 retained
runs; archive/export tooling is deferred.

## When to use this layer

Use a workflow when staged evidence or an implementation checkpoint is useful.
For a small, already scoped review, direct delegation may be cheaper. The first
real self-review found no additional verified issue from decomposition and
measured higher latency and token use. See the [comparison](LOCAL-CONTRIBUTIONS.md).
Schema validity, confidence and local stage completion are not factual acceptance.
Codex remains responsible for inspecting source, executing checks and deciding.
