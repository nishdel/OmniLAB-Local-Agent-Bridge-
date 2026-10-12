# Selective local execution implementation report

## Strata upgrade — 2026-10-12

**Delivered adapter/configuration work; Strata is not functional or enabled on
this machine.** Stage A stopped at missing runtime/compatible assets. No Strata
inference, LAB advisory through Strata, or OpenHands/Strata implementation passed.
[Current setup and installation approval package](SELECTIVE-SETUP.md#independent-strata-status)
and [source-verified workflow](WORKFLOW.md#source-map) are the canonical details.

### Verified starting point

The workspace root is an older non-Git source copy. Work continued in the existing
isolated `codex/selective-local-execution` checkout at
`a9a4bad6eaa2761d3a3648854f83664a94bc119d`, preserving both uncommitted manual
session documents. Its former LocalAgentBridge origin redirects to OmniLAB.
Draft PR #1 was open on that exact head with successful Windows validation;
main was `f6df420181f21856cb421619e2c1310f6cf46685`, latest release v0.4.1.
The retained close-out installed package is 0.5.0.dev0, wheel SHA-256
`df9b041c8198213b9237078e39fe71ff18e7c6e55112c771ee7d516f88db2429`;
all **88 installed runtime files equal the starting Git revision**. The older
operations file points to an earlier GPU package with three differing accounting
files; it was not mistaken for this newer package. Installed runtimes were not upgraded.

| Component | Implemented | Live verified | Enabled | Published where at start | Remaining work |
|---|---|---|---|---|---|
| Durable LAB v0.5 and dock | Yes | Scoped prior lifecycle/backend evidence; owner confirms opening and some selections only | Project config active | Development branch / PR #1 | Full human controls acceptance |
| Ollama advisory | Yes | Qwen27 prior runs and one advisory in this pass | Qualified project config; service initially stopped | Development branch / PR #1 | No general performance claim |
| OpenHands implementation | Restricted SDK 1.53.0 | Qwen27 and Qwen35 fixture + UTC accepted; Gemma fixture accepted, UTC output-limited; 4B acceptance failed | Project-only approved categories; Docker engine initially stopped | Development branch / PR #1 | No new SDK execution claimed here |
| Strata | Existing adapter, now hardened | No live model/API/SDK qualification | Disabled | Development branch / PR #1 | Explicit installation approval, loaded identity and stages A/B/C |
| Main / release | v0.4.1 | Historical scope | Separate from development | Default branch / release | Human review and merge; no release authorized |

### Implementation and evidence boundaries

The existing `ChatProvider` now bounds metadata and SSE bytes, translates SDK
text blocks, validates tool-result history, rejects images/unsupported streaming
tools, pins non-thinking behavior, disables runtime MCP, checks output counters,
and validates actual serving identity before and after each request. The existing
host-only mailbox path is unchanged. `strata_identity.verify_binding` checks
trusted complete artifact/config metadata against the listening server and child
engine, exact arguments, template and loaded context. Model-name echoes never
establish identity. Readiness errors distinguish unreachable, disabled, unloaded,
unverified and incompatible states. No fallback or cloud inference was added.

`companion provider-status` adds read-only diagnostics; configured Strata profiles
appear in the existing model selector with explicit status and an unavailable
reason. Only reviewed, loaded, verified choices are selectable. The same durable
setting stores `strata::ALIAS`; explicit contracts keep backend/model separate.
Existing Ollama selections, profiles, workflow budgets, recovery, cancellation,
expiry, review/integration guards, protected tests and dock controls are retained.

Current upstream source is pinned at
`7695859aa13afb248bdb4d36f9b2e95707db079d`; release metadata is 0.1.43.
Installed Qwen35 is `qwen3.6:35b`, parent
`qwen3.6-source:35b-a3b-mtp-q4_K_M-20260824`, qwen35moe / Q4_K_M,
35,505,251,456 parameters, 256 experts / 8 active. Current manifest identity is
`a7eb95c53bcf96b4bdd008d0fab4a5dac88047d9c1a7a9ab88ed453423fbd87c`.
The manifest references main weight SHA-256
`d372de8e934898a59e6ccfabc3368474711384d8f1fd4d22d87a3f0a45400cdc`;
its 21,718,480,960-byte file and GGUF v3 header were observed. The full weight
was not rehashed or loaded during this pass. It is not a Flash-Next Coder binding.
Ollama's nine-tag inventory was read without model replacement or cloud access.

### Staged qualification

| Stage | Actual result | Next gate |
|---|---|---|
| A: Strata readiness + bounded inference | **Blocked before inference**: no service/config/runtime or compatible assets in bounded inventory; disabled project setting confirmed by CLI | Approve the pinned installation package; verify actual headers/weights/engine and loading peaks |
| B: LAB durable advisory through Strata | **Not run**, prerequisite A failed | One correlated bounded job after A |
| C: LAB → restricted OpenHands → Strata → edits/tests → Codex | **Not run**, A/B failed | Disposable protected fixture, exact tool round trip, independent diff/test acceptance |
| Strata cancel/failure | Deterministic transport cancellation closes the response; HTTP rejection/timeout certainty tested. Live unreachable endpoint observed. **No live generation cancellation claim** | Once A passes, qualify owned inference cancellation and retained uncertain reservation |
| LAB → Ollama/Qwen27 advisory | Completed and independently reviewed **after Codex correction**; no local code patch | Contribution ledger records exact job/receipt, limits, timings and measured peaks |

The one advisory used a separate durable store and the unchanged installed worker,
with exact native Qwen27 context/GPU settings. Its [contribution record](LOCAL-CONTRIBUTIONS.md#strata-upgrade-advisory--2026-10-12)
keeps model output and Codex correction separate. The adapter/security work was
direct Codex work; a model cannot approve its own architecture or permissions.
The broad benchmark pilots remain inactive and no token savings are claimed.

### Validation and publication

Focused provider/profile suite: **66 passed** (fixture-based, overlapping the full
regression). Full regression, packaging, documentation/diagram validation and
publication results are recorded in the final addendum below. The initial full
run was retired after source review changes; it is not counted as a completed gate.

The README now includes architecture and advisory/implementation sequence views;
WORKFLOW retains its detailed sequence, lifecycle, trust, storage and accounting
views and source map. The existing eleven-row manual ledger records two incomplete
owner observations and nine untested rows, with **zero fully passed rows**. No
widget, callback, fresh-install or performance gate was removed. The diagrams
make no claim that Codex runs locally or that SQLite dispatches jobs.

Private evidence is retained under the task's dated evidence directory:
`local-inventory.json`, `installed-base-check.json`, `qwen35-weight-inventory.json`,
`advisory-dispatch.json`, `advisory-result.json`, `advisory-review.json`, test logs,
source/package hashes and diagram validation. Databases, private config, source
inspection cache, raw model output and machine paths are excluded from publication.


### Final validation addendum — 2026-10-12

- Full Windows source regression: **614 passed, 1 skipped**, 883.45 seconds.
  The skip remains conditional; it is not live Strata or complete human acceptance.
- Offline-installed package: **114 passed**, overlapping the full suite. Wheel
  inspection matched **89 runtime files**. Wheel/sdist built from the explicit
  public allowlist; copied v0.4.1 usage/checkpoint survived the supported upgrade.
  Existing dependencies were reused without downloading or replacing the controller.
- Ruff and generated CLI/configuration checks pass. The source-reference check
  inspected 46 Markdown files, 311 local links, 47 anchors and 43 code symbols.
  Public-source audit inspected 232 files with no findings; no private config,
  databases, raw job/session logs or weights are included.
- Eight native Mermaid diagrams parse with the existing local Mermaid 11.12.2
  renderer. All eight were visually inspected in the browser. The overview and
  trust view were revised to remove cramped groups; retry labels were shortened.
  The detailed six-participant sequence remains a deeper view suitable for zoom.
  GitHub's actual renderer and exact remote CI are checked after pushing; their
  outcome belongs to PR #1's current validation, not this pre-push snapshot.
- The two owner observations remain incomplete and nine human rows untested.
  Native widget control/persistence/error/cancellation acceptance was not performed
  through the browser. Strata live stages A/B/C and live generation cancellation
  remain blocked as recorded above.

Publication target remains `codex/selective-local-execution` and draft PR #1.
No main-branch update, merge, tag, release, general enablement or runtime upgrade
is performed. Remote review/CI and the retained human merge gates still apply.


Latest scoped result: [bounded MoE batch](OPENHANDS-STRONGER-QUALIFICATION.md#bounded-moe-configuration-batch--2026-10-10). Qwen35 independently completed fixture and UTC with full collection; Gemma passed a safe fixture but its UTC response exhausted output. Qwen27 remains preserved and was not rerun. Both pilots and general routing stay disabled. Earlier sections retain historical scope.

Historical bounded qualification: [qwen3:4b-instruct outcome](OPENHANDS-BOUNDED-QUALIFICATION.md).
Real SDK tool calls worked, but generated code failed protected acceptance; the
useful repository task remained gated for that configuration. New terminal/collector controls preserve
failed evidence and do not activate implementation or either pilot. Earlier model
results below remain historical, configuration-specific evidence.

Previous scoped status: see the [scoped OpenHands qualification](SELECTIVE-LIVE-QUALIFICATION.md#scoped-openhands-qualification--2026-10-09). It supersedes earlier installation, transport and model-safety blockers; the historical results below retain their original identities. Pilots and production implementation remain inactive.

Candidate: **codex/selective-local-execution**, based on companion development
`0b817c572a81a22c94988cdbf163d214957985b7`. Changes are uncommitted. In the original implementation pass, no push,
merge, release, issue publication, model download/deletion or system installation
was performed. Existing development/release trees and historical evidence are retained.

The [live qualification report](SELECTIVE-LIVE-QUALIFICATION.md) supersedes the
initial hardware observation. It records the final installed candidate, targeted
MCP/lifecycle/quota fixes and historical live results. The later
[blocker-resolution report](SELECTIVE-BLOCKER-RESOLUTION.md) records the clean
full regression, current model inventory, enforced sandbox probes and separate
pinned approval manifests. It supersedes the earlier unresolved size/image notes.

The historical [installed-model follow-up](SELECTIVE-LIVE-QUALIFICATION.md#installed-model-follow-up--2026-10-09)
records 508 passed / 1 skipped in the complete rerun and 97 overlapping installed
checks. All nine installed tags were inspected; Qwen3.8 passed the small advisory
and tool screen without correction. Implementation remains blocked by the pinned
SDK, bounded tmpfs transport and real context gates. This follow-up also discloses
Ollama's unintended pruning of two unused blobs and automatic GPT compatibility
conversion/tag change. The original implementation's no-change statement above
does not describe those later cache side effects. Defaults and pilots remain
unchanged; no runtime/test changes were made in the latest pass.

## Components and status

| Component / changed files | Status | Evidence and limit |
|---|---|---|
| Contracts, selected canonical skills and deterministic routing: task_contract.py, selective_config.py, config.py | Implemented; automatically verified | Separate lane/provider/orchestration; old aliases/profiles/reviews retained; cycles, unsafe scope and invalid overrides fail closed. |
| Durable state/review: task_store.py, companion_store.py, companion.py | Implemented; automatically verified | Additive schema 3, atomic admission, exact-candidate acceptance, bounded correction, owned restart reconciliation and a shared inference reservation. Actual prior-package upgrade preserved runs/jobs/events. |
| Ollama advisory reuse: ollama_advisory.py, selective.py | Implemented; automatically and live verified | Existing Bridge schema, exact identity, thinking and accounting reused. Final installed MCP/controller/worker advisory completed on RTX 3060 after MCP closure. This does not qualify implementation. |
| Strata HTTP adapter: inference.py | Implemented; automatically verified; live untested | Pinned upstream source inspected; mocked readiness/models/Chat Completions JSON/SSE, reasoning separation, errors and limits. No installed serving binding or model fit qualification. |
| OpenHands executor: sandbox.py, executor_assets/*, qualification.py, tests/test_selective_bounded.py | Implemented; automatically verified; Qwen27 and Qwen35 scoped UTC tasks independently accepted | SDK/tools 1.53.0 and the final collector exercised through actual read/edit/test loops. Qwen35 collection and independent protected/telemetry checks passed; Gemma passed its safe fixture but its UTC completion hit output allowance. Earlier 4B and collection failures remain historical evidence. No general routing or pilot activation. |
| Candidate verification/integration: selective.py, integration.py | Implemented; automatically verified | Independent baseline/candidate/combined checks; preserved acceptance files; exact byte hashes; no automatic acceptance/commit. Windows byte-preserving and interrupted integration tests. |
| Companion controls and display: selective_cli.py, companion_cli.py, dock.py | Implemented; automatically verified; manual untested | Real lane/backend/model, skills, parent/children, routing, verification/review/integration and observed/unavailable usage. Existing dock/focus architecture retained. |
| Resources and measurement: selective_resources.py, measurements.py | Implemented; automatically verified | Measured whole-system memory admission, resident-model checks, phase provenance and optional counters. No invented cloud attribution or savings. |
| Pilot and release guidance: prepare_selective_pilot.py, examples/selective*, SELECTIVE-*.md, ROLE-MIGRATION.md, manual guide/draft | Prepared; GPU pilot unrun | Eight matched synthetic starter cases, three independent arms, identical acceptance inputs; no solutions or inference run by preparation. Human/native and conditional checks remain unmarked. |
| Distribution: pyproject.toml, MANIFEST.in, PUBLIC-FILES.txt, check_docs.py, prepare_release.py | Automatically verified | Wheel/sdist inspection, non-editable isolated install, retained definitions/executor assets, source audit; fresh-machine manual qualification remains. |

The [design record](SELECTIVE-EXECUTION.md), [role mapping](ROLE-MIGRATION.md),
[setup/rollback](SELECTIVE-SETUP.md), [pilot protocol](SELECTIVE-PILOT.md) and
[manual draft](release-testing/selective-execution-issue-draft.md) contain the
detailed interfaces and prerequisites.

## Final blocker-pass validation

Full regression: **508 passed, 1 skipped**; all **225** formerly failing-run cases
passed as a subset. Installed final wheel: **97 passed**, overlapping the source
coverage. Actual package bytes match the tested runtime exactly. Production expiry
remains unchanged and rejects late ownership/result/finish in deterministic clock
checks. This pass changed only documentation, not runtime or test code. See the
[blocker report](SELECTIVE-BLOCKER-RESOLUTION.md) for hashes and evidence.

## Initial implementation validation and genuine local contribution

These earlier suites overlap; do not add their counts. Current qualification
results and exact package identity are in the linked live report.

The unchanged baseline passed **411 tests, 1 skipped**. The expanded full regression
run passed **498 tests, 1 skipped in 637.92 seconds**. The skip is the existing
Windows symlink privilege condition. Final UI counter wiring, context guard and
malformed-provider hardening are validated by the separately recorded final
targeted suite: **181 passed**. The final correction/dependency review fix then
passed **95 focused tests**. No failures remain in those source runs. See the retained
JUnit files for exact case outcomes. All **94 selective tests also passed against
the installed final wheel in 16.71 seconds**, outside the source checkout. A further
**36 retained workflow/checkpoint tests passed** after correction resolution changed.

Ruff, generated configuration/CLI documentation checks and public-source audit
are required final gates. Build inspection confirms all **31** existing canonical
definition files and all three executor build inputs. Install/upgrade checks use
separate non-editable environments, existing dependency paths and no global Python
changes; they are not fresh-machine installation qualification. The first wheel
lifecycle run exposed a missing pywin32 path in the isolated test harness; enabling
the installed dependency bootstrap fixed it, and the complete 94-test rerun passed. Only a 1.3 MB
setuptools 77.0.3 build dependency was fetched into an isolated task directory.
OpenHands, container images and model weights were not downloaded.

Private evidence under workspace data/ includes:

- selective-final-regression.xml, selective-final-targeted.xml and selective-correction-final.xml.
- selective-wheel-tests-final.xml for tests against the installed final runtime.
- selective-source-audit.json; selective-packages-final/inspection.json and the local wheel/sdist.
- selective-upgrade-validation.json and the pre-upgrade backup.
- selective-local-contribution, selective-live-advisory and selective-live-native.
- selective-upstream source snapshots and selective-pilot-prepared/manifest.json.

The real stable LAB/Qwen3:4b test-plan advisory supplied concurrent-admission,
dependency and partial-recovery suggestions; Codex used these as prompts for
tests and rejected unsupported uncertainties. Codex authored and reviewed the code.
The first generic-chat advisory smoke failed; that evidence remains intact.
The corrected native Bridge smoke used **1,011 input / 145 output tokens**, reported
**7.263 s model loading / 17.756 s provider total**, and took **20.322 s** at the
controller. Codex checked its useful missing-model finding against source and
excluded an unrelated uncertainty. Execution finished before supervisor review.
See [the contribution ledger](LOCAL-CONTRIBUTIONS.md). These are observations,
not a comparative pilot, independent acceptance or cloud-token savings.

## Migration and rollback

1. Let the old worker relinquish its jobs; retain its fixed runtime. Make a SQLite
   backup with the worker/controller stopped, keeping all historical artifacts.
2. Test the candidate non-editable package with a separate copy of that data.
   First open applies additive schema 3. Defaults preserve existing behavior:
   selective admission, Strata and implementation remain disabled.
3. Configure exact identities, selected skills, memory plan and optional sandbox
   only after the documented prerequisites. Use contract-route before submission.
4. Disable selective.enabled for a feature rollback while retaining schema-3
   history. For an older runtime, restore the pre-upgrade backup into a different
   data directory and preserve all newer evidence separately. Never downgrade
   user_version, delete tables or overwrite the only database.

The automated upgrade used the actual pre-change wheel (schema 2), created a run,
completed job and accepted review, backed up the database, installed the candidate
and reopened twice. Those original rows were identical after migration. Corrected attempts retain their
original failed/rejected rows; dependents resolve the explicitly authorized correction
and successful finalization still requires its exact acceptance/integration.

## Remaining boundaries and exact next steps

Current observation **2026-10-08T17:14:47.8599842Z**: **34,139,435,008 bytes RAM,
RTX 3060 12,288 MiB, driver 560.94, PCIe Gen3 x4**, Windows 10 Home 19045.
The internal GTX 1060 Max-Q reports Code 31 and is absent from nvidia-smi;
its current UUID/VRAM is unavailable. The earlier eGPU-absent observation is historical.

Earlier Ollama qwen3:4b advisory was live verified for short RTX-only requests at
16,384 context. That exact tag is now absent from the supplied model directory;
qwen3:4b-instruct is present and requires fresh binding/qualification. No model
was changed by this pass. Durable MCP jobs use the independent controller.

OpenHands remains disabled. The existing quota gate correctly rejects this Docker
backend; bounded read-only tmpfs allocation probes passed, but docker cp transport
and the current exit/collection lifecycle cannot use that profile. The published
SDK-version server image exists; the isolated Python SDK environment still needs
approval and construction. These are environment/adapter blocks, not observed
SDK or model-tool-use failures.

The [blocker-resolution report](SELECTIVE-BLOCKER-RESOLUTION.md) resolves the
separate pinned dependency manifests and download totals. Its storage estimates
are explicitly distinct from measured installation/peak usage. Strata has no
local model assets; driver 560.94 is below its standard >=580 minimum. A common
581.80 compatibility candidate has a security-maintenance caveat and unconfirmed
exact Dell INF binding. Preserve the working RTX setup pending supported driver
guidance; the experimental CUDA 12 alternative remains unqualified.

Approve OpenHands independently if desired, qualify its restricted SDK fixture
with an existing exact Ollama model, then qualify Strata separately. No real
implementation fixture succeeded. The original eight-case pilot remains inactive
and not ready; a narrower two-arm study would require a separate protocol and
activation. Human dock checks remain unexecuted.

Current limitations are explicit: implementation edits are bounded UTF-8 exact
paths; deletion/rename/binary edits and arbitrary new directories are unsupported.
New contract jobs are single stages; workflow orchestration returns to the existing
workflow-submit/next/checkpoint interfaces. The inference reservation coordinates
one LAB data directory, not unrelated processes/controllers started elsewhere.
Unconfirmed provider termination holds the queue until trusted reconciliation.
Containers/evidence are retained for review; cleanup is not automatic.

Passing tests is not acceptance or a security proof. Container/tool compatibility,
Strata serving identity, real context fit, human UI behavior and the GPU pilot remain
unqualified. No authorized review callback was sent. Codex supervision still uses
its configured data path, even when inference is local.

## Exact changed-file inventory

- MANIFEST.in
- PUBLIC-FILES.txt
- README.md
- SECURITY.md
- docs/ARCHITECTURE.md
- docs/CONFIGURATION.md
- docs/LOCAL-CONTRIBUTIONS.md
- docs/MANUAL-RELEASE-TESTING.md
- docs/ROLE-MIGRATION.md
- docs/SELECTIVE-EXECUTION.md
- docs/SELECTIVE-BLOCKER-RESOLUTION.md
- docs/SELECTIVE-IMPLEMENTATION-REPORT.md
- docs/SELECTIVE-LIVE-QUALIFICATION.md
- docs/SELECTIVE-PILOT.md
- docs/SELECTIVE-SETUP.md
- docs/release-testing/selective-execution-issue-draft.md
- examples/selective-contract.json
- examples/selective.toml
- localagentbridge/companion.py
- localagentbridge/companion_cli.py
- localagentbridge/companion_store.py
- localagentbridge/config.py
- localagentbridge/dock.py
- localagentbridge/executor_assets/Dockerfile
- localagentbridge/executor_assets/requirements.txt
- localagentbridge/executor_assets/runner.py
- localagentbridge/inference.py
- localagentbridge/integration.py
- localagentbridge/measurements.py
- localagentbridge/ollama_advisory.py
- localagentbridge/qualification.py
- localagentbridge/sandbox.py
- localagentbridge/selective.py
- localagentbridge/selective_cli.py
- localagentbridge/selective_config.py
- localagentbridge/selective_resources.py
- localagentbridge/task_contract.py
- localagentbridge/task_store.py
- pyproject.toml
- scripts/check_docs.py
- scripts/prepare_release.py
- scripts/prepare_selective_pilot.py
- tests/test_companion_recovery.py
- tests/test_companion_acceptance.py
- tests/test_selective_contracts.py
- tests/test_selective_flows.py
- tests/test_selective_integration.py
- tests/test_selective_process.py
- tests/test_selective_mcp.py
- tests/test_selective_providers.py
- tests/test_selective_sandbox.py


Gemma-only follow-up, 2026-10-10: the [single scoped comparison](OPENHANDS-STRONGER-QUALIFICATION.md#gemma-comparison--2026-10-10)
stopped its fixture during loading at the unchanged GPU-memory ceiling. No
Gemma implementation was accepted; UTC was not run. This is a resource/configuration
blocker, not a model-quality failure. Qwen's independently accepted isolated UTC
patch is preserved. No runtime code, installation, production default or pilot
changed; a further Gemma configuration requires a new scoped authorization.


Current batch changes and validation (2026-10-10): optional scoped native Ollama
`draft_num_predict` forwarding/validation in inference.py and selective_config.py,
three deterministic cases and setup/report documentation. Codex performed this
bootstrap directly; the local model generated its isolated UTC patch. Full source
564 passed / 1 skipped; 153 overlapping extracted-wheel checks passed; copied
v0.4.1 upgrade retention passed. No install or schema change. Final identities,
cleanup and storage are in data/openhands-moe-20261010. Both original checkouts and
the accepted Qwen27 patch remain unchanged. Human dock checks remain untested.
