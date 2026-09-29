# Companion user guide

The companion is a bounded coding/review assistant. You or supervising Codex
provide a selected excerpt; local models propose code, tests or explanations.
The supervisor integrates and validates. The companion does not execute commands
invented by a local model, modify arbitrary repositories, or bypass cloud quotas.

The dock shows the selected run/task, exact model, local input/output tokens,
total elapsed time, queued and locally finished counts. `unavailable` means no
provider report, not zero. Counts are not percent-complete estimates. Details
show each job, digest, queue wait, local execution, review duration, reported
Codex usage, result, error and review event. Local execution time includes bridge
work; provider usage has the actual inference duration. Repeated review attempts
remain in the deliveries table; displayed review timing is the latest attempt.

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
