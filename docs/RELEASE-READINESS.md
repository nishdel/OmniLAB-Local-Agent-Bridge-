# Companion candidate readiness

Status: **cross-database process-crash recovery blocker resolved; Windows release
gates remain open**. The [focused repair](RECOVERY.md) persists authoritative
packets/transition receipts and reconciles downstream results without replay.
Unsaved output, incomplete stages and ambiguous legacy incidents still require
explicit intervention; they are never reported as recovered success.

Final Windows suite: **411 passed, 1 skipped** in 644.98 seconds. The skip needs
Windows symlink privileges; the separate reparse-point guard regression passes.
Final installed-wheel recovery suite: **50 passed** in 490.61 seconds. The old
wheel's 13 failure characterizations are retained. Actual v0.4.1/schema-1 wheel
upgrades preserve historical rows; copies of the original checkpoint incidents
repair automatically, while lost hash-only output remains unavailable.

One packaged repository review used exact GPT-OSS routing through the existing
workflow engine (1,595 input / 72 output tokens), with independent Codex review,
an explicit checkpoint and three separately recorded reviews. The incorrect local
finding was rejected; Codex supplied corrected analysis. Local completion was
observed before review completion. The final compatibility correction preserves
the original non-companion ledger method contract; the local step's installed
runtime was retained unchanged, and the final wheel handled the subsequent
checkpoint after all earlier workers exited. See [contributions](LOCAL-CONTRIBUTIONS.md).

Native dock/model-selector and missing-provider/model guidance checks pass.
The GPT-OSS preference, exact Qwen tag/digest, stable checkout and frozen runtimes
are preserved. No models were downloaded/deleted and no callback was sent.
Supervised local use is supported within [recovery's restrictions](RECOVERY.md).
Windows RC gates remain: authorized real authenticated callback testing, a fresh
Windows machine/VM installation, Python 3.11, human visual/interaction acceptance,
and the privilege-dependent native symlink check. New virtual environments on
this host are isolated installs, not fresh-machine tests.
The existing active-resource/perceptual measurement checklist is also retained;
no performance certification or other-platform certification follows from this repair.

## Historical feature-preservation follow-up

The following records are the baseline for the focused repair above. Their
byte-equality claims and counts describe that earlier candidate; necessary
recovery changes to the workflow/ledger are documented separately, without
repeating the broad preservation audit.

The [matrix](FEATURE-PRESERVATION.md) compares the actual pre-companion v0.5
implementation, not merely v0.4.1. Of 70 implementation/configuration/test files
compared with the frozen manifest, only `__main__.py`, `bridge.py`, `config.py`
and `widget.py` differ (additive CLI/transport options and the previously justified
dead UI cleanup). Workflow, workflow ledger, catalog, delegation, adaptive routing,
service, schemas, all 31 definitions, profiles and pre-companion v0.5 regressions
remain byte-identical. All 20 compatible built-in role/skill pairs are now tested
through executable custom project-catalog stages.

The missing companion integration is repaired with the existing Service and
WorkflowEngine, full configuration, policy identity, one durable step/checkpoint
per job, persisted bounded handoffs, exact model digest checks, local review
tracking and dock budget/checkpoint details. See [integration](COMPANION-WORKFLOWS.md).
No implemented feature was removed because it was unpublished/experimental.

Latest full Windows acceptance: **359 passed, 1 skipped**, 148.24 seconds,
including native Tk and real detached processes. Subsequently added exact-Qwen
single-opinion and uncertain-local-review regressions pass in the **35-test**
workflow integration suite. A final retry-after-completion check exposed volatile
planning estimates in the submission identity; comparison now excludes only those
estimates while retaining task/configuration/policy/model identity. The subsequent
companion and workflow suite passed **73 tests** (one native test deselected,
already covered by the full Windows run). Existing real MCP stdio tests retain 7-tool opt-out
and 13-tool workflow-enabled behavior. Providers in automated tests are synthetic.
The CLI integration test uses a disposable Git repository and exercises workflow
submission/retry, worker restarts, status, next step, checkpoint, local review and
successful finalization without initializing a Codex session.

The first broad run exposed a Git-owner-dependent CLI fixture and a transient
Windows `Access denied` during research-worker atomic state replacement. The
fixture now owns a disposable repository. State replacement now retries Windows
sharing/access errors for at most 200 ms; persistent failure remains an error and
retains old state plus temporary evidence. Both paths have regressions. The
original coordinating implementation and frozen research evidence were not edited.

Live local verification used a frozen pre-companion multi-stage GPT-OSS workflow
(1,861 input / 256 output), then a separately frozen candidate worker's durable
workflow direct path (633 / 64) and fixed sequential consensus (GPT-OSS 508 / 60;
exact Qwen3 14B 363 / 165). The launcher exited independently. The worker completed
and exited; the next workflow step after restart stopped at the supervisor
checkpoint. The two opinions disagreed, which is retained. No broad model-quality
claim follows. [Contribution accounting](LOCAL-CONTRIBUTIONS.md) explicitly
separates these paths from the initial direct Bridge calls.

The documentation checker validates **29 Markdown documents** and generated
CLI/configuration references. The public allowlist has **172 files**, with zero
pattern/ignore findings. Updated wheel/sdist and isolated-install verification
cover 72 wheel entries, all 31 definitions and all 172 allowlisted source files;
the extracted source's documentation and audit also pass. Isolated installation,
upgrade sentinel preservation, uninstall data retention and CLI submission/retry/
cancellation are recorded separately from the older package evidence below. No authenticated
callback, model download/deletion, stable checkout edit or publication occurred.

At that baseline, the cross-store crash window was explicit: an engine-ledger commit could
outlive a crash before companion handoff persistence. Reservations remain spent;
missing content requires supervisor recovery/new scope, never silent replay.
Original v0.5 workflows are still continued through their original interface,
not automatically imported into the companion. Fresh-machine, Python-minimum,
other-platform and authenticated-callback gates remain open.

## Initial candidate record (before the follow-up above)

Repository: existing `nishdel/LocalAgentBridge`, clean stable checkout at
`f6df420181f21856cb421619e2c1310f6cf46685` (v0.4.1). Development branch:
`companion-release-candidate` in a separate worktree. The original workspace root
had no Git metadata and contained newer v0.5 work; commit `cc88d4d` preserves that
source before candidate changes. The stable checkout and original runtime source
remain unchanged. No models, historical evidence, user DBs or unrelated projects
were deleted.

The previous Qwen terminal review was inspected before development: recorded
`started`, reviewer and worker absent, final events were network reconnection
failures, no response/report artifact. This is an unresolved interrupted review,
not a successful review or confirmed graceful controller exit. No duplicate old
review or Qwen benchmark was launched.

## Staged work and validation

1. Inspected state, preserved newer source, hashed frozen runtime/environment.
2. Added inventory, exact model selection, durable jobs/outbox and callbacks.
3. Tested lifecycle recovery and used genuine local code/test/doc contributions.
4. Added dock, contributor/user/security docs and evidence-backed cleanup.
5. Clean package/install/upgrade and end-to-end gates are recorded below as run.

Baseline: 276 passed, 1 skipped, 8 failed. Seven native tests failed because the
restricted shell could not initialize Tcl; one lifecycle test asserted completion
artifact existence before the worker finalized it. That race now waits for both
terminal state and the artifact. Native tests run outside that restriction:
14 passed. New companion plus protected-worker targeted suite: 63 passed.

New automated tests cover duplicate submissions/completions, simultaneous review
claims, busy session serialization, restart with uncertain delivery, seven-day
quota retry metadata, authentication/network failure categories, cancellation,
missing models, explicit final validation and deduplication. Clock advancement to
six hours/seven days is simulated, not a multi-hour model run. Real detached
Python processes with fake Ollama prove worker independence and result persistence.

Live contributions: GPT-OSS 20B code/test/doc proposals and one focused correction;
see [ledger](LOCAL-CONTRIBUTIONS.md). Their quality required corrections. No full
Qwen evaluation was run. The genuine candidate worker completed independently (853 input / 129 output tokens,
92.35 seconds bridge execution); the result was rejected on supervising review.
Its callback remains pending because automatic approval review rejected sending
repository-derived content/result and local paths to authenticated Codex without
specific permission. No completed live callback or successful run finalization is claimed.

## Cleanup and compatibility

- Removed unreachable registry controls, horizontal detail table, set_cap,
  toggle_details and refresh_details from LegacyDashboard. Factory dispatch sends
  all registry configs to RegistryDashboard; existing v0.1/v0.2 views remain
  supported and their native tests pass. No supported CLI/UI route was removed.
- Removed duplicate process/lock/Windows Job Object implementations from the
  research IO module, importing tested shared process_control primitives. Frozen
  historical jobs retain their old snapshots. New runner snapshots include the
  shared helper and fixture module.
- Removed the obsolete one-time freeze_v02.py from the development tree. It was
  already excluded from public packaging and had no current entry point, caller
  or test dependency; historical fixture/evidence files remain untouched.
- Removed the redundant benchmark dependency extra; psutil is core for durable
  process identity. Existing constraints already pin psutil/pywin32. No third-party
  runtime dependency was removed merely because a static scan found few imports.
- Replaced private-evidence-dependent lifecycle fixtures with explicit synthetic
  fixtures. Protected cancellation/ownership tests remain. The old assertion that
  current source must equal a historical snapshot was replaced by public profile
  compatibility plus per-experiment frozen-input verification.

Remaining research scripts have active tests/CLI/reference uses and are retained;
this is not a claim that every remaining line is necessary. Research evidence is
excluded from runtime packages, not deleted or relocated as a cleanup shortcut.

## Known limits and release gates

Callbacks are dedicated read-only reports. Automatic integration into the original
desktop task is not implemented; the supervisor records decisions/validation.
Managed sessions must be exclusive to this controller/store. Cross-client busy
session coordination and a general app-server event transport are not implemented.
Structured reset/error handling is tested with fixtures; CLI versions can emit
unstructured reconnect errors, which require manual reconciliation.

Shared-server cancellation cancels the HTTP request, not guaranteed server-side
generation. No exact token-position resume, inference during shutdown, model
download manager, bundled executable installer, or non-Windows desktop
certification is claimed. Models exposed through Ollama must truthfully report
their remote metadata. Raw diagnostics require manual redaction before sharing.

Python/Tk is retained; measurements are recorded separately from Ollama inference
in the local validation evidence. No language rewrite or inference speedup is claimed.

## Final observed validation

| Check | Observation |
|---|---|
| Complete Windows suite | 320 passed, 1 skipped in 135.21 seconds, before the final three added regressions |
| Latest companion regressions | 38 headless passed, 1 native test separately passed; includes callback source evidence, digest-scoped validation and inventory-timestamp retry cases |
| Ruff / whitespace | Passed |
| Documentation | 27 Markdown files have valid local links; configuration keys and companion action flags are generated/checked against code |
| Real lifecycle | Detached fake-provider worker survives launcher exit; real worker termination reconciles interrupted; kernel ownership/cancellation regressions pass |
| Simulated lifecycle | Six-hour execution, seven-day quota/reset, auth/network failures and duplicate/uncertain callback cases; not real multi-hour inference or real quota exhaustion |
| Genuine local work | Three initial GPT-OSS proposals, one focused correction, one candidate worker run; rejected/corrected outcomes recorded |
| Live Codex resumption | Blocked by automatic approval review; specific approval requested for the exact final packet; never substituted with a fixture claim |
| Wheel install | Fresh Windows venv, constrained dependencies, pip check clean; import path verified inside installed environment; 12 roles / 15 skills load |
| Upgrade | Actual v0.4.1 wheel installed in disposable environment; synthetic usage record survives upgrade to candidate and companion schema creation |
| Public export | 164 allowlisted files, zero audit findings at first final audit; exact export and rebuilt archive inspection recorded in local validation evidence |
| Publication | None; stable v0.4.1 checkout/tag unchanged |

The package is a wheel/source distribution, not a bundled executable installer.
Clean environment means a new venv on this Windows host, not a fresh Windows VM.
Only Python 3.13 on Windows was exercised here; the declared Python 3.11 minimum
and other operating systems still need a compatibility matrix run.

Tested dependencies include httpx 0.28.1, mcp 1.30.0, psutil 7.2.2, pywin32 312,
Tk 8.6.15, Pillow 12.3.0, pytest 9.1.1 and Ruff 0.16.7. Build used setuptools 84.0.0.
The frozen initial dogfood server was Ollama 0.34.3; shared-server correction and
candidate calls used Ollama 0.32.5. Installed Codex CLI inspected was
0.155.0-alpha.16.4; live callback behavior on it remains unverified.

One warm controller sample (no inference) measured 1.51 seconds startup, 43.16 MiB
resident memory, 0.78% of one CPU during a two-second idle sample and 9.76 ms mean
SQLite setting transaction over 100 writes. The controller then exited with code 0.
These are laptop samples, not performance guarantees. Active inference CPU/peak
memory, true callback latency and perceptual UI responsiveness remain unmeasured;
native UI functional checks pass. No C#/C++ rewrite was justified or attempted.

The development branch contains separate baseline, feature and cleanup commits.
Final documentation and follow-up corrections remain staged while the pending
live run retains base `8b02eba`. The public stable checkout is still `f6df420`.
Review the staged diff and source hashes alongside this report; do not confuse
its Git HEAD with an assertion that the staged tree was already committed.
