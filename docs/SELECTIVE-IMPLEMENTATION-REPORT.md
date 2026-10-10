# Selective local execution implementation report

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
