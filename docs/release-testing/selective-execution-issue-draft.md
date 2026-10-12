# Unpublished selective-execution manual test draft

This is the current source-change draft, not a published issue or completed manual
acceptance. The [previous draft](0.5.0.dev0-issue-draft.md) and historical package
evidence remain intact. Build/package hashes and exact candidate revision must be
filled from the reviewed artifact before owner testing. No published release is
claimed. Use [manual definitions](../MANUAL-RELEASE-TESTING.md) and the
[setup/qualification guide](../SELECTIVE-SETUP.md).

Candidate: codex/selective-local-execution; accepted deployment checkpoint
bec07f63bc8a0991576d7392353f1a541615eeeb plus the recorded close-out commits. Rechecked 2026-10-10: Windows 10 19045, 32 GB RAM,
RTX 3060 12,288 MiB, driver 560.94; internal GTX reports Code 31.
Human acceptance: Passed 0 / Failed 0 / Blocked 0 / Incomplete 2 / Not tested 9 / N/A 0.

Manual session prepared 2026-10-10 for runtime source
`a9a4bad6eaa2761d3a3648854f83664a94bc119d`, retained wheel SHA-256
`df9b041c8198213b9237078e39fe71ff18e7c6e55112c771ee7d516f88db2429`.
All 88 runtime files match the installed package and that source. The private
kit's `identity.json` records isolated configuration, fixture and definition
hashes; no inference or human interaction occurred during preparation.
Actual tester/date and observation evidence are pending. This existing table
is the sole result location for the authorized unpublished session; issue
publication remains unauthorized. Start with the
[current Qwen27 idle-display procedure](../MANUAL-RELEASE-TESTING.md#current-qwen27-disposable-display-kit--2026-10-10).
All eleven result rows and their full criteria remain unchanged.

The current 27B configuration independently passed the frozen UTC repository task.
The later bounded batch also accepted Qwen35 fixture and UTC; Gemma accepted
its fixture but exhausted the UTC output allowance. No human acceptance row has passed. See
[stronger-model qualification](../OPENHANDS-STRONGER-QUALIFICATION.md); the
[4B bounded failure](../OPENHANDS-BOUNDED-QUALIFICATION.md) remains historical.
Hidden Tk observations are not human verification. See
[live qualification](../SELECTIVE-LIVE-QUALIFICATION.md) for the latest nine-tag
inventory, four-model screen, full regression and separate approval manifests;
[blocker resolution](../SELECTIVE-BLOCKER-RESOLUTION.md) retains earlier probes.
Automated/mocked and live smoke results are in the [implementation report](../SELECTIVE-IMPLEMENTATION-REPORT.md),
separate from this table. Assess applicability before changing Blocked/N/A.

Current automated milestone: project-only Qwen27 default and supervised routing
are active. Clean committed-source regression is 591 passed / 1 skipped; 180 extracted-wheel checks overlap and are recorded separately.
Installed start/cancel/recovery/restart and the actual dock data binding were
checked. Qwen documentation was accepted without repair, UTC tests after local
retry, and advisory after a three-word Codex trim. No human row below changes.
Exact package/runtime/config hashes and rollback state are in private
`data/qwen-standard-20261010/` evidence. Strata remains disabled under Q-15.
Net operating token savings are not established; partial cancelled usage is unknown.

| Test | Tested? | Result | Issue registered | Evidence/notes |
|---|---|---|---|---|
| Package identity, launch, upgrade and rollback (M01, C05) | Partially (owner) | Incomplete | — | Owner confirmed the widget opens (reported 2026-10-12); package/upgrade/rollback criteria remain. Final installed candidate checked locally; fresh Windows/human launch remains required. |
| Displayed model/backend, usage and absence (M02, C01, C02) | Partially (owner) | Incomplete | Q-21 (local) | Owner confirmed some options can be selected; exact identity, receipts and unavailable counters not observed. Confirm exact selected model/backend and measured versus unavailable usage against the job receipt. Keep missing values unknown. Strata disabled: Q-15. |
| Explicit model override and restart persistence | No | Not tested | — | Select a default, submit an explicit override, then restart dock/controller after work resolves. Verify the override affects that job and the saved default persists; no silent substitution. |
| Idle -> running -> awaiting review -> completed (M03) | No | Not tested | — | Observe all four dock states and elapsed time; completed requires trusted review/finalization. Hidden widget checks do not establish human acceptance. |
| Keyboard, focus, DPI and readability (M04, M05) | No | Not tested | — | Human/native acceptance still required. |
| Hide/reopen and cancellation (M06) | No | Not tested | — | Cancel a bounded owned job in the dock; verify cancellation/uncertainty and resource release. Hiding/reopening must not silently cancel work. Automated lifecycle checks already recorded. |
| Retained workflows, profiles, budgets and checkpoints (C03) | No | Not tested | — | Include new contract dependency/integration order. |
| Conditional managed review callback (C04) | No | Not tested | — | Separate callback authorization is still required. |
| Conditional OpenHands isolation and tool round trip | No (human); live qualification recorded | Not tested | Q-10, Q-12, Q-14 | Current final collector + qwen3.8:27b passed fixture and useful UTC task with independent acceptance. Later Qwen35 fixture/UTC accepted; Gemma fixture accepted and UTC output-limited. Historical failures retained. Scoped project activation is recorded in the standard-model milestone; human controls remain untested and unrelated pilots remain inactive. |
| Candidate verification, stale/forged acceptance and recovery | No | Not tested | — | Include one correction then escalation and exact combined integration checks. |
| Conditional eGPU/resources and matched pilot (C06) | No | Not tested | Q-20 (local draft) | RTX short checks verified separately; pilot inactive/not ready; human responsiveness untested. |

All inherited detailed M01–M06 and C01–C06 procedures remain applicable through
these grouped references; this compact table does not waive them. New selective
checks are defined in the manual guide's selective-execution addendum. No model,
driver, Docker/WSL, networking, callback, issue publication or release publication
is authorized merely by filling this draft.


## Bounded pre-merge follow-up — 2026-10-10

At published source `819448220e03b406001382bc684d0b539b727694`, neither main nor
the PR branch contained an Actions workflow. Repository Actions was enabled;
the API listed zero workflows/runs, not a queued job or an approval request.
The follow-up adds [minimal PR validation](../../.github/workflows/pr-validation.yml)
with read-only permissions and existing mocked-provider checks. Exact published
SHA and CI result belong to [draft PR #1](https://github.com/nishdel/OmniLAB-Local-Agent-Bridge-/pull/1);
workflow presence alone does not pass acceptance.

Graphical access was retried: the embedded browser kernel failed during Windows
sandbox initialization (setup refresh errors). Native desktop control is unavailable
in this session. **No human check or graphical Mermaid check passed.** The existing
11 rows and detailed criteria remain unchanged. No local inference, restart,
model/configuration change or benchmark was needed for CI security review.

Owner diagram review: inspect one overview in [README](../../README.md#system-overview),
four views in [WORKFLOW](../WORKFLOW.md), and two retained views in
[ARCHITECTURE](../ARCHITECTURE.md) on GitHub. Confirm all seven render; inspect
labels, clipping, arrow direction, protected/write boundaries and Strata's explicit
disabled alternative. Local parsing and fetched Markdown HTML are not graphical
GitHub evidence. The previous syntax evidence remains applicable because the
seven blocks did not change.

## Historical evidence and qualification issues

Local draft only; none published. New milestone status is recorded above; the following earlier evidence is retained.

Qualification issues:

- Q-01: Docker containerd storage accepted size=2G without enforcing it. Final
  candidate blocks it. Read-only tmpfs writes now prove ENOSPC at every configured
  capacity. Scoped pass now verifies fixed exec seeding/collection, durable collection-before-stop
  and independent checks with the actual SDK. Default quota gate still fails closed.
- Q-02: MCP Windows job cleanup killed a descendant worker. Fixed by using the
  existing independent controller; final installed advisory survived client close.
  Restart now preserves an orphaned reservation for trusted reconciliation.
- Q-03: Git inherited MCP stdin and hung. Fixed with DEVNULL/no-console probes.
- Q-04: Internal GTX Code 31 and split 582.66/560.94 driver assignment; shared
  service uses 560.94. Cause remains unproven. Common 581.80 compatibility evidence
  has security/OEM caveats; no driver change recommended without supported guidance.
- Q-05 (historical): Published SDK-version image was reachable, not installed; pinned Python SDK
  build manifest is resolved (101,666,057 download bytes). Separate Strata manifest
  resolves model/draft/runtime/source artifacts. Installation and real SDK/model
  qualification remain blocked pending approval; no download/installation performed.

Historical advisories and the current GPT advisory required Codex correction;
Qwen3.8 passed the new fixture without correction. No real implementation patch
or integration was claimed in that earlier screen; the later scoped pass accepted one
synthetic SDK fixture and integrated only its disposable target. Automated checks
do not complete this human table.

- Q-06: Three retained crash tests expired their four-second fixture lease before
  the injected crash. The fixture allowance is now 15 seconds; production limits
  and actual lease-expiry assertions remain unchanged. Closed by full regression
  (508 passed, 1 skipped; all prior 225 cases passed) and deterministic boundary
  checks against the installed final wheel. Counts overlap; human rows stay untested.

- Q-07: Four-model screen completed on the installed candidate. Qwen3.8 passed;
  GPT needed two editorial correction groups; Qwen3.6/Gemma exhausted the advisory
  output budget and had fenced-JSON format failures in compatible/both probes.
  This earlier screen did not qualify implementation. The later scoped pass
  verifies one exact Qwen3.8 SDK fixture; production/category and pilot gates remain inactive.
- Q-08: Ollama startup unexpectedly pruned two unreferenced blobs (identities
  unknown). Pruning was then disabled. Automatic GPT compatibility conversion
  subsequently added a 13,793,422,816-byte derived blob and changed its tag digest
  to 9ba9cc2b4e02. Original referenced files remain present; other eight wrappers
  are unchanged. No rollback/delete was attempted and no qualification transfers
  to the changed binding. See the full before/after evidence in live qualification.

Earlier retained installed wheel SHA-256:
`42de265e805c4b2216f40cb5db5bea5f6fe238275f45eccf49b26768785c4233`.
Its 97-test rerun overlaps the full 508-pass suite. Current documentation/source
package hashes are recorded privately in installed-models-20261009/final-package-identity.json;
copy them from the chosen artifact before human testing. Both original and narrower
pilots remain inactive; this draft does not authorize installation or activation.


Scoped update, 2026-10-09: the [current qualification report](../SELECTIVE-LIVE-QUALIFICATION.md#scoped-openhands-qualification--2026-10-09)
records the exact approved dependency installation, model-store protection,
64k RAM/editor failure, one corrected 32k SDK fixture, separate independent
verification, exact Codex acceptance, disposable integration, real pending-mailbox
recovery/cancellation and final source/installed artifact identities. Q-01's
alternative transport and Q-05's installation blockers are resolved for that
specific image/fixture. The first 64k attempt remains failed; no result is erased.
GPT-OSS remains reassessment-required. General implementation reliability, Strata,
eight-case comparisons, and all human checks remain unqualified/inactive.

Automated final candidate: wheel SHA-256 `92185269dfab4f678680056599b2213f7b63a908110ab4f4f10fe5e83808b09a`; full source **523 passed / 1 skipped**, **112 overlapping installed checks passed**; separate 0.4.1 upgrade data retention passed. Source/sdist/dependency identities are in the linked qualification evidence. Human counts above are unchanged.

- Q-10: Current qwen3:4b-instruct model produced incorrect function/class changes
  in the real SDK fixture. Protected tests failed; conservative context admission
  stopped the next request. No qualification or repository-task acceptance granted.
- Q-11: Native SDK content-block conversion was missing; fixed with protocol tests.
  First rejected HTTP400 attempt is retained separately from real model inference.
- Q-12: Failed candidate was lost on early sandbox stop. Fixed persistent command
  audit plus quiescent bounded collection; live cancellation/missing-audit cases
  tested. The old candidate cannot be recovered. Initial PID1 freeze failure is retained.
- Q-13: Running Ollama added one 891-byte manifest blob. Existing tags/weights
  remained unchanged. Blob retained; no pruning, model replacement or retagging.

Current validation/identities are in openhands-bounded-20261009/final-validation.json
and final-package-identity.json. Earlier package/test references above are historical;
never add overlapping source/installed/selective counts. Human rows remain unexecuted.


Stronger-model follow-up (2026-10-09): the current evidence root is
openhands-stronger-20261009. The final collector image is unchanged. Exact models,
context, actual tool use, independently accepted UTC patch, preserved failures,
resource peaks and separate full/installed validation are in the
[stronger-model report](../OPENHANDS-STRONGER-QUALIFICATION.md). All ten human
rows remain untested. No actual/manual result is inferred from these live or
automated checks.

- Q-14: 35B retry produced a correct retained fixture and passing command, but
  normal collection rejected an unexpected process owner. External Docker stats
  removes the diagnostic exec concurrency source; original transient PID cause
  remains unproven. Guard retained. Failed attempt stays failed; no third fixture
  or UTC job admitted for 35B. A new scoped attempt budget is required.
- Q-15: Earlier 4B context stop was conservative serialized-byte admission,
  not a measured tokenizer overflow or cumulative-token limit. Per-request
  role/tool/overhead/output/margin accounting and strict native context controls
  now make this distinction explicit. No guard or production expiry was weakened.
- Q-16: Bounded Strata discovery recovered only preparation/source records in
  searched locations. Actual runtime, complete assets and serving binding remain
  unlocated; new installation/download decisions remain separately approval-gated.


Latest automated source/package gate: **561 passed / 1 skipped**, with **150
overlapping installed checks passed**, 85 byte-identical installed package files,
222 audited public files and supported copied v0.4.1 upgrade retention. Nine tests
were added; no prior cases removed. Final identities are private in
openhands-stronger-20261009/final-package-identity.json. Human counts stay unchanged.


Gemma-only comparison (2026-10-10): [current report](../OPENHANDS-STRONGER-QUALIFICATION.md#gemma-comparison--2026-10-10).
No human table result changed. One actual SDK fixture request hit the retained
GPU stop (11,980 > 11,776 MiB); all failed-job bytes were collected before stop.
No model reply, tool call or candidate edit completed; UTC was not authorized
after the failed fixture. This is a resource/configuration result, not a coding
quality result or an efficiency win. Qwen's accepted UTC patch remains isolated.

- Q-17: Gemma4:26b Q4_K_M at context 65,536 / output 1,536 / 18 GPU layers plus
  its installed MTP draft exceeds the qualification VRAM reserve during loading.
  No OOM or GPU-loss response was observed. Ownership guard, memory ceiling and
  policy remain unchanged. A new explicit scoped attempt would be required for
  another configuration; no retry or general qualification is implied.

New checks: 150 installed selective cases passed using a fresh scoped temp
folder (same cases as the initial 63-pass/87-temp-setup-error invocation, not
additional tests). All 85 package files still match the previously tested runtime.
The full 561-pass/1-skip result and upgrade evidence above remain historical,
not re-executed here. Current lint/docs/source/diff evidence is in
openhands-gemma-20261010/validation.json. Human counts remain 0 / 0 / 0 / 10 / 0.


Bounded MoE follow-up (2026-10-10): [current report](../OPENHANDS-STRONGER-QUALIFICATION.md#bounded-moe-configuration-batch--2026-10-10).
The compact human table and 0 / 0 / 0 / 10 / 0 counts remain unchanged.

- Q-18: Gemma now safely loads with request-scoped draft 0 / 16 GPU layers,
  context 65,536 / output 1,536, unchanged guards. Genuine SDK fixture independently
  accepted. Its one UTC attempt exhausted output on request five; full failed
  collection retained the unchanged baseline. Not a context or memory failure,
  and no accepted UTC implementation. Earlier Q-17 remains valid for its old config.
- Q-19: Fresh Qwen35 fixture and UTC both completed collection, protected checks
  and independent Codex acceptance; 10 isolated telemetry tests passed. No code
  repair/integration. Earlier Q-14 failure stays failed; its transient cause is
  not retroactively proven. Qwen35 used lower VRAM but more host RAM and longer
  accepted UTC execution than historical Qwen27; no new baseline run occurred.

New runtime source gate: 564 passed / 1 skipped, with 41 focused and 153 extracted
wheel checks overlapping that suite. Three draft-option cases added. No dependency
installation; optional setting omitted preserves existing defaults. Final source,
wheel/sdist, upgrade, lint/docs/audit/diff and cleanup records are private in
openhands-moe-20261010. Model identities, original checkouts and accepted Qwen27
patch preserved. Pilots/general routing inactive; human verification still pending.

- Q-15 (current): Optional Strata has no runnable compatible installation/assets in the bounded inventory. The inspected Flash-Next upstream does not qualify dense Qwen27; separate weights/runtime/driver compatibility and safe admission remain unresolved. No large download, driver/network change or live Strata acceptance is claimed.

- Q-20 (close-out): Usage identity bindings and missing/duplicate/conflict checks now pass. Historical generation-only baseline and shared hybrid supervision do not provide complete matched costs. No new comparison was run; net savings remain unknown. Mixed controller usage is retained explicitly. This local entry is not a published issue.


## Strata upgrade retest scope — 2026-10-12

Q-21 (local entry, not a published issue): Strata choices require an exact
configured profile and binding; unavailable/unqualified choices show a reason
and cannot be saved. Retest the existing model/backend row for `strata::ALIAS`,
installed/compatible/qualified/enabled distinctions and identity mismatch errors.
Use the existing persistence row to verify saved provider plus model after a
restart and an explicit different per-job override. Retest progress/error/cancel
rows against durable receipts. No Strata live runtime exists in this candidate's
inventory; fixture tests do not pass these human checks. No existing criterion
or conditional approval requirement is waived.

The owner's limited observation above passes no complete row. Automated protocol,
selector and cancellation results belong to the upgrade report. Graphical Mermaid
inspection is tracked there separately from the eleven widget acceptance rows.
