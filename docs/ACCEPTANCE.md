# Focused companion acceptance

This is the historical pre-repair acceptance record. Its original reproductions
are retained in `tests/companion_crash_baseline.py`. The subsequent local repair
and its guarantees are documented in [recovery](RECOVERY.md); current release
gates are in [release readiness](RELEASE-READINESS.md).

Status: suitable only for supervised local use; **not a Windows release candidate**.
This pass uses the preservation matrix and integration report as its baseline.
It does not repeat the preservation audit or certify general model quality.

## Packaged practical task

A fresh Windows Python 3.13 virtual environment installed the baseline wheel
(`c419cc3839ce126fc78adac000b86369fc995a1b5a6c7775a559194040d84338`)
with the constrained tray dependencies. Imports resolve inside site-packages;
`pip check` passes. The environment is isolated on the existing Windows host,
not a fresh Windows machine. The shell's initial network restriction required
rerunning installation with network access; dependency pins were not loosened.

The real repository task reviewed companion crash recovery through the existing
`review_change` workflow, generic profile and Large compute cap. The local
explorer used the configured GPT-OSS preference and produced a durable summary
with repository evidence. A fresh worker received the same handoff packets for
the review stage. The GPT-OSS review attempt failed and handed off to Codex;
it did not produce a valid local review. No substitute model was silently used.
The supervising Codex reviewed the code and process evidence, corrected the
summary's overly broad crash-safety wording, and completed explicit checkpoints.
This is completion of a bounded review task, not approval to release.

The run completed with seven durable workflow jobs and seven separately reviewed
events, ending at `codex_verified`. Usage feedback records the explorer as
corrected and the failed local review as rejected. Companion event decisions
record the supervisor's corrected handoff, rather than accepting a failed model
answer. All worker processes exited; the callback delivery table remains empty.

The two local calls used exact `gpt-oss:20b`, digest
`17052f91a42e97930aa6e28a6c6c06a983e6a58dbb00434885a0cf5313e376f7`.
Reported usage: explorer 2,249 input / 186 output; failed review 2,431 / 342.
The latter token counts do not imply a usable answer. No benchmark was launched.

Local jobs finish before review: their events remain pending and the dock shows
`waiting_for_codex`. Explicit local supervisor decisions are recorded separately
with `supervisor_local_review`; they do not represent an authenticated callback.
The task's original `not_run` validation status is retained and acknowledged,
rather than rewritten as model-certified testing. Actual acceptance checks are
documented by the supervisor outside that immutable evidence envelope.

## Recovery acceptance: release blocker

`tests/test_companion_acceptance.py` uses isolated databases, a deterministic
loopback provider and real child processes terminated with `os._exit` at commit
boundaries. It is characterization coverage: passing tests reproduce and expose
the unresolved defect; they do not mean recovery is safe.

| Interruption | Observed restart behavior | Recovery verdict |
|---|---|---|
| Before companion job claim | Queued job executes once after restart | Recoverable |
| After job claim / workflow creation | Job retained as interrupted; no automatic replay | Explicitly blocked |
| After workflow claim / reservation | Lease expires to handed_off; spent reservation retained | Explicitly blocked |
| Provider answer before result reference | Provider work can exist without saved result content | Content cannot be reconstructed |
| After result-reference or stage commit, before companion completion | Ledger advances, handoff content is absent, job becomes interrupted | **Release blocker** |
| Inside companion completion transaction | Job/result/event transaction rolls back together; earlier workflow commit survives | **Same cross-store blocker** |
| After companion completion commit | Result and unique review event survive restart | Recoverable |
| After waiting-checkpoint or accepted-checkpoint commit | Ledger says waiting_for_codex or codex_verified; companion job is interrupted without result | **Release blocker** |
| Review claimed before invocation | Controller restart marks delivery uncertain; no replay | Explicit reconciliation required |
| Fixture response before delivery commit | Response artifact survives; delivery uncertain; no duplicate invocation | Inspect artifact, reconcile delivered |
| Fixture response after delivery commit | awaiting_decision survives; no duplicate invocation | Review decision required |

Detection uses `companion status` and `companion workflow-status --job JOB_ID`
together. Compare the companion result/handoffs with workflow version, stages,
attempts and result references. The companion detects the abandoned worker;
workflow status expires the durable lease. There is no automatic cross-store
repair or synthesized replacement packet.

For a missing handoff, `workflow-next` refuses the interrupted job. Repeated
submission of the same task returns the same job; repeated restarts do not run
it again. A supervisor may record a rejected local review and finalize the
companion run **blocked**. This closes the incident record but does not recover
the lost content or resolve the underlying ledger. Preserve both databases and
scope new work explicitly when needed. Do not treat that procedure as a fix.

In the tested cases no job row disappears, no local generation repeats, and
there is one completion review event per job. Losing output while preserving
the job row is still data loss. Durable cross-store reconciliation remains a
release requirement; no recovery implementation was added in this focused pass.

## Callback boundary

The local callback file/stdio/subprocess path is exercised with synthetic CLI
executables and synthetic session IDs. Checks cover the exact resume ID,
untrusted-evidence packet, retained artifacts, authentication_required blocking,
and explicit delivered/not_delivered reconciliation. A second claim is made
only after evidence-backed explicit reconciliation of an unsent fixture claim.
This is a local contract test, **not a live Codex callback test**.

No authenticated session initialization or callback was sent. Existing explicit
authorization is absent, so the actual authenticated end-to-end callback is
pending. It must not be inferred from local supervisor review or fixtures.

## Installation, usability and minimal fix

The live answer exposed a Windows redirected-output defect: `companion status`
raised UnicodeEncodeError on a nonbreaking hyphen. The only production change
in this pass makes CLI JSON use ASCII escapes, preserving the decoded strings.
A regression forces cp1252 output with both that hyphen and a CJK character.

Validation after the fix: **17 process/encoding acceptance tests passed** in
183.79 seconds; **75 existing companion/workflow regressions passed** in 46.39
seconds. Those 17 include characterization of the release-blocking recovery
failure. Ruff and the documentation checker pass; the public allowlist audit
has 174 files and no findings. The rebuilt source distribution installs with
the documented tray dependency constraints in a second clean virtual
environment; `pip check` passes. Packaging retains all 31 definitions. Only
`companion_cli.py` changes among packaged runtime files relative to the baseline.

Native Tk checks inspect dock status/details and the public selector against
the installed inventory. GPT-OSS remains the selected preference; exact
`qwen3:14b-q4_K_M` remains installed with digest
`bdbd181c33f2ed1b31c972991882db3cf4d192569092138a7d29e973cd9debe8`.
Neither personal routing configuration nor models are modified.

Missing-service checks use an isolated unavailable loopback port, leaving the
real Ollama service alone. The dock displays unavailable/stale inventory; the
CLI fails visibly (with a raw connection traceback). The troubleshooting guide
provides start-service guidance. An empty-inventory fixture verifies install
guidance and exact-model rejection with no substitution and no download request.
These tests do not simulate uninstalling Ollama from a fresh machine.

Remaining manual checks: authorized live callback/session resumption and its
actual authentication/quota behavior; fresh Windows install with documented
prerequisites; declared Python 3.11 minimum; visual dock/tray behavior, DPI,
keyboard/focus and hide/reopen during real work. Other-platform certification
and active-resource performance measurements remain outside this Windows pass.

All changes remain staged. No commit, push, tag, publication, model download or
deletion, stable-checkout change or frozen-runtime update is part of this pass.
