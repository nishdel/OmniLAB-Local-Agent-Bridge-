# Minimum sufficient delegation (0.5.0.dev0)

Adaptive selection adds a deterministic gate before the existing local execution
layer. It prefers direct analysis; a workflow needs an explainable reason or an
explicit project/user requirement. It makes no classifier model call. Decisions
are advisory estimates, and all implementation and final decisions remain with
Codex. The representative evaluation is recorded in
[the adaptive report](v0.5/ADAPTIVE-REPORT.md).

## Enable auto without changing existing callers

Use [`examples/v0.5/adaptive.toml`](../examples/v0.5/adaptive.toml). It uses only
Qwen3 4B, points to this repository, and stores history separately. Its
[project profile](../examples/v0.5/catalog/project-profiles/adaptive-example.toml)
explicitly sets `workflow_mode = "auto"` and requires conditional security and
resource reviews. Adapt its source/data paths for another project.

The existing MCP tools and CLI actions remain unchanged. A project explicitly
setting `workflow_mode`, `decomposition_threshold` or `required_reviews` enables
the gate, including for callers that omit the new task hints. A caller cannot
bypass explicit project requirements by omitting its `delegation` field.

With an existing profile that has no new controls, add `"delegation": {}` to the
task to opt into auto. Omitting it preserves the original explicit-workflow
behavior and all existing definitions/profiles. The seven legacy analysis tools
remain unchanged and do not participate in the workflow ledger or new profile
policy; clients requiring the policy must use this task entry point.

Example JSON for `workflow_plan` or `workflow_start`:

```json
{
  "task": {
    "task_id": "helper-review-1",
    "kind": "review_change",
    "objective": "Review whether the helper still accepts negative inputs.",
    "context": "Returning the supplied value unchanged is required.",
    "diff": "-return value\n+return abs(value)",
    "delegation": {}
  }
}
```

```powershell
.\.venv\Scripts\python.exe -m localagentbridge --config examples/v0.5/adaptive.toml workflow plan --request task.json
```

Replace illustrative evidence with the actual task before execution. Use `start`,
then `step` with the returned `run_id`/current `version` and the same task, then
record the actual Codex checkpoint decision. The existing evidence, handoff,
restart and shared-budget rules in [WORKFLOWS.md](WORKFLOWS.md) still apply.

Direct execution is one existing adapter call (or deterministic repository search)
with shared accounting and a Codex decision. It does not add semantic-role prompts
or an exploration pass. It still honors the associated operation's routing
requirements and explicit project instructions/overrides. Status labels the stage
`execution: "direct"`; its role reference supplies compatible requirements, not
an additional agent. A workflow can contain just one specialist and Codex.

## Inputs and deterministic indicators

Task `complexity` remains `simple`, `moderate` or `complex`. Optional fields under
`delegation` are:

| Field | Meaning/default |
| --- | --- |
| `mode` | `auto` by default; caller may request `direct` or `workflow` within project policy. |
| `expected_files`, `components` | Expected breadth, both default 1. Actual selected/diff paths can increase the file estimate. |
| `independent_concerns` | Number of distinct questions needing review; default 1. |
| `security_sensitive`, `dependency_change` | Explicit sensitivity/dependency evidence. |
| `architecture_impact`, `resource_sensitive`, `ui_change`, `release_scope` | Domains where a specialist might add useful information. |
| `ambiguous` | Scope/requirements need Codex clarification before local work. |
| `independent_review` | Independent source-based advice is expected to be useful. |
| `specialization_value` | Caller expectation: `unknown`, `useful` or `essential`; not a quality measurement. |

All flags default false. Existing task `security_review` and `resource_review`
requests are retained. Selected evidence and `+++` diff-header paths provide
bounded deterministic signals: common dependency manifests, dedicated
auth/security/secrets/permissions directories and common UI extensions. These
signals cannot execute anything. The gate never interprets model-generated
instructions as task policy and does not inspect the whole repository to classify
a task. Content-only or renamed files can evade these hints; supply known risks.

Path signals are conservative hints: a metadata-only `package.json` edit can
activate dependency review, while a Python-rendered UI change may need an explicit
UI flag. Names alone do not prove a vulnerability or a license problem. Only counts
and signal booleans are retained in decision metadata, not raw paths or task text.

## Explainable scoring and feasibility

The initial policy uses these small integer contributions:

| Indicator | Points |
| --- | ---: |
| Moderate / complex task | 1 / 2 |
| At least two components or four files | 1 |
| At least three components or eight files | 2 instead of 1 |
| Two / at least three independent concerns | 1 / 2 |
| Security/dependency sensitivity | 2 |
| Architecture impact | 2 |
| Resource sensitivity | 2 |
| UI or release scope | 1 |
| Explicit independent review | 2 |
| Applicable specialist or expected useful specialization | 1 |
| Expected essential specialization | 2 instead of 1 |

The default threshold is 3. Reaching it is insufficient without a positive
specialization case: relevant domain advice, independent review/concerns, or a
non-simple implementation issue. Task-kind names map to suitable adapters rather
than hardcoded direct/workflow verdicts. Broad search with no distinct review need
can therefore stay direct; a focused security review can select a single role.
The score is a routing heuristic, **not a universal quality score or a calibrated
probability of useful findings**.

The gate checks the resolved workflow/profile/global limits and existing router
candidate gates. It estimates first-pass model calls, conservative context/output
reservations, and measured latency when local history exists. Estimates exclude
retries; unknown time stays null. The existing executor performs exact input/output
admission and actual installed-model checks. Planning does not contact Ollama or
claim that a registered candidate is installed.

Optional auto decomposition falls back to direct if it cannot fit the cap/budget
and direct can. Required reviews and explicit forced-workflow policy are never
dropped to fit a budget. Inadequate plans return a visible Codex handoff before
inference. Complex or ambiguous work also returns to Codex for bounded scoping;
this gate does not bypass the existing complex-work safeguard by relabeling roles.
Moderate-role strength and all Light/Medium/Large/Maximum gates remain authoritative.

## Project control and conditional specialists

Example profile fragment:

```toml
workflow_mode = "auto"
decomposition_threshold = 3

[[required_reviews]]
role = "security-reviewer"
skill = "security-review"
when = "security"

[[required_reviews]]
role = "performance-reviewer"
skill = "resource-review"
when = "resources"
```

`workflow_mode = "direct"` forces the initial analysis down the direct path.
`workflow_mode = "workflow"` requires decomposition. A non-auto project mode
takes precedence over the caller's requested mode. Required reviews are appended
even after a direct initial analysis; direct → Security Reviewer → Codex is valid.
An already selected required role/skill pair is not duplicated. Existing
`require_security` and `require_resources` remain supported.

Required review conditions are `always`, `security`, `dependencies`, `resources`,
`architecture`, `ui` and `release`. Role/skill compatibility and enabled-role
policy are validated. An unavailable mandatory specialist remains an explicit
handoff, never a silent skip. Explicit workflow selection and project stage
overrides preserve the resolved workflow structure; the gate cannot prune a
project-authored checkpoint or local stage. A direct project mode conflicting
with an explicit workflow/stage override is rejected as a policy conflict.

Auto domain choices reuse existing definitions:

- Architecture → `architect` / `architecture-review`.
- Security or dependency risk → `security-reviewer` / `security-review`.
- Resource cost → `performance-reviewer` / `resource-review`.
- UI evidence → `ux-reviewer` / `ui-ux-review`.
- Release evidence → `documentation-reviewer` / `release-review`.

With several independent concerns, auto may retain the general analysis role
alongside domain advice. Single-concern auto review can use only its specialist.
Specialists receive original source/diff evidence, not previous model conclusions.
Forced decomposition uses exploration plus analysis, with existing declared
handoffs where appropriate; it is available for explicit comparisons and policy.
The original `implement_issue` workflow retains its implementation checkpoint and
post-change validation. Even direct issue analysis leaves actual implementation
with Codex and retains subsequent test/review stages.

Security is a conditional advisory review, not a persistent running agent.
Resource Efficiency is a conditional skill using the existing performance role,
plus shared execution budgets. No new permanent role or license-checking engine
was added. A project may supply dependency/license evidence in its instructions;
missing license evidence stays unknown.

If changed evidence at an implementation checkpoint now triggers a required
review absent from the persisted plan, acceptance is blocked. Codex must explicitly
scope a new task rather than silently adding unchecked work or skipping policy.
This conservative recovery costs an extra coordination step; dynamic replanning
is outside this foundation.

## Decision records and limitations

`workflow_plan` exposes a `delegation` object, and `start` stores it in the existing
metadata ledger. Status includes:

- Primary `path` (`direct` or `workflow`), effective mode and selected workflow.
- Weighted reasons, score/threshold and bounded indicators.
- Original compute tier, eligible direct candidates and blocked reasons.
- First-pass estimates, budget fit, runnable state and handoff blockers.
- Selected roles, required reviews and whether project policy mandated them.

When the primary path is direct but policy requires later roles, both facts are
shown. A repeated `start` returns the persisted decision; latency or cap changes
do not silently create a new plan or reset spend. Actual model routing still reads
the current cap at execution, so the decision's original tier and an attempt's
current tier can legitimately differ.

The gate does not learn a cost/quality tradeoff from a universal score. It uses
declared scope and simple signals, and can over-select specialists that repeat
already available findings. Different prompts on the same model are not independent
expertise. Required confidence is still established by Codex's verification.
Use the evaluation's factual counts and actual usage, not role count, model
confidence or schema validity, to judge whether decomposition earned its cost.
