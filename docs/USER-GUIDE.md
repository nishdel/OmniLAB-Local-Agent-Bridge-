# Companion user guide

The owner's refreshed **idle-only candidate kit** is separate from the active
installation. From the candidate checkout its established launch command is
`.\data\readiness-20261013\manual-kit\open-dock.ps1`; add `-CheckOnly` to validate
the pinned wheel/runtime/configuration and empty paused store without opening UI.
It has execution disabled and cannot verify running-job/cancellation behavior.
Use the [existing eleven-row ledger](release-testing/selective-execution-issue-draft.md)
for actual observations. Other users should use the [quickstart](QUICKSTART.md),
not assume this private kit exists on their machine.

The companion is a bounded coding/review assistant. You or supervising Codex
provide a selected excerpt; local models propose code, tests or explanations.
The supervisor integrates and validates. Legacy/advisory jobs have no
model-directed tools. The separately qualified
selective implementation lane permits only bounded tools inside its restricted
sandbox; see the [complete workflow](WORKFLOW.md). Neither path grants arbitrary
repository access or bypasses cloud quotas.

## Choose the model and store

First identify the configuration used by the intended controller. `--config`
takes precedence over `LAB_CONFIG`, then the current directory's `config.toml`;
relative paths resolve against that file. Reopening with another configuration
can show a different empty store, not lost work. Do not point a test/acceptance
instance at the active data directory or upgrade a controller while it owns jobs.

For a first advisory, select an already installed compatible completion model.
An installed tag is not a quality guarantee. Companion exact jobs use an explicit
job model before the saved selector and configured default; workflows retain their
own roles/allowlists. Selective contracts resolve the backend/model's own profile.
An unavailable Strata choice cannot be made runnable by selecting it.

| Model/provider label | Meaning |
|---|---|
| installed | Local inventory contains the tag/assets; not proof of loaded identity or fit |
| compatible | Required protocol/capability metadata matches; not acceptance |
| qualified / locally_validated | Evidence applies to that exact identity, settings and scoped task/tool use |
| enabled | Policy permits consideration; admission and execution still recheck |
| disabled / unreachable / unloaded / unverified | Read the specific reason; no silent model substitution |

Pause prevents new jobs; it does not suspend current generation. To stop safely,
pause, inspect active jobs/review events, and finish or explicitly cancel owned
work. Retain uncertain reservations until trusted reconciliation confirms a stop.
Only then shut down the owned controller if needed. Hiding/quitting the dock does
not stop jobs. Reopen with the same configuration and store; never delete a database
to clear a blocked state. The separate idle-only acceptance kit opens no controller.

## Read results before accepting

The dock shows the selected run/task, exact model, local input/output tokens,
total elapsed time, queued and locally finished counts. `unavailable` means no
provider report, not zero. Counts are not percent-complete estimates. Details
show each job, digest, queue wait, local execution, review duration, reported
Codex usage, result, error and review event. Local execution time includes bridge
work; provider usage has the actual inference duration. Repeated review attempts
remain in the deliveries table; displayed review timing is the latest attempt.

Local tokens are provider counters, not cloud tokens saved. Preflight counts,
configured context and output ceilings are admission quantities. CPU power,
cloud phases or cache metrics may be unavailable. The benchmark's full-session
accounting is separate from dock totals. Execution, verification, review and
integration are separate axes: `finished`, `passed`, `accepted` and `integrated`
are different milestones. An advisory's verification may legitimately be
`not_run`; its source-grounded independent review is still required.

`Refresh models` fetches the configured Ollama inventory and show metadata.
`Save default` changes future exact-model jobs only; submission and execution both
revalidate selection. CLI `submit --model TAG` explicitly selects exact execution.
Configured roles otherwise retain routed execution. Workflow jobs retain their
profiles, compute controls and model allowlists; the selector never rewrites them.
The details document capability status, size and quantization through the
`companion inventory` JSON; the compact selector displays exact names. Models remain `untested` until a successful contribution is explicitly reviewed
as accepted/corrected with validation evidence. `locally_validated` is scoped to
the exact server, model digest and reviewed tools; it never means generally
validated coding quality. A changed digest returns to `untested`.

`Cancel current job` cancels the bridge HTTP request. The shared Ollama server
may still generate; no unrelated process is stopped or model unloaded. `Cancel
run` also cancels queued jobs and retains their review events. `Pause / resume
queue` only controls new jobs, never suspends an active generation. `Pin` keeps
the dock on top; `Details` expands it. `Evidence` opens the private state folder.
Closing or hiding the dock leaves the controller and worker independent. Reopen
it through its tray icon or `companion dock` after quitting the dock.

| State | Meaning and next action |
|---|---|
| local_queued / local_generation | Authorized local work is waiting/running |
| waiting_for_codex | Local result persisted; callback not yet claimed |
| reviewing | A serialized report-only Codex turn is active |
| blocked | Availability, uncertain delivery, rejection or validation needs attention |
| validating | Review decision recorded; supervisor must finish validation |
| completed | Every local job succeeded, all reviews accepted/corrected, explicit validation passed |
| cancelling / cancelled | Cancellation requested / reviewed cancellation finalized |

An uninitialized review session leaves results waiting. Authentication/quota/
network failures retain results. A worker crash marks generation interrupted on
recovery, never completed. Submit a new task key after inspecting interrupted
work; there is no token-position resume. A blocked report can be finalized as
blocked after reviews, but unresolved callbacks cannot be finalized as success.

The existing `widget`/`dashboard` usage views and MCP/workflow commands remain
supported. They are usage-monitor views in the same Python/Tk frontend and do not
own the new queue. Their totals are separate from a companion run's accounting.

The [durable workflow guide](COMPANION-WORKFLOWS.md) describes submission, next
steps, checkpoints and local review without authenticated callbacks. Dock details
show workflow ID/profile/path/version, next stage and shared budget. Routed jobs
show the configured routing selection and pinned inventory; actual attempts and
models are in the saved result. Review events and workflow checkpoints are separate:
marking a local result accepted does not advance a waiting workflow checkpoint.
