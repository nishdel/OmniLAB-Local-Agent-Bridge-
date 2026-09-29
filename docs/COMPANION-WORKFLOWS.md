# v0.5 workflows in durable companion jobs

Use the existing skills, advisory roles, project profiles, workflow budgets and
adaptive direct/auto/workflow gate through the companion queue. The worker calls
the same `Service` and `WorkflowEngine` used by the existing CLI and MCP tools.
It does not plan a second workflow or remove existing policy controls.

## Choose the execution contract

| Interface | Selection and ownership |
|---|---|
| `companion submit` with configured roles | Existing role/adaptive routing, including preference, resource/quality caps and bounded retries; optional role/routing hints |
| `companion submit --execution exact` or `--model TAG` | One exact installed model. The saved dock default applies here. No workflow policy is claimed. |
| `companion workflow-submit` | Existing typed workflow task, project controls and shared ledger; queues one next step |
| `workflow ...` or workflow MCP tools | Original caller-driven engine interfaces, still supported independently |

`--model` and `--execution routed` conflict and are rejected. A changed dock
default never changes queued jobs, routed role bindings or project allowlists.
Routed jobs persist full configuration and the available registered model
digests. Every generation rechecks its exact name/digest. A missing registered
model does not gain eligibility by being installed after submission.

## Submit and advance a workflow

The [quality example](../examples/companion-quality.toml) enables GPT-OSS 20B,
Qwen3 14B fallback/reasoning, Qwen3 4B lightweight work and `[agentic]`.
Alternatively use the existing [4B-only adaptive example](../examples/v0.5/adaptive.toml).
Inspect and adapt source/data paths for the selected Git worktree. These files
do not change installed models or the personal routing configuration.

```powershell
python -m localagentbridge --config examples/companion-quality.toml companion inventory
python -m localagentbridge --config examples/companion-quality.toml companion create
python -m localagentbridge --config examples/companion-quality.toml companion workflow-submit --run RUN_ID --request examples/companion-workflow-task.json
python -m localagentbridge --config examples/companion-quality.toml companion start
python -m localagentbridge --config examples/companion-quality.toml companion status --run RUN_ID
python -m localagentbridge --config examples/companion-quality.toml companion workflow-status --job JOB_ID
```

Replace example evidence with the actual bounded task. The JSON envelope contains
`task_key` and `task`; the task uses the existing WorkflowTask schema. It accepts
`delegation: {"mode":"auto"}`, `direct` or `workflow`, and existing risk/profile
controls. Omit delegation to retain explicit workflow selection. Project-required
reviews remain mandatory even in direct mode. No classifier model is called.

Submission returns a job ID without inference. A worker executes one engine step
and commits its bounded result/handoffs plus a review event. Inspect the result.
When its workflow state is `ready`, submit the next step:

```powershell
python -m localagentbridge --config examples/companion-quality.toml companion workflow-next --job PREVIOUS_JOB_ID
```

The next job uses the same workflow ID, current version, pinned configuration,
policy identity and exact handoffs. It constructs a fresh engine; in-memory
cache is not required. Every role attempt still reserves the original shared
budgets before generation. Skipped stages and checkpoints may use zero model
tokens. Reservations are distinct from provider-reported usage.

At `waiting_for_codex` or `handed_off`, inspect the findings and actual source or
validation evidence. A trusted supervisor can submit `checkpoint.json`:

```json
{
  "checkpoint": {
    "action": "accept",
    "note": "Describe the actual inspection and validation performed.",
    "acknowledge_unverified_checks": true
  }
}
```

```powershell
python -m localagentbridge --config examples/companion-quality.toml companion workflow-checkpoint --job PREVIOUS_JOB_ID --request checkpoint.json
```

That example explicitly acknowledges unrun/failed checks; it does not certify
tests. Supply actual `validation_status="passed"` only after running them. For
implementation/correction, include a complete updated `task` with the actual
diff/test evidence; the adapter preserves its scoped task identity. Existing
`accept`, `reject`, `revise`, `abort`, evidence freshness, correction limits and
version checks still apply. A local answer can never create a checkpoint request.
Inspect the checkpoint job before using its returned job ID for another step.

## Review events, the dock and finalization

Workflow checkpoints and companion review events are separate records. A final
workflow checkpoint cannot erase a failed job or satisfy its review event.
The dock details show workflow ID, profile, selected path, next stage, version,
spent budget and each job's pending review. Pause/cancel act on the existing queue.
The dock has no implicit checkpoint acceptance or automatic workflow editor.

Supervising Codex/the user can record a review locally, without a cloud callback:

```powershell
python -m localagentbridge --config examples/companion-quality.toml companion decide --event EVENT_ID --outcome accepted --validation "Describe actual review evidence" --local
```

`--local` accepts pending/retry events and leaves an explicit local-review reason.
It cannot bypass an in-flight or uncertain external delivery; reconcile that
delivery first. `start` without `--codex-exe` only schedules local workers. No
authenticated session or callback is created by any command in this guide.

Successful `finalize --validation-passed` requires all jobs and reviews resolved,
accepted/corrected results, and every attached workflow at `codex_verified`.
An explicit failed-validation finalization can record a partial/blocked result.
Acknowledging unverified workflow checks does not itself prove validation passed.

## Qwen second opinions and fixed consensus

The quality example's `second_opinion` reasoning route is the exact
`qwen3:14b-q4_K_M` tag when adaptive routing is disabled; with adaptive routing,
single opinions follow the configured preference and gates, as before.
For an independently fixed Qwen opinion alongside GPT-OSS, use consensus:

```powershell
python -m localagentbridge --config examples/companion-quality.toml companion submit --execution routed --run RUN_ID --request examples/companion-consensus-task.json
```

The [request](../examples/companion-consensus-task.json) uses coding and reasoning
roles. `Service.second_opinion` checks both exact configured models before chat,
then calls GPT-OSS and Qwen sequentially with the same evidence; neither receives
the other's answer. Each model keeps its configured thinking mode. Missing models,
duplicate models, caps or digest changes produce an explicit failure/handoff,
never a substituted opinion. The supervisor decides disagreements.

For one exact independent Qwen opinion, use `tool="second_opinion"` with just the
four required task fields and `submit --model qwen3:14b-q4_K_M`. Omit consensus
options for this exact call. The saved Qwen profile supplies think=false.

## Recovery boundaries

The original workflow interface stores metadata and digests only. Companion
workflow jobs additionally persist private bounded packets and operation receipts
with the authoritative ledger transitions, then reconcile companion results and
review events. Keep both databases private. Catalog edits or changes to the Git
base block queued execution rather than silently replanning. Keep runtime and
catalog definitions fixed while owning jobs, and edit a separate worktree.

`workflow-status` reads the authoritative workflow ledger after a worker failure.
Startup or `companion recover` repairs downstream state from committed receipts;
it never repeats inference or checkpoint decisions. Partial saved output remains
interrupted, and output never saved cannot be reconstructed. Spent reservations
are not refunded. See [recovery](RECOVERY.md) for exact automatic and manual cases.
Old v0.5 metadata-only workflows are not
automatically imported into companion jobs: continue them with their original
workflow interface and retained handoffs. No original ledger or capability is
deleted. `no_inference_deadline` never disables the workflow time/attempt budgets.
