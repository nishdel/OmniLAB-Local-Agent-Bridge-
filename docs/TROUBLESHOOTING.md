# Troubleshooting

| Symptom | What to inspect and do |
|---|---|
| Ollama unavailable or no models | Start your Ollama service; run `ollama list` and `companion inventory`. Select an installed completion model. The bridge never downloads or substitutes one. |
| Selected model removed/changed | Refresh inventory; a missing model or changed digest fails visibly. Select and submit new work after review. |
| Slow generation | Inspect local execution time and reported counters. For direct companion jobs, use `--no-deadline` or `no_inference_deadline = true`. Connection establishment stays bounded. No deadline does not mean execution through shutdown. |
| Five-hour or weekly quota exhausted | Inspect the callback event and Codex availability. Reported absolute reset metadata controls retry. A weekly limit may still block after five hours. No credits, saved resets, account switch, cloud-model switch or paid API fallback occurs automatically. |
| Authentication required | Authenticate with your installed Codex CLI, then inspect the failed delivery. Explicitly reconcile `not_delivered` only when evidence establishes it. Credentials are never copied into bridge records. |
| Network loss / unknown failure | Results remain durable. Structured terminal network errors schedule a retry; unstructured or interrupted delivery is `uncertain`, requiring inspection rather than automatic replay. |
| Busy managed session | Callbacks serialize by exact session ID and wait for the preceding review decision. Keep the dedicated session exclusive to this controller; another client is outside its lock domain. |
| UI disconnected / hidden | Reopen the tray dock; use `companion status`. UI lifetime does not govern execution. |
| Worker failure / shutdown | Restart the controller. A released kernel lock permits interrupted-worker reconciliation. Completed results survive. In-progress model generation restarts only as a new explicitly submitted job, not mid-token. |
| Cancellation still shows model activity | HTTP cancellation does not establish shared-server termination. This candidate does not kill or unload a shared runtime. The separate benchmark's owned Job Object cancellation is preserved. |
| Pending / uncertain review | Inspect `reviews/<run>/<delivery>/events.jsonl`, `response.txt` and `stderr.log` locally. Run `companion reconcile --event EVENT --disposition delivered|not_delivered --evidence "observed evidence"`. Delivered events become reviewable; confirmed non-delivery is queued again. Never guess. |
| Uncertain session initialization | Inspect `reviews/<run>/init/` and verify the old CLI turn is no longer active. A recorded session can be enabled with `companion reconcile-session --run RUN --evidence "observed evidence"`; do not create a duplicate session. If no session ID was returned, keep the run blocked and create a new run after resolving availability. |
| Finalization refused | Resolve every review, record integration/test evidence with `decide`, and finalize only when dependencies are resolved. |
| Missing Tcl/Tk | Install Python with Tcl/Tk. If `tkinter.Tcl()` works outside a restricted shell, record a sandbox-specific test limitation rather than changing the system install. |

The controller checks its local queue once per second; this is ordinary process
scheduling, not model-driven polling. A callback has a 120-second host watchdog.
Watchdog expiry terminates only its owned CLI process and marks delivery uncertain;
it does not reset the local inference deadline or erase outputs.

`companion shutdown` requests controller exit after the current callback finishes.
It does not cancel an independent worker. Pause new work and use the appropriate
cancel control separately when needed. Its recorded process/heartbeat helps
diagnosis; an old heartbeat is not proof of graceful process exit.

Keep raw diagnostics private. They can contain supplied repository excerpts,
model outputs and local paths. Share a redacted state summary, version and error
category, never a database or authentication directory.

## Qualified project workflow

- **Identity/backend/template mismatch:** compare the exact recorded digest,
  Ollama version and template hash in the qualification evidence. Restore the
  approved configuration or ask the supervisor for a new qualification. Do not
  substitute a model or redownload weights automatically.
- **Runner settings differ:** LAB withheld the tool call because actual
  context/offload/draft flags did not match. Check the private profile against
  the live runner evidence; do not weaken the check.
- **Resource admission/pressure stop:** preserve OS headroom and wait for
  unrelated work or an existing model residency to end. Inspect resources.jsonl
  and the durable reservation. Never raise ceilings to force a pass.
- **Cancellation pending:** a disconnected request does not prove provider
  termination. After independent verification that the owned work is stopped
  and the provider is idle, use contract-resource-release with the job ID and
  concrete evidence. Never clear another job's reservation.
- **Legacy transport cannot verify the profile:** use companion submit or
  contract-submit with the qualified project config. Old Bridge/workflow
  configurations remain available; they are not proof of this runtime profile.
- **Strata disabled:** no compatible runnable installation was found in the
  checked locations. The example port is not a live URL. Supply an actual
  installation path for separate verification; do not run an automatic large
  download or networking/driver setup.
- **Token totals unavailable:** inspect per-request coverage and the accounting
  cutoff. Missing and cancelled-response counters are unknown. Cached/reasoning
  counters are subsets, and local tokens are not cloud tokens avoided.
