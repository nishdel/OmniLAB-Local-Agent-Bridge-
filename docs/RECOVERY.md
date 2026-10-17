# Companion workflow recovery

This repair addresses the two-database interruption defect reproduced in
[focused acceptance](ACCEPTANCE.md). It uses the existing WorkflowEngine and
ledger transitions. It does not replay inference, repository actions or
checkpoint decisions, and it does not require a Codex callback.

## Authority and commit ordering

Both databases use SQLite WAL with `synchronous=FULL` on writer connections.
Their commits are independent. The repair never relies on an atomic transaction
across WAL files.

| Record | Authority and atomic boundary |
|---|---|
| Model response only in memory | Not durable; cannot be reconstructed after the process exits |
| `companion_payloads` in the workflow database | Exact bounded packet, sources and digest; committed in the same transaction as its `workflow_results` reference |
| Workflow step/checkpoint | Existing `workflow_runs`, stages and events; its full `companion_operations` receipt commits in that same transaction |
| Explicit checkpoint intent | Saved request bound to job/attempt/request digest; a committed transition receipt proves the engine validated and applied it |
| Companion result and logical review request | Copied receipt, unique completion event and destination receipt marker commit together in `companion.sqlite3` |
| Supervisor review | Existing event decision/validation and run status commit together in the companion database |
| Final verification | Existing finalization transaction, gated by the current committed workflow version and matching explicit supervisor checkpoint while the workflow database is locked |

Only companion workflow jobs opt into packet/receipt persistence. Original
caller-driven workflow APIs remain metadata-only and keep their existing
handoff contract. Companion workflow storage now includes private excerpts and
results in **both** databases; protect the entire companion data directory.

The operation identity is the durable job ID, attempt ID and exact saved-request
digest. Packet keys include operation, stage, skill and version. The original
packet serialization/digest contract is retained. The receipt contains the
post-transition version, exact handoffs, status and usage; it is authoritative
even when the downstream companion write has not happened.

Copying the receipt and acknowledging it are separate transactions. A crash
between them repeats the copy safely: the destination marker and unique job
review event identify the already-applied receipt. Acknowledgment is never used
as proof of approval. Competing recovery is serialized by the existing worker
kernel lock and database transactions. The lock order is workflow database,
then companion database, including final verification.

## Automatic repair

Worker/controller startup reconciles abandoned companion workflow operations.
For an existing state directory, a local-only inspection/repair can be requested
without launching generation:

```powershell
python -m localagentbridge --config config.local.toml companion recover
python -m localagentbridge --config config.local.toml companion status
```

If the worker is alive, its lock prevents a competing recovery owner. Recovery
does not reread mutable repository files, invoke Ollama, authenticate or send
callbacks. A later explicitly requested workflow step still performs the normal
repository, policy, model and evidence-freshness checks.

- A committed operation receipt restores the missing companion result and one
  pending review event. Saved payloads are verified against their digests and
  operation identity. No inference or decision is repeated.
- A saved partial packet without a committed terminal transition is retained in
  an **interrupted** result. Ownership recovery uses the existing interrupted
  lease state; it does not infer that the whole stage finished. Reservations
  remain spent. This is preserved evidence, not successful completion.
- A committed checkpoint restores exactly its recorded workflow state. Only an
  actual accepted final checkpoint can carry `codex_verified`. Local completion
  never creates that approval, and the review event remains a separate decision.
- An old terminal companion result can restore a missing completion event
  without changing the result. Existing logical review events keep their IDs.
- An old metadata-only transition is reconstructed only with a uniquely matching
  job, exact successor version and event, and every required packet available
  from saved companion evidence. A legacy checkpoint additionally needs its
  saved predecessor and matching explicit action/note hash. A saved rejection
  remains rejected; it is never turned into acceptance.

## Intervention and limits

`companion status` includes durable recovery dispositions; `companion recover`
returns the affected job IDs and diagnostics. The workflow database retains
operation receipts and packet evidence even when applying a receipt is refused.

- Output never committed to a durable packet is unavailable. Old result hashes
  cannot recreate lost text. Preserve the incident and explicitly scope new work
  if needed; there is no blind retry or token-position resume.
- Partial steps, mismatched/corrupt receipts, missing legacy packets and ambiguous
  legacy transition attribution require supervisor inspection. They do not
  become successful jobs.
- A stale version cannot overwrite newer workflow state. Recovery does not
  change the ledger to match an old receipt. Inspect the newer decision and the
  saved receipt before deciding how to proceed.
- Cancellation, already-recorded reviews, conflicting results and finalized
  runs are preserved. A contradictory receipt is retained for inspection, not
  silently substituted beneath an existing review. No cancelled job is queued
  again and no duplicate logical review is requested.
- An interrupted job remains non-successful under existing finalization rules,
  even if a useful partial packet was saved. A supervisor may close it as
  blocked and scope new work; the saved packet can inform that decision.

The companion schema upgrade is additive (version 1 to 2); existing rows are
retained. New private journal tables are additive to the workflow usage database.
Do not downgrade a live state directory to an older companion runtime. As
before, do not upgrade an active controller/worker; keep old runtimes and state
backups until recovery evidence has been inspected.

## Tested failure model

The pre-repair installed wheel reproduced 13 original crash/checkpoint cases.
Those tests characterize the defect and deliberately retain the old expectations;
they are not a claim that recovery worked before this change. Isolated copies of
those actual old databases were also opened by the repaired package: both saved
checkpoint cases were reconciled, while the missing-output case stayed explicit.

Final validation: 411 Windows tests passed with one privilege-dependent symlink
test skipped; 50 focused recovery/acceptance tests passed from outside the
checkout against the final installed wheel. Ruff, documentation and public-source
checks passed. Python 3.13 was available; Python 3.11 remains untested.

| Failure scenario | Previous behavior | Repaired behavior | Test evidence |
|---|---|---|---|
| Response before packet transaction commits | Response lost; job interrupted | Still unavailable, never reported recovered or replayed | `test_crash_boundaries_preserve_jobs_and_prevent_blind_replay`, packet before/inside transaction exits |
| Packet commits, terminal transition does not | Digest survives but output is lost | Exact committed packet retained; job remains interrupted | Same boundary test; `test_second_crash_during_reconciliation_retains_original_saved_payload` |
| Terminal workflow commit before companion completion | Output/handoff absent downstream | Committed receipt restores exact result and one review event | Boundary test plus `test_owned_process_termination_after_commit_recovers_exact_receipt` |
| Checkpoint commits before downstream update | Ledger advances; companion stays interrupted | Exact committed checkpoint copied; explicit decision not repeated | `test_checkpoint_commit_window_is_reconciled_without_replaying_decision`; original-database upgrade copies |
| Destination commit before journal acknowledgment | No reconciliation protocol | Repeated delivery uses the same receipt marker and review identity | Boundary test; second-crash tests; competing/repeated receipt delivery |
| Supervisor decision interrupted | Same-database transaction was already atomic | Decision/run status remain atomic; recovery preserves existing review | `test_review_decision_transaction_crash_is_atomic` |
| Stale, cancelled, reviewed or finalized work | No cross-database reconciler | Existing decisions win; contradictory receipt stays inspectable | Stale-version, identity, cancellation/review/finalization tests |
| Legacy hash-only output or ambiguous checkpoint | No output recovery | Intervention required; no invented packet or inferred approval | Legacy missing-payload, differing-note and migration tests |

The actual upgrade sequence installed v0.4.1, then the previous companion
schema-1 wheel, then the repaired wheel in a disposable environment. All old
usage, settings, job, review, cancellation and finalization rows were compared
and preserved. Future journal versions are rejected before creating current
journal tables. The pre-companion ledger subclass keeps its original `finish`
call contract; its mock-answer regression exposed and verified this correction.

Tests use isolated persistent SQLite files, deterministic providers, forced
`os._exit` boundaries and termination of an owned Windows subprocess. They cover
transaction rollback, saved payload equality, interrupted reconciliation,
copy-before-ack, repeated/competing recovery, stale identities/versions,
cancellation, existing reviews and legacy migrations. The original expectations
remain runnable against the old installed package in
`tests/companion_crash_baseline.py`.

These tests model process crashes on a working local filesystem. They do not
prove host power-loss safety, disk/controller flush behavior, recovery from a
physically corrupted or lost database, or correctness after arbitrary manual
database edits. SQLite guarantees and honest local storage remain prerequisites.
Live callback, fresh-machine installation and visual acceptance are independent
release gates; none is a prerequisite for local database reconciliation.
