# Stronger-model OpenHands qualification — 2026-10-09

## Standard model milestone

Current milestone: **project Qwen27 default and supervised routing active**. The existing
`codex/selective-local-execution` worktree and HEAD
`0b817c572a81a22c94988cdbf163d214957985b7` were preserved. The starting manifest
records all pre-existing changes separately. The prior 564 passed / 1 skipped
source run and 153 overlapping wheel checks were verified in their actual logs;
they are not the new milestone's validation counts. Historical accepted patches,
original checkouts, Qwen35 acceptance, and Gemma's incomplete UTC result remain.

The personal project profile selects `qwen3.8:27b` on Ollama 0.40.2:
`aaee06c39dcf2437cde036998d960e1fc1494b8191be7cc9657d01e509097813`.
The exact dense Qwen35-architecture weights are Q4_K_M; the tag's name does not
identify a separately qualified architecture. Full local blob hashes matched the
accepted manifest. Qwen27's historical UTC patch was independently inspected and
applied exactly; its immutable original remains intact.

The native request and actual runner agree on context 65,536, 28 GPU layers,
draft MTP 4, one sequence and loopback serving. Maximum output is 1,536 per
response, temperature zero, thinking false, no truncation or context shifting,
and keep-alive 120 seconds. Receipts preserve backend/template/digest, request
options and observed runner process identity. Stored template SHA-256:
`b507b9c2f6ca642bffcd06665ea7c91f235fd32daeefdf875a0f938db05fb315`.
The runner uses the accepted chatml template path with no Jinja. The final safety audit added explicit rejection of missing/zero loaded VRAM for GPU profiles. A clean-start positive check observed 8,051,543,243 loaded GPU bytes and used 152 input / 31 output tokens; its one-sentence advisory was independently accepted without repair as a validation probe. Unknown or
changed effective settings stop the job; configuration fields alone are not proof.

The pinned OpenHands SDK/tools 1.53.0 image and restricted file mailbox were
reused. Native inference is performed by trusted LAB outside the networkless
tool container. There are no host-drive mounts, Docker socket, credentials,
privileges or general outbound network inside the model's tools. Only declared
task files are writable; original input and acceptance checks are protected.
Live tool-policy rejections are retained as failed-attempt evidence.

Strata is a separate disabled provider. The inspected upstream commit
`fb58e0dbc8399662c0e47c76578c6e878b14f6cf` (engine 0.1.41) supports the
documented Flash-Next candidates, not this qualified dense Qwen27 combination.
No runnable compatible installation or weight set was located in the bounded
local inventory. The proposed roughly 64 GB Coder assets were not downloaded;
CUDA 13's documented driver requirement also exceeds this host's driver.
The existing CUDA 12 alternative is not qualification. No Strata live acceptance,
tool round trip, cancellation or loaded identity is claimed. Services are not
exposed to a LAN, and system networking/drivers remain unchanged.

Final source regression: **586 passed, 1 skipped** in one complete run after
the GPU fail-safe. Every Python source/test hash matches that run's manifest.
Earlier 583-pass evidence remains preserved separately.
Extracted-wheel checks overlap this suite and are
reported separately in the private package evidence. Lint, 45-document checks,
the 228-file public allowlist/source audit, offline installation and the actual
0.4.1 retained-state upgrade passed. Final wheel/sdist identities and counts live
in the evidence manifest, avoiding a package hash embedded inside itself.

Real contributions: AGENTS guidance accepted without Codex repair; seven UTC
tests accepted after one local retry with no Codex patch repair; installed-default
advisory accepted after a three-word Codex trim to meet its 120-word requirement.
The advisory used 992 actual input and 208 output tokens, with no model override.
The installed controller verified the same digest, loaded 65,536 context and
effective runner profile from a clean start.

Live cancellation observed a new inference loader, reached durable cancellation,
retained the uncertain reservation and reconciled it only after an empty resident
inventory. No shared Ollama process was terminated or model manually unloaded.
Controller shutdown/restart and recovery preserved job states without replay.
The cancelled call's partial counters are unavailable, not zero. Timeouts,
malformed/truncated completions, protected writes, provider switching and ownership
boundaries also have deterministic and process regression coverage; deliberate
host memory exhaustion was not attempted. Historical live OpenHands mailbox
cancellation/recovery evidence remains valid for the unchanged pinned executor.

The actual dock is open on the project store. Hidden real Tk tests verified its
state/usage data and expand/collapse against the live retry. Keyboard/focus/DPI,
readability, tray and human click/hide/reopen checks remain **not tested**; the
manual ledger has ten untested rows. Automated observations do not pass them.

Milestone evidence is under workspace `data/qwen-standard-20261010/`:
`starting-point.json`, `identity-before.json`, `assets-verified.json`,
`operation/companion/` durable jobs/receipts, `comparison/`,
`strata-status.json`, and final acceptance/activation records. Installation
paths and exact local commands are recorded privately in `operations.txt`.
See [setup and rollback](SELECTIVE-SETUP.md#qwen27-project-workflow),
[contribution outcomes](LOCAL-CONTRIBUTIONS.md#qwen27-standard-model-milestone),
[accounting methodology](SELECTIVE-PILOT.md#milestone-accounting) and the
[compact manual ledger](release-testing/selective-execution-issue-draft.md).

Codex owns safety, provider bindings, integration and final decisions; these
changes are direct supervising work. Qwen's real bounded documentation and test
tasks have separate reviews, including failed attempts. The small isolated
Codex-only test-generation comparator used the same frozen inputs and protected
checks, and never supplied its solution to Qwen. It reported 23,173 input,
0 cached input and 1,127 output tokens (393 reasoning tokens are an output
subset). That artifact phase cost 24,300 cloud tokens; supervision and evaluation
overhead are separate. Matched hybrid supervision cannot be isolated completely
from this implementation session: **net operating savings are not established**.
Actual implementation investment, cutoff, identifiers and missing metrics remain
auditable in the existing usage store. No monthly or subscription-cost saving is
claimed.

Previous: [bounded MoE batch](#bounded-moe-configuration-batch--2026-10-10) — Qwen35 fixture and UTC independently accepted; Gemma safe fixture accepted, UTC output-limited. Historical results below remain unchanged.

Earlier follow-up: [the single Gemma comparison](#gemma-comparison--2026-10-10)
ended at the GPU-memory stop during loading. Qwen's accepted UTC patch remains
unchanged and isolated; Gemma has no implementation acceptance.

This report supersedes the current readiness conclusions of the
[4B bounded qualification](OPENHANDS-BOUNDED-QUALIFICATION.md), whose failures and
artifacts remain historical evidence. Historical qualification was scoped to that batch; the current project activation is recorded above. Both broad pilots remain disabled. Branch:
`codex/selective-local-execution`, base `0b817c572a81a22c94988cdbf163d214957985b7`.
Original development/release checkouts remain separate. No commits or publication.

Evidence root: workspace `data/openhands-stronger-20261009/` (N).
The old frozen task and initial approval evidence remain in
`data/openhands-bounded-20261009/` (R) and
`data/openhands-scoped-20261009/` (S).

## Source and narrowly scoped bootstrap

Codex performed infrastructure changes directly while combinations were
unqualified; these changes are not local-agent contributions. The controller
runs hashed source copies N/runtime-1 and N/runtime-2, never changing its imports
while it owns work. The pinned SDK/tools remain 1.53.0. The final collector image
used by every new model attempt is
`sha256:b0ec53df107bdbb7b9df9c397ee56d4f7f74bc49d6e6550b16ca6f23e5748090`.
No image/base/dependency replacement occurred. The existing 174-artifact package
and its 101,666,057-byte approved payload were reused. New downloads: **zero**.

Changed infrastructure:

- `inference.py`: transparent per-request accounting, explicit native Ollama
  context/offload/keep-alive controls, disabled backend truncation/context shifting
  when requested, actual prompt/output counts and provider timings.
- `task_contract.py` / `selective_config.py`: compatible optional safety/repair
  budgets and exact-contract supervisor approvals. These substitute only for
  category pilot admission; identity, tool, sandbox, risk and memory gates remain.
- `selective.py`: persist rejected-request accounting; enforce bounded SDK error
  recovery; collect cancelled work before stopping volatile storage.
- `qualification.py`: fixed-seed repeated fixture, explicit limits and optional
  policy-only execution guidance; no changes to its semantic acceptance.
- `tests/test_selective_bounded.py`: corresponding admission, native settings,
  fixture identity and repair-budget regressions.

No Codex-authored candidate solution was supplied to either model.

## Context and resource admission

N/historical-context-audit.json replays the rejected 4B request without inference.
Its serialized request occupied 32,306 UTF-8 bytes; the old 1,024-token output
reservation required a conservative 33,330-token allowance against 32,768.
This was a **conservative admission rejection**, not measured tokenizer/KV-cache
overflow. It was not cumulative input-token usage. No exact local tokenizer was
verified. The conservative full-JSON byte bound remains, with role/tool/overhead
accounting and a new explicit safety margin; no requirements, failures or history
are silently removed. Actual tokenizer counts are recorded separately when the
backend responds. Ollama 0.40.2's request controls were checked against its
[API types](https://github.com/ollama/ollama/blob/v0.40.2/api/types.go).

Both Qwen configurations use 65,536 context, 1,536 output, 1,024 extra safety,
temperature 0, thinking false, native Ollama, strict context and 120-second
keep-alive. GPU layers: 14 for 35B, 28 for 27B. No global runtime setting changed.
Fixture cap: 12 inference requests; repository cap: the frozen stricter 8.
Both allow at most two model error-recovery cycles, zero transport retries,
15-second commands, 16-KiB command output and 30-minute attempt ceilings.
Batch ceilings remain 90 live minutes, two actual fixture attempts per model,
two repository attempts total, and at most three distinct model configurations.
Configuration changes never reset accounting. Pre-dispatch bootstrap failures
remain recorded separately from actual model fixture attempts.

Read-only sandbox: 2 GiB RAM/no swap, 2 CPU, 152 MiB combined writable tmpfs,
128 PIDs, disabled container logging, no network or host mounts. The controller
alone contacts `http://127.0.0.1:11434`; there is no configured cloud fallback.
Acceptance files are protected. Host job artifacts are bounded at 128 MiB;
resource evidence is separately capped at 8 MiB per attempt. The pinned collector
retains actual candidate bytes and command audit before volatile storage is stopped.
Incomplete evidence never establishes acceptance.

Before loading, require 6 GiB available host RAM. Stop immediately below 2 GiB,
below 3 GiB sustained for 15 seconds, GPU diagnostics failure, or more than
11,776 MiB GPU allocation. Snapshot, controller, inference process and sandbox
memory are measured separately. Offload is allowed; active-parameter count is
not used as a proxy for total weight memory. Only one inference residency runs.

## Strata location recovery and readiness

**Strata installation/runtime/model assets were not located in the searched
locations.** This is not a claim of absence from the whole computer. No Strata
launch, installation, download, driver change or model conversion was performed.

| Item | Verified location or result |
|---|---|
| LAB adapter | This worktree's `localagentbridge/inference.py`; optional, disabled by default |
| Source/documentation records | Existing `data/selective-upstream/strata-*`, `data/selective-blockers-20261008/strata-*`, and `data/installed-models-20261009/strata-*`; snapshots/manifests, not a runnable application checkout |
| Application checkout / installed environment | Not located in searched locations; no verified launchable path |
| Model assets | No complete or partial Coder asset path established; existing Ollama models are not assumed compatible |
| Configuration | Root LAB `config.toml` has no enabled Strata configuration or binding. `examples/selective.toml` is disabled and only illustrates `http://127.0.0.1:8080` |
| Endpoint/process | No actual Strata executable/process found; proxy-free loopback health checks on 8080/8081/8000 did not establish readiness |
| Completed installation evidence | Recovered commands show source/documentation inspection and preparation metadata, not a completed runtime/model installation |

Actual Codex data root was resolved as `%USERPROFILE%/.codex` (CODEX_HOME
unset); its resolved absolute path is retained in the private discovery evidence. The October 8–9 LAB sessions were inspected for relevant tool commands,
including custom calls and their outcomes; other recent sessions were searched
only for Strata tool commands. No unrelated conversation or credential dump was
used. The bounded command/path evidence is in N/strata-session-discovery.json,
strata-path-discovery.json, strata-lab-record-discovery.json and strata-inspection.json.
The search checked LAB's relevant records/worktree/configuration and direct
children of the workspace parent, the data drive software/download/temp roots, user Downloads,
Documents, application/cache roots, and referenced Strata/Hugging Face paths.
There was no whole-drive content/model-binary scan. No record justified a WSL
or container installation-path search. No access-denied limitations occurred in
the recorded path scopes; unsearched locations and older sessions remain outside
this bounded conclusion.

The pinned inspected upstream revision remains
`fb58e0dbc8399662c0e47c76578c6e878b14f6cf`, engine 0.1.41; the separately cached
current MODELS content matched the pinned SHA-256. The proposed Coder IQ1_M
artifacts and full hashes are in I/approval-strata.json (I means
`data/installed-models-20261009/`). That preparation manifest is not installation
proof or authorization. Its proposed package is about 64.4–64.7 GB download,
120 GiB reserved preparation; standard CUDA 13 requires a newer driver, while
the documented CUDA 12 alternative remains unqualified. Actual runtime memory,
complete assets, loaded identity and fit are **unmeasured**. No Strata live
inference or OpenHands-to-Strata qualification is established. Existing Ollama
qualification proceeds independently.

## Batch outcomes and validation

**The exact qwen3.8:27b configuration independently completed and was accepted for the frozen UTC timestamp repository task.** The accepted patch stays in its disposable worktree/artifacts; it is not merged into this development tree or any original checkout.
Human dock, focus and DPI acceptance remain **not tested**; automated checks do
not fill those manual rows. A fixture pass alone never accepts the repository task.

### Hardware and exact model identities

Timestamped N/hardware-before.json (2026-10-09 16:38:43 UTC) records
34,139,435,008 bytes installed system RAM; external RTX 3060, 12,288 MiB VRAM,
driver 560.94, PCI 07:00.0; exact physical UUID retained privately in the hardware evidence.
The internal GTX 1060 Max-Q remains Code 31 (PnP driver 582.66); its live UUID/VRAM
are unavailable through this active driver. Intel UHD 630 is also recorded.
No device repair or pooling was attempted. Available storage was about 143 GB on
the system volume and 2.92 TB on the data volume. No hardware change was made.

| Local tag | Full manifest digest | Verified local metadata (advertisement is not live qualification) |
|---|---|---|
| qwen3.6:35b | a7eb95c53bcf96b4bdd008d0fab4a5dac88047d9c1a7a9ab88ed453423fbd87c | qwen35moe, Q4_K_M, 35,505,251,456 total parameters; parent tag names 35b-a3b. 256 experts / 8 selected; exact active parameter count not independently measured. 22,621,314,381 asset bytes. |
| qwen3.8:27b | aaee06c39dcf2437cde036998d960e1fc1494b8191be7cc9657d01e509097813 | Dense qwen35, Q4_K_M, 27,320,697,856 parameters; 17,741,872,154 asset bytes. |
| gemma4:26b | 001e5dafc3c77684c2307ebc6ab8e336e10c9b18eca52acf547d72fc83c3ca8c | Gemma family, Q4_K_M, 25,233,142,046 total parameters; 128 experts / 8 selected; 18,731,025,629 asset bytes. NOT RUN in this batch. |

Each advertises 262,144 context and tools; the new live Qwen requests instead
verify the explicitly loaded 65,536 context. The existing Ollama 0.40.2 service
and model store were reused without restart. Before/after nine-tag digests and
referenced file inventory are unchanged (N/inventory-before.json,
inventory-after.json, model-before.json, model-after.json). No model-store
addition/removal/retagging was detected in this batch. Normal runtime logs,
transient residency and context/checkpoint caching occurred; they are not model
installation. Existing launcher port-bind warnings were observed; the active
loopback service continued serving requests. Those user-owned launchers were
not stopped or reconfigured.

### Observed comparison

| Model/backend and configuration | Fixture | UTC repository task | Actual attempts / requests / elapsed | Peak whole-host RAM / GPU allocation | Failure class and evidence |
|---|---|---|---|---|---|
| 35B-A3B local tag / Ollama; 65,536 context, 1,536 output, 14 GPU layers | Attempt 1: failed tool-policy recovery; attempt 2: correct retained edit/test, normal collector failed | NOT RUN: full fixture transport not accepted; two-fixture cap reached | 2 fixture attempts; 5 + 6 requests; 309.7 + 337.9 s | 28.65 GiB / 8,682 MiB | Model/tool-policy failure first; controller collection failure second. N/qwen35-fixture-2 and qwen35-fixture-3; retained diagnostic candidate passes independent check, but does not change failed job status. |
| 27B local tag / Ollama; 65,536 context, 1,536 output, 28 GPU layers | Passed and independently accepted | Passed and independently accepted, no Codex repair | 1 fixture + 1 repository attempt; 4 + 5 requests; 372.7 + 507.2 s | 26.24 GiB / 10,530 MiB across its attempts | N/qwen27-fixture-acceptance.json and utc-supervisor-acceptance.json; exact patch and full tool traces retained. |
| Gemma 26B / Ollama | NOT RUN | NOT RUN | 0 | Unavailable | Fallback unnecessary after accepted 27B task; no third configuration loaded. |
| Strata | NOT RUN | NOT RUN | 0 | Unavailable | Runtime/assets/binding not located in searched locations; separate optional lane stays disabled. |

One earlier 2.9-second harness launch failed before creating any job or sending
inference (N/qwen35-fixture-1). It remains recorded and counts toward elapsed
budget, but is not a third model fixture attempt. Total batch: **20 inference
requests across four actual model attempts**, about **25.5 live minutes** including
loading/baseline/cleanup; within every declared attempt and batch ceiling.
No resource stop, device loss, OOM or unexpected CPU-only fallback was observed.
This is a short qualification, not an endurance or eGPU performance certification.

Provider-reported load totals: 35B attempts 76.31 / 75.15 seconds; 27B fixture
59.18 seconds and repository 59.08 seconds. Controller inference intervals include
load, prompt processing and generation: 246.90 / 279.99 seconds for 35B;
318.84 / 445.86 seconds for 27B. Overall elapsed also includes admission,
protected baseline checks, collection, verification and cleanup. These intervals
overlap and must not be added together. Exact samples/counters are in
N/batch-summary.json and per-attempt resources.jsonl/inference receipts.

Local input/output token aggregates: 35B first 30,725 / 326; 35B retry 37,827 / 513;
27B fixture 24,681 / 329; UTC task 41,670 / 442. These are sums across requests,
not individual context sizes. Local cached tokens, attributable Codex cloud
input/cached/output tokens, and phase-specific cloud costs are unavailable.
No cloud savings, quality equivalence or euro estimate follows.

Minimum observed available system RAM: 3.14 GiB (35B first), 4.03 GiB (35B retry),
5.56 GiB (27B fixture), 5.81 GiB (27B repository). Per-process llama-server RSS
peaks: 17,938,862,080 bytes for 35B retry; 15,611,142,144 / 16,062,390,272 bytes
for 27B fixture/repository. The first 35B sampling filter missed llama-server;
only a supplemental snapshot exists, not a complete process peak. Controller RSS
stayed below 81 MB; sandbox cgroup peaks were 409/278 MB for 35B and 275/415 MB
for 27B (rounded upward). Cgroup samples include brief diagnostic exec processes.
These process working sets can share pages; do not sum them as physical RAM.
`ollama ps` records 68%/32% CPU/GPU for 35B and 61%/39% for 27B. GPU UUID/activity
samples and runtime logs jointly establish external-GPU use; `ps` alone does not.

### Review boundary and retained useful patch

The UTC task began from the exact previously frozen source/protected acceptance
at base 0b817c5. The Linux baseline failed the timezone-free case. The local agent
read the actual module and acceptance file, used SDK file_editor to change only
`timestamp`, and ran `python acceptance.py`. It recovered from one denied
directory read; no candidate repair or replacement was provided by Codex.

The retained patch parses once, assigns UTC only to a timezone-free datetime,
and preserves explicit offsets and the existing Z normalization. Codex inspected
the diff and surrounding RolloutReader/counts source. The unchanged protected
suite independently passed in two fresh verification executions: five time cases,
invalid input and unchanged surrounding AST. Ten existing telemetry regressions
also passed on the exact bytes in the disposable repository. No tests were
weakened or skipped. Candidate files and protected baseline hashes are retained.

Exact job/attempt IDs are in N/utc-supervisor-acceptance.json; candidate identity
`92b43c4eb089ce09c047c668874ade25d47ad7be7933ec4101d525e17596b361`;
patch SHA-256 `7ab41b1372c8c45c49ba0faec94f6a412bfdbaff018130c21015d4aa8b874734`.
The exact patch is under N/store/artifacts/<job-id>/candidate.patch, and exact
materialized bytes are in N/qwen27-repository-1/repository. Execution finished,
automated verification passed, then the job durably awaited review until the
separate Codex action accepted that candidate hash. Integration into project
checkouts remains **not done**. The worker had no supervisor acceptance authority.

35B's first attempt read the seed/test but repeatedly attempted directory/shell
operations outside policy; three denied observations exhausted two recovery
cycles. The second attempt received policy-only guidance and generated the correct
fixture, executed the test, and finished six inference requests with no error
recovery cycle. Its normal freeze/collection rejected an unexpected process owner;
strict fallback collection retained its complete tree/command audit and cleanup
later confirmed owned termination/unload. No success was substituted for that
failed terminal state. A fresh independent verifier passed those retained bytes
as a **diagnostic only**; no full fixture qualification or UTC admission followed.

N/collector-observer-race.json reproduces rejection of an explicitly root-owned
diagnostic and successful collection after external Docker stats. The first
reproduction used the default worker UID and was correctly frozen; its cleanup
wait failure and subsequent owned stop are retained separately. The exact original
PID/UID was not captured: an exec/runc transition during concurrent sampling is
suspected, not proven. The qualification harness now observes Docker stats from
outside the namespace. No ownership guard, worker permission, image or production
policy was relaxed. Another 35B fixture run requires a new authorized attempt
budget; it was not silently treated as infrastructure-free extra work.

### Operational result and remaining gates

The approved isolated **27B/Ollama/OpenHands** configuration has one independently
accepted useful task. It is eligible for further explicitly scoped use; it does
not enable general automatic implementation. 35B's full executor path remains
unqualified despite its correct diagnostic candidate. Historical 4B failure is
not a prerequisite or blocker for 27B. Strata remains independently disabled.

The eight-case and narrower pilots remain inactive. Before any activation, review
the prepared per-case protected commands/context and resource fit, measurement
capture and matched starting revisions using the demonstrated 27B settings. One
case does not establish that all eight cases fit or compare quality/cost. Strata
is not required to run an Ollama-only pilot. Human dock/focus checks remain separate
and untested, not blockers for isolated model qualification.


### Rollback and continuation

No new dependency or database schema migration was introduced by this pass.
Optional contract fields have compatible defaults; production expiry is unchanged.
Isolated N/store contains the qualification jobs only. Existing historical stores
and the original checkouts were not migrated or edited. To roll back this pass,
stop its owned work, retain its evidence, and use the previously retained candidate
package/configuration. Do not reset the shared worktree or overwrite unrelated
uncommitted work. No global provider/implementation setting needs reverting.

The accepted UTC patch is intentionally separate from the built infrastructure
package. Review/integrate it later only with new explicit authorization. A future
35B retry must use external monitoring and a new bounded attempt allocation;
repeat the complete fixture before admitting a repository task. Further Strata
preparation needs separate exact asset/runtime approval after locating or selecting
an installation; do not assume the preparation manifest proves an installation.
Human UI checks and any pilot activation remain separately gated.


### Final automated gates

Full Windows source regression: **561 passed, 1 skipped**, 714.07 seconds.
The retained skip requires Windows symlink privileges; it is not a passed manual
check. The 111-case focused run and subsequent 38-case bounded run overlap this
full suite, as do the ten telemetry cases run separately on the accepted patch.
Do not add these counts. Earlier harness collection failure (wrong working
directory importing the old root package) remains N/focused.xml; the correct
candidate run is N/focused-candidate.xml.

Final wheel/sdist hashes, isolated installed subset results, byte equality,
0.4.1 upgrade retention, documentation/lint/source-audit gates and measured
preparation usage are recorded in N/final-package-identity.json,
final-validation.json and preparation-final.json. The final infrastructure
package excludes the separately retained UTC candidate patch.


Installed package subset: **150 passed** (28.24 seconds), all included in the
561-pass source suite. All 553 prior cases remain present; nine cases were added.
Ruff, 45-document checker, 222-file public-source audit (zero findings), Git
whitespace check, wheel/sdist inspection and copied v0.4.1 upgrade retention pass.
All 85 installed package files match reviewed source bytes. Initial documentation
audit findings were resolved by keeping physical/job identifiers in private
evidence; no scan rule was weakened. No global package or dependency was changed.

The accepted 27B live jobs used hashed runtime-1. Final runtime-2 differs only in
optional fixture execution guidance and extraction of the unchanged repair-budget
logic into its tested helper. The 35B retry ran runtime-2; final installed controller
source matches it. Final installed protected-candidate verification is recorded
separately and uses no model inference; it does not retroactively qualify 35B.
The accepted task remains isolated, not included in this infrastructure wheel.

| Component | Current result | Evidence | Remaining blocker |
|---|---|---|---|
| Approved SDK/base | Reused exact installed SDK/tools 1.53.0 and pinned collector; zero new downloads | R/approval-reuse.json; N/executor-binding.json | None for this cached package; no general installation authorization |
| Exact models and GPU inference | Both primary Qwen tags ran with observed RTX 3060 activity and CPU offload; identities preserved | N/inventory-before.json, inventory-after.json, batch-summary.json; per-attempt ps/logs | Limited duration; first 35B RSS peak unavailable |
| SDK tool use / bounded transport | Real reads/edits/tests; 27B complete; 35B second candidate correct but collection failed | Job artifacts; collector-observer-race.json | New bounded 35B fixture run after observer change, with explicit extra attempt allocation |
| Useful UTC task | Locally generated, independently accepted; no Codex repair | N/utc-supervisor-acceptance.json and retained candidate.patch | Isolated review patch; no project integration/commit |
| Independent verification / installed controller | Protected acceptance and ten telemetry checks pass; final installed verification recorded | N/utc-regression.xml; installed-protected-acceptance.json | Passing one task does not qualify other categories |
| Regression/package/upgrade | 561 passed / 1 skipped; 150 overlapping installed cases; quality gates pass | N/final-validation.json, final-package-identity.json | Symlink privilege and fresh-machine/human checks remain separate |
| Resources/storage/cleanup | No safety-stop events; bounded storage and owned stop; no model-store changes | N/preparation-final.json, cleanup.json, model-after.json | Component accounting is not whole-VM physical peak usage |
| Strata | Not located in searched locations; source/preparation records recovered | N/strata-*-discovery.json | Runtime, assets, identity/fit and independent live checks unqualified |
| Dock / comparison pilots | Human checks not tested; both pilots inactive | Grouped manual ledger | Human action and separate explicit pilot activation/preflight |


## Gemma comparison — 2026-10-10

The user authorized exactly one installed-Gemma fixture attempt and one UTC
attempt only after an independent fixture pass, with no fresh Qwen inference.
**Gemma did not independently complete the useful UTC task.** Its first fixture
request was cancelled during model loading after GPU usage crossed the existing
safety ceiling. This is a **runtime/resource stop**, not evidence of poor coding
or malformed tool use. UTC was **NOT RUN**, as required by the prerequisite.
No retry, configuration sweep, substitution or Codex-written candidate occurred.

New private evidence root: workspace `data/openhands-gemma-20261010/` (G).
The attempt ran on 2026-10-10 at approximately 00:33:37–00:35:15 Europe/Berlin
(2026-10-09 22:33:37–22:35:15 UTC). Historical N evidence remains intact.
G/qwen-preservation-before.json and preservation-final.json bind the unchanged
Qwen acceptance records, diff and isolated accepted source.

### Frozen identities and scope

- Gemma: exact installed `gemma4:26b`, family `gemma4`, Q4_K_M;
  digest `001e5dafc3c77684c2307ebc6ab8e336e10c9b18eca52acf547d72fc83c3ca8c`.
  Metadata: 25,233,142,046 parameters, 128 experts / 8 selected, base-model label
  Gemma 4 26B A4B. The label is not a measurement of active memory consumption.
  Installed assets total 18,731,025,629 bytes, including the projector and draft.
  Manifest identities and presence checks are in G/gemma-artifact-manifest.json;
  large model blobs were not rehashed during this comparison.
- Historical Qwen: `qwen3.8:27b`, family `qwen35`, Q4_K_M;
  digest `aaee06c39dcf2437cde036998d960e1fc1494b8191be7cc9657d01e509097813`.
  This compares these installed configurations, not unquantized model families.
- Same Ollama 0.40.2, SDK/tools 1.53.0 and final collector image
  `sha256:b0ec53df107bdbb7b9df9c397ee56d4f7f74bc49d6e6550b16ca6f23e5748090`.
  The controller reused N/runtime-2; all 85 package files match the worktree,
  frozen runtime and existing installed candidate. Retained wheel SHA-256:
  `abbf23dabb615a602047d343524707eb1eedcbe33ce1f44dac5513565360c704`.
  No package installation, image rebuild or runtime code change was needed.
- Both explicitly request native Ollama, 65,536 context, 1,536 output tokens,
  1,024-token safety reserve, temperature 0, thinking false, no truncation/shift,
  120-second keep-alive and no transport retries. Gemma requested 18 GPU layers;
  Qwen used 28. Layer counts differ across architectures and do not imply an
  equal VRAM allocation. This single Gemma setting was not swept or tuned.
- Model defaults were preserved: Gemma top_k=64, top_p=0.95, draft_num_predict=3;
  Qwen top_k=20, top_p=0.95, draft_num_predict=4, presence_penalty=0,
  repeat_penalty=1 and min_p=0. Explicit temperature 0 overrides both installed
  temperature defaults. Different draft mechanisms/settings limit comparability.
- Identical frozen fixture bytes, protected tests, objective, skill version and
  acceptance criteria. The actual SDK system-message and tool-schema hashes
  match Qwen's first requests, recorded in G/frozen-comparison.json. No historical
  solution, candidate, transcript or accepted patch was mounted into the worker.
  The frozen UTC inputs were preserved but never dispatched to Gemma.

### Preflight, admission and stop

Read-only diagnostics confirmed 32 GiB installed RAM (34,139,435,008 usable bytes)
and RTX 3060 12,288 MiB, driver 560.94. The internal GTX remains Code 31; no repair
was attempted. G/hardware-before.json records device identity and timestamps.
Power mode was Balanced. Disk headroom before work was about 133 GiB on C and
2,716 GiB on D. Background Windows, Codex, Ollama launchers and Docker remained
running; background load and file caches were not controlled between dates.

The final collector's real non-inference SDK probe preserved failed-job bytes
and command audit before stopping its sandbox. The protected baseline failed
as intended. External `docker stats` monitoring introduced no diagnostic process
into the worker PID namespace; the process-ownership guard remained enforced.
G/collector-preflight.json, probe-container-inspect.json and storage-enforcement.json
record this check and actual tmpfs exhaustion enforcement.

The actual fixture request was retained in its intent artifact. Replaying that
request through the unchanged adapter **without network dispatch** reconstructs
25,952 serialized UTF-8 bytes plus 1,536 output and 1,024 margin: conservative
capacity bound **28,512 / 65,536**. System bytes 15,473; user bytes 1,308; tool
schema bytes 8,947. This was admitted; it was not a context rejection. Actual
prompt-token count is unavailable because no response completed. No history
compaction or hidden truncation occurred. The separate SDK preflight had a
slightly different diagnostic task ID and a 28,458 bound.

The native endpoint remained `http://127.0.0.1:11434` with no cloud fallback.
Runtime logs confirm `-c 65536`, `-ngl 18`, CPU/GPU offload on CUDA0 RTX 3060,
main-model 18/31 layers and draft-model 5/5 layers on the GPU. The main allocation
was estimated at 11,203 MiB: weights 9,570.05, KV 936 and compute 697.38 MiB.
Draft weights added 425.34 MiB and draft compute 124.50 MiB. Runtime fitting could
not meet its free-memory target with the explicit layer count; the extra-model
memory fitting was incomplete, and loading continued. These logs explain why
weight-size-only or active-parameter estimates would have been insufficient.

The external monitor observed **11,980 MiB GPU use**, above the unchanged
**11,776 MiB** stop ceiling (512 MiB reserve). The controller cancelled the request;
the backend logged HTTP 499 / context cancelled and the owned llama-server exited.
No completed generation, CUDA device-loss or out-of-memory response was observed.
Runtime context initialization was 65,536, but the model never reached a ready
`ollama ps` entry. GPU allocation is not proof of stable inference or tool use.
The test deliberately did not lower the safety reserve or retry fewer layers.

Limits remained read-only root, 2 GiB/no-swap sandbox RAM, 2 CPU, 152 MiB total
writable storage, protected acceptance files, no network/host mounts, disabled
container logging, 15-second commands and 16-KiB output. One fixture / conditional
one UTC attempt, 12 / 8 inference-request caps, at most two within-attempt repair
cycles, 30 minutes per stage and 60 minutes total. The harness additionally
monitored a 64-MiB batch evidence ceiling; the unchanged controller's hard job
artifact bound remains 128 MiB. No limits or approval gates were relaxed.

### Comparison

| Metric | Gemma 26B | Qwen 27B | Comparability / caveat |
|---|---|---|---|
| Configuration / quantization | gemma4:26b Q4_K_M; 65,536 / 1,536; 18 GPU layers; thinking off | qwen3.8:27b Q4_K_M; 65,536 / 1,536; 28 GPU layers; thinking off | Same SDK/image/temperature and protected tasks; architecture, draft and default sampling differences above |
| Independent fixture acceptance | Not accepted: resource stop before first response | Accepted | Gemma's unchanged baseline still fails; no quality judgment possible |
| Independent UTC acceptance | NOT RUN: fixture prerequisite did not pass | Accepted, isolated patch retained | No independently accepted Gemma implementation |
| Codex code repairs | 0; no candidate change | 0 | Gemma generated no patch; neither result includes a Codex replacement |
| Fixture elapsed | 97.748 s, stopped | 372.728 s, passed | Whole stage includes baseline, load attempt, collection and cleanup; not equal completed work |
| UTC elapsed | Unavailable / not run | 507.223 s, passed | Qwen UTC-only time recovered from its original batch record |
| Combined elapsed | No completed two-stage sequence | 879.951 s = 14m39.95s | Qwen's previously reported 9 requests / 14m40s covers both stages |
| Loading | Cancelled before readiness; separate completed load time unavailable | Provider load: 59.180 s fixture + 59.084 s UTC | Empty residency before each stage; OS/file caches not reset or measured |
| Inference / tool / collection time | No completed inference; aborted HTTP interval 59.572 s; first dispatch at +36.157 s; freeze 0.497 s and owned stop 0.543 s | Controller inference 318.839 / 445.857 s, including load; acceptance command 0.032 / 0.175 s | Historical collection and editor timing not separately measured; do not sum nested phase intervals |
| Requests / tool calls / self-correction | 1 dispatched, 0 completed; 0 tool calls / 0 repair cycles | Fixture 4 requests / 5 tool calls / 0 cycles; UTC 5 / 6 / 1 | Qwen UTC recovered from one denied directory view; no malformed calls in retained evidence |
| Reported tokens / throughput | Unavailable, not zero | Input 24,681 / 41,670; output 329 / 442; output 2.505 / 2.153 tokens/s | Backend evaluation durations; different tokenizers and outputs, not primary efficiency measure |
| Host before stage / sampled peak | 12.116 / 21.545 GiB used | Fixture 11.672 / 26.237; UTC 10.294 / 25.982 GiB | Whole-host, different background load; Gemma stopped during loading |
| Minimum available host RAM | 10.249 GiB | Fixture 5.558; UTC 5.813 GiB | No host-memory stop; insufficient basis for memory-saving claims |
| Sampled peak VRAM | 11,980 MiB | 10,530 MiB in each stage | Same physical GPU and total-memory query; Gemma's allocation crossed the stop ceiling |
| Process / sandbox memory | llama-server RSS peak 9.222 GiB; controller 68.5 MiB; sandbox external stats retained | llama-server 14.539 / 14.959 GiB; controller 74.7 / 76.7 MiB | RSS and shared memory are not additive; historical cgroup and new external Docker stats differ |
| Memory pressure / stability | GPU stop; minimum host RAM stayed above thresholds; no device loss observed before cancellation | Neither accepted stage hit memory stops | Windows paging-rate time series unavailable; zero psutil swap I/O is not proof of no paging |
| Energy / throttling | GPU power samples 8.94–32.68 W during observed startup, no energy integration | No matched energy/power series | Whole-system energy and electricity savings unavailable; no sampled thermal-stop evidence, CPU throttling not measured |
| Codex review time | No candidate acceptance review reached; failure audit time not isolated | Active review duration unavailable | Elapsed stage times exclude separate Codex review; full time-to-supervisor-acceptance cannot be compared |
| Evidence | G/comparison-metrics.json, fixture artifacts, failed-candidate-review.json, ollama-server.log | N/qwen27-fixture-1, qwen27-repository-1, accepted records and original receipts | G references retained Qwen data; no new Qwen inference |

No relative speed or memory percentage is calculated: the Gemma run did not
complete equivalent work. Its smaller observed host peak and shorter stopped
interval are not efficiency wins. Provisionally prefer the retained **Qwen27
configuration for this narrowly demonstrated task**, because it has independent
acceptance; Gemma's coding quality and accepted-task efficiency remain unknown.
A future lower-VRAM Gemma configuration would require a new scoped authorization,
new preflight and fixture; it is not proven to fit or succeed. One historical
Qwen success still does not establish repeatability or general quality equivalence.

### Verification, preservation and outstanding work

G/cleanup.json records final execution failed, verification not_run, review
escalated, no accepted hash, stopped owned containers, no inference reservation,
no resident model and retired owned model process. The user's Ollama service
continues running. G/failed-candidate-review.json independently confirms the
retained tree equals the frozen baseline and the command audit is empty.
Missing bytes were not replaced with a generated summary or a success claim.

New automated check: **150 installed selective/security/adapter tests passed**
in 28.89 s with a fresh workspace-owned temporary directory. An earlier invocation
reported 63 passed / 87 setup errors because its default temporary directory was
inaccessible; both logs are retained. These are the same 150 cases, not additive.
The previous full regression remains **561 passed / 1 skipped** and previous
upgrade/package checks remain historical evidence; no runtime source change
required rebuilding or reinstalling. All 85 installed/runtime/source package
files were rechecked byte-for-byte. Documentation, lint, source audit and diff
results are recorded in G/validation.json after the report update.

Only qualification harness/measurement artifacts and documentation changed.
No downloads, dependency installations, model-store mutations or new candidate
implementation occurred. Existing user services wrote runtime logs; OS/GPU
cache writes were not comprehensively traced and are not claimed absent.
G/inventory-after.json and the model before/after comparison show all nine model
identities preserved. Qwen's isolated accepted patch remains uncommitted and
unintegrated; there is no Gemma implementation patch to integrate.

Both pilots, general routing, production defaults/expiry, drivers, networking
and Strata are unchanged. Human dock checks remain untested. Further Gemma
inference requires a new bounded authorization; human UI checks and any pilot or
production activation remain separate decisions. Nothing was committed, pushed,
merged, integrated or published.

Final report gates: Ruff passed, documentation checked 45 Markdown files,
public-source audit checked 222 files with no findings, and diff whitespace
check passed. New local evidence plus scoped test artifacts occupied
5,803,802 logical bytes and 6,113,944 allocated bytes
at the final measurement (G/storage-final.json). This excludes shared Docker
backing-store attribution and filesystem metadata. Downloads and installations
were zero; the existing 64-MiB live evidence stop was never reached.


## Bounded MoE configuration batch — 2026-10-10

This new authorization superseded the preceding one-shot restriction. Historical
failures above remain evidence, including Gemma's loading stop and the earlier
35B collection failure. Private evidence root **M** is workspace
`data/openhands-moe-20261010/`; **N** remains `data/openhands-stronger-20261009/`.
No Qwen27 inference was run. Its accepted UTC worktree and evidence are preserved.

### Candidate and controlled changes

Branch `codex/selective-local-execution`, base
`0b817c572a81a22c94988cdbf163d214957985b7`, remains uncommitted. Codex performed a
small direct bootstrap, not local-agent implementation: `selective_config.py`
and `inference.py` now allow an explicitly configured native Ollama
`draft_num_predict` integer from 0 through 16. Omission preserves the installed
model's existing behavior. Three deterministic cases in `test_selective_bounded.py`
cover validation, native forwarding and omission. No default, expiry, global
runtime option, collector, SDK, dependency or production policy changed.

Pinned [Ollama 0.40.2 source](https://github.com/ollama/ollama/blob/v0.40.2/llm/llama_server.go)
was inspected before use: `appendDraftArgs` returns without adding draft-model
arguments when the option is zero. M/draft-source-investigation.json records
source URLs, revision and SHA-256. This was read-only source inspection, not a
runtime installation. Thinking disabled alone would not disable draft loading.

The live controller imports the immutable, 85-file M/runtime snapshot.
M/runtime-identity.json and harness-identity.json bind source and harness hashes.
The actual executor is the unchanged collector image
`sha256:b0ec53df107bdbb7b9df9c397ee56d4f7f74bc49d6e6550b16ca6f23e5748090`,
OpenHands SDK/tools **1.53.0**, Python **3.13.12**. No old installed LAB bridge,
worker or dock is credited with these scoped SDK jobs. The existing installed
LAB package remains untouched; it differs in the two runtime files above.
The rebuilt wheel was extracted and tested without dependency installation.

### Exact configurations and fitting decision

| Setting | Gemma selected configuration | Qwen35 rerun | Historical Qwen27 |
|---|---|---|---|
| Tag / family / quantization | gemma4:26b / gemma4 / Q4_K_M | qwen3.6:35b / qwen35moe / Q4_K_M | qwen3.8:27b / qwen35 / Q4_K_M |
| Full digest | 001e5dafc3c77684c2307ebc6ab8e336e10c9b18eca52acf547d72fc83c3ca8c | a7eb95c53bcf96b4bdd008d0fab4a5dac88047d9c1a7a9ab88ed453423fbd87c | aaee06c39dcf2437cde036998d960e1fc1494b8191be7cc9657d01e509097813 |
| Total parameters (metadata) | 25,233,142,046; 128 experts, 8 selected; base-model label 26B A4B | 35,505,251,456; 256 experts, 8 selected plus shared expert; installed A3B source label | 27,320,697,856; dense |
| Context / output / temperature / thinking | 65,536 / 1,536 / 0 / false | Same | Same |
| GPU layers / draft option | 16 / explicit 0 | 14 / installed 2, no override | 28 / installed 4, no override |
| Other installed sampling | top_k 64; top_p .95 | top_k 20; top_p .95; repeat 1; min_p 0; presence 1.5 | top_k 20; top_p .95; repeat 1; min_p 0; presence 0 |
| Runtime | Existing Ollama 0.40.2; localhost native API | Same | Same retained version |

Inventory metadata advertises 262,144 context and tools for the two current
models; these are not live guarantees. The tested loaded context was 65,536.
Active-parameter labels are not memory estimates. M/inventory-before.json retains
exact metadata, manifests and asset totals. No model pull, wrapper change or retag.

The first and only new Gemma configuration used measured prior allocation:
draft zero plus two fewer GPU layers (18 to 16). Based on the previous main allocation, draft removal alone appeared too close
to the unchanged ceiling and was not separately tested. There
was no separate model-backed tuning probe or blind sweep. Runtime logs confirm
16/31 main layers, 8,553.34 MiB GPU weight buffer, one loaded model buffer and no
draft launch arguments or draft buffer. M/gemma-draft-absence.json records those
checks. The selected configuration passed its fixture; no remaining tuning
configurations were spent on speed hunting. Context/output were not reduced.

Qwen35 retained its previously tested configuration, including draft generation.
Runtime logs confirm 14/42 layers, 6,910.82 MiB GPU weights, 13,790.11 MiB mapped
host weights, 384 MiB GPU/896 MiB CPU main KV, and an MTP context against the same
model with 128 MiB GPU KV. This is not a second full model weight allocation.
`ollama ps` reported CPU/GPU offload (68%/32% for Qwen35); physical-GPU activity and
UUID in external samples identify the RTX 3060, rather than relying on ps alone.

### Preflight, isolation and admission

M/hardware-before.json reconfirmed 32 GiB installed RAM (34,139,435,008 usable
bytes), RTX 3060 12,288 MiB, driver 560.94. The internal GTX remains unavailable;
no repair was attempted. Balanced power mode, Windows/Codex/Docker and personal
Ollama background processes remained. No devices, network or power settings changed.

Before model requests, M/collector-checks.json exercised actual SDK/container
normal completion, failed-test bytes/trace/diff, cancellation and evidence-limit
failure using a separate synthetic transport. Those were **zero-inference control
probes**, not model qualification. M/timeout-output-controls.json verifies bounded
command timeout/output exhaustion. M/storage-enforcement.json records actual
read-only-root denial and ENOSPC at the configured tmpfs capacities. Wrong-owner
operations were denied. Collection precedes stop on normal and failed jobs;
incomplete collection never becomes success. External monitoring never added a
process to the worker PID namespace. The ownership guard was unchanged.

Sandboxes retained 2 GiB/no-swap RAM, 2 CPU, 152 MiB total writable tmpfs, disabled
container logging, network none, no host mounts/credentials/Docker socket and
protected acceptance files. The trusted host controller mediates only declared
files, bounded editor calls and exact commands; inference uses
`http://127.0.0.1:11434`, without cloud fallback. Host inference is measured outside
the sandbox cap. Controller source retains no-redirect/no-environment-proxy
behavior. No shared service was restarted or reconfigured.

The GPU ceiling remained **11,776 MiB**. Host admission requires 6 GiB available;
hard stop is below 2 GiB, or below 3 GiB for 15 seconds. Each stage allowed at most
30 minutes, 12 fixture requests / the stricter 8 UTC requests, two error-recovery
cycles, 15-second commands, 16-KiB command/output bounds and no transport retry.
The batch allowed 120 live minutes. The overall approved preparation ceiling
remains 2 GiB. A 256-MiB current-batch reservation includes tests, packages and
evidence, with a separate 16-MiB metadata reserve; no evidence was deleted.
M/preparation-reservation.json records the accounting and pre-live reservation.

M/sdk-request-identities.json proves the same SDK system-message and four tool
schemas as the retained Qwen27 run (system SHA-256
`f123e64b8a1394cdd48f4ead76d0e1607498658ba4b24952a4f3dbfe30d11a61`, tool-schema SHA
`ab12adf1ddb841b5541559bda3b842534c28f1c9ae45170055a104cd2e0d517f`). Both new models
received the same existing tool-policy clarification about exact paths/commands;
Qwen27 historically had no extra clarification. It supplied no solution. Frozen
files, task semantics, protected tests, skill version and test visibility matched.
Prior accepted patches and solution-bearing transcripts were never mounted or
included in either model's requests.

Admission counts each actual serialized request, including messages/history,
tool schemas/results and overhead, with the unchanged conservative UTF-8-byte
upper bound, 1,536 reserved output and 1,024 safety margin. No aggregate-token
count is used as per-request context. No hidden truncation/compaction, context
shift or weakened margin was introduced. Native strict context and loaded-context
checks remained enabled. Receipts retain per-request accounting.

### Gemma outcome

The genuine SDK fixture completed 12 requests, actual reads/editor writes/tests
and finish. Only subject.py changed; protected tests passed in the worker,
controller and fresh independent sandbox. Two denied calls (relative editor
path and listing) were recovered within budget; four test invocations were
redundant. Codex reviewed the retained diff/trace and accepted exact hash
`7c6bf489ebd6f25c5fafc06c848760cb990e8793b5e03c57ff0df72d2eb47955`.
M/gemma-g16-d0-c64-fixture-acceptance.json is the authoritative scoped acceptance.

The fresh UTC task **failed and was not accepted**. It read the file, recovered
from a relative-path denial, ran the protected failing baseline and read the
test. The fifth response reached 1,536 generated tokens; backend logs show about
304 seconds for that response. LAB rejected its incomplete completion. No edit
was applied. M/gemma-utc-failure-review.json independently confirms retained
failed-tree bytes exactly equal the frozen baseline. Collection completed,
commands/output and the rejected request's accounting survived, then the owned
executor/model residency stopped. There was no resource stop or context rejection.
The rejected request bound was 41,104 / 65,536, including output and margin.
This is an output-budget/model-behavior outcome for this configuration, not proof
that Gemma cannot code or that MoE cannot fit. No Codex repair or additional UTC
retry occurred. Rejected completion text and full provider token counters were
not retained; the four successful receipts are explicitly partial usage, with
1,536 additional generated tokens observed separately in the backend log.

### Qwen35 outcome and independent acceptance

The fresh fixture completed six requests, with actual read/edit/test calls and
complete collection. The new fixture candidate
`9b78e8fa590e63cb4b28c83591d258331d2f48a4f501bb68a7fb288fd5fb2bfb`
passed the worker, controller and fresh independent verifier. Codex reviewed and
accepted it before the UTC job was dispatched. This resolves the missing
end-to-end evidence for this configuration; it does not retrospectively turn the
old collection-failed attempt into success or prove its transient PID cause.

The UTC task also completed six requests and complete collection. It read source
and protected tests, used the existing SDK think tool, demonstrated the baseline
failure, edited only timestamp(), reran acceptance successfully and finished.
The patch assigns UTC only to parsed values with no tzinfo, preserving aware
values and ValueError behavior. The exact reviewed candidate hash is
`2ff883846f53fb650d6b32755481266b833174293cccaf7529207cb451703685`. Protected Linux tests passed again in a fresh
restricted sandbox; **10 telemetry tests passed** in the isolated candidate
worktree, with the import path checked. Protected files and surrounding AST were
unchanged. There was no Codex code repair or implementation assistance.

M/qwen35-g14-c64-utc-acceptance.json records the authorized supervisor decision,
coverage and exact accepted hash. Execution finished, verification passed,
review accepted and integration remains **candidate**, separately represented.
M/qwen35-utc-disposable.patch and the repository worktree retain the generated
patch for review; neither it nor Qwen27's patch was committed or integrated.
The model's requested 30-second command argument did not expand the controller's
15-second enforced cap. The explicit SDK think tool is distinct from the native
backend thinking flag, which stayed false; its time/tokens are included.

### Accepted work and total qualification cost

All times below are whole controller stages: baseline, loading, inference,
SDK/tool work, collection, automatic verification and cleanup. They exclude the
separately timed Codex review. Whole time to supervisor acceptance cannot be
compared fairly because historical Qwen27 active/review timing is unavailable.
Peak host RAM includes Windows and all processes; GPU is the whole RTX device.
Peaks are sampled lower bounds, not exact allocator maxima.

| Candidate/configuration | Fixture | UTC acceptance | Accepted-work time | Peak host RAM / VRAM | Tuning cost | Failure class or caveat | Evidence |
|---|---|---|---|---|---|---|---|
| Gemma Q4_K_M, 16 layers, draft 0, 65,536/1,536 | Independently accepted | Failed; unchanged baseline retained | Fixture only: 339.231 s; no accepted UTC cost | Fixture 26.672 GiB / 10,693 MiB; failed UTC 23.885 / 10,683 | One config, two stages, 869.478 s; 17 requests | UTC fifth completion hit output allowance; no context/resource/collector failure | M/gemma-g16-d0-c64-fixture-acceptance.json; gemma-utc-failure-review.json |
| Qwen35 Q4_K_M, 14 layers, installed draft 2, 65,536/1,536 | Independently accepted | Independently accepted | Fixture 345.358 s; UTC 630.481 s; combined 975.839 s | Fixture 28.175 GiB / 8,599 MiB; UTC 28.409 / 8,599 | One unchanged config, two stages, 975.839 s; 12 requests | More host RAM and longer UTC execution; lower VRAM | M/qwen35-g14-c64-fixture-acceptance.json; qwen35-g14-c64-utc-acceptance.json |
| Qwen27 Q4_K_M historical, 28 layers, installed draft 4, 65,536/1,536 | Independently accepted previously | Independently accepted previously | Fixture 372.728 s; UTC 507.223 s; combined 879.951 s | Fixture 26.237 GiB / 10,530 MiB; UTC 25.982 / 10,530 | No new inference; retained two-stage cost only | Untuned historical baseline; different background/cache and brief tool guidance | N/utc-supervisor-acceptance.json; qwen27-fixture-acceptance.json |

The new batch used **1,845.316 seconds (30m45.3s)** of the 120-minute ceiling,
including all loading and the failed Gemma UTC work. No extra model-backed probe,
second Gemma configuration, infrastructure retry or repeated UTC attempt occurred.
The old Gemma 97.748-second failed loading attempt is separate historical cost,
not erased or included in this newly authorized batch. Earlier 35B failures
likewise retain their original evidence. Non-inference bootstrap/preflight,
regression and reporting time is separate and is not a model-efficiency claim.

Matching accepted UTC execution: 630.481 versus 507.223 seconds is **24.30% longer**
for Qwen35. Matching combined stages: 975.839 versus 879.951 seconds is **10.90%
longer**. UTC sampled host peak 30,503,813,120 versus 27,897,638,912 bytes is
**9.34% higher**; whole-device VRAM 8,599 versus 10,530 MiB is **18.34% lower**.
These are observed configuration-level differences, not controlled model-family
causal effects. Gemma's failed UTC elapsed/host peak is not an efficiency win.

| Stage | Elapsed s | Provider load s | Requests / tool calls / error observations | Reported input / output tokens | Host before / peak / minimum available GiB | Peak GPU MiB |
|---|---|---|---|---|---|---|
| gemma-g16-d0-c64-fixture-1 | 339.231 | 57.390 | 12 / 12 / 2 | 75,417 / 688 | 10.930 / 26.672 / 5.122 | 10,693 |
| gemma-g16-d0-c64-repository-1 | 530.247 | 58.772 | 5 / 4 / 2 | 28,968 / 199 (partial: 4 completed) | 11.240 / 23.885 / 7.910 | 10,683 |
| qwen35-g14-c64-fixture-1 | 345.358 | 75.421 | 6 / 5 / 0 | 37,827 / 513 | 11.225 / 28.175 / 3.620 | 8,599 |
| qwen35-g14-c64-repository-1 | 630.481 | 75.706 | 6 / 6 / 1 | 57,358 / 1,889 | 11.289 / 28.409 / 3.386 | 8,599 |
| qwen27-fixture-1 | 372.728 | 59.180 | 4 / 5 / 0 | 24,681 / 329 | 11.672 / 26.237 / 5.558 | 10,530 |
| qwen27-repository-1 | 507.223 | 59.084 | 5 / 6 / 1 | 41,670 / 442 | 10.294 / 25.982 / 5.813 | 10,530 |

The two current models and baseline used initially empty model residency at each
stage, without flushing OS/file caches. Provider load time is separately reported
inside stage time. No model was left competing with the next one. Tokenization,
response lengths and speculative decoding differ; tokens/second cannot select a
winner. Qwen35's accepted UTC output throughput was 6.581 tokens/s versus Qwen27's
2.153, yet its complete UTC execution took longer, including its long think call.
Gemma's incomplete fifth UTC response is absent from the four successful receipt
counters; its backend log separately records 1,536 generated tokens and 304.037 s
of prompt/generation. Full rejected-request input/usage remains unavailable.

Controller inference intervals, including load, were fixture/UTC: Gemma
264.604 s / 176.638 s for completed receipts only (UTC excludes the failed final
response); Qwen35 281.345 / 570.283 s; Qwen27 318.839 / 445.857 s. Per-command
outputs/exits and elapsed times remain in worker-result or failed-commands.
New collection freeze/read/stop phase timestamps are in controller-phases.json;
these include nested intervals and repeated mailbox reads, so must not be added
as independent stage costs. Historical collection/editor overhead was not
separately measured. Exact tool and verification timings are retrievable there.

Error observations are the enforced bounded-recovery counter, not necessarily
bad generated patches. Gemma fixture had two denied calls; UTC had one denied
relative path plus the deliberately failing pre-edit test. Qwen35 fixture had
zero and UTC had one pre-edit failing test. Qwen27 historically had zero/one
(denied directory view). No malformed accepted tool call was observed; Gemma's
incomplete response is recorded separately. Neither accepted Qwen UTC patch
needed Codex repair or a model repair of incorrect implementation code.

The same admission bound spans were 28,827–34,252 (Gemma fixture),
28,841–41,104 (Gemma UTC including rejection), 28,804–31,580 (Qwen35 fixture),
and 28,818–46,369 (Qwen35 UTC). All include the output reservation/margin and fit
65,536. Per-request actual token receipts remain distinct from cumulative usage.
No capacity rejection occurred in this batch.

New sampled intervals averaged about 8.9–9.5 seconds including external Docker
statistics, versus about 4.0 seconds historically. Different monitor overhead,
background load, file caches, sampling defaults, model quantizations and the
small policy-guidance difference limit the comparison. Host before/peak values
above are not model-only allocation. Peak llama-server RSS was Gemma 15.178 /
12.434 GiB and Qwen35 16.706 / 16.903 GiB; Qwen27 was 14.539 / 14.959 GiB.
RSS/shared memory must not be added to whole-host or GPU totals. New controller
peaks were 73.9–78.3 MiB; sandbox peaks about 256–274 MiB, separately measured
against its enforced 2-GiB cap. Host inference exceeded some planning estimates;
measured stop guards, not those estimates, established observed headroom.

No current stage hit GPU/host stops, device loss or a transport failure. Qwen35's
minimum available host RAM was only 3.386 GiB in UTC, versus Qwen27's 5.813 GiB;
its host-memory margin is smaller despite lower VRAM. Windows paging rates are
unavailable: psutil's zero swap-I/O fields do not prove no paging. Balanced power
mode was unchanged; GPU power/temperature/raw clock-reason samples and process
CPU observations are retained in M/resource-detail.json. CPU throttling and a
matched historical power series were not established. Existing duplicate
personal Ollama launchers emitted bind warnings; the selected service stayed
reachable and no unrelated service was terminated.

GPU-only instantaneous power is not whole-system energy. Energy, electricity
cost, cloud input/cached/output tokens and Codex token savings remain unavailable.
No quality-equivalence or savings claim follows. Recorded review wall intervals
were 42.212 s for Gemma fixture, 28.930 s for Qwen35 fixture and 63.132 s for
Qwen35 UTC, from explicit inspection through fresh checks/acceptance; they are
not active CPU time or cloud-token cost. The historical comparison lacks this
measure, so those durations are not folded into a misleading relative total.

Both Qwen configurations met the same acceptance standard on this one task.
Provisionally prefer the retained **Qwen27 configuration for similar scoped
work on this hardware**: shorter accepted UTC execution and more host headroom.
Qwen35 is a separately demonstrated alternative when lower VRAM matters, with
higher host use and longer observed task time. Gemma now has a safe, accepted
fixture configuration but no independently accepted useful UTC implementation.
Further Gemma changes would be a new scoped experiment, not a reason to relax
acceptance or imply MoE is unsuitable. None of these single runs establishes
repeatability, general quality equivalence, production routing or pilot readiness.

### Validation, preservation and next actions

New bootstrap validation: **564 passed / 1 skipped** in the full source suite
(734.37 s; Windows symlink privilege skip), **41 focused bounded cases** and
**153 extracted-wheel selective cases** (29.73 s). The focused and wheel cases
overlap the full suite; never add them. The separate 10 telemetry tests above
were run against the accepted isolated UTC candidate and are not another full
suite. Three new cases cover the optional draft setting; no prior tests were
removed. Actual copied v0.4.1-wheel database seeding and candidate migration
preserved usage/checkpoints. M/bootstrap-validation.json records exact scopes.

The tested wheel SHA-256 is
`89c27489900befa6fa14ea7f245b5ed438ab439544cf9d34bd697599e3d14960`.
It contains the same 85 byte-identical package files as source and live runtime.
No package/environment was installed. M/final-package-identity.json records the
report-final source manifest/sdist and lint/docs/audit/diff gates, distinct from
the prior installed package. Runtime was not altered during owned execution.
Rollback is to omit the new optional setting/use the prior retained wheel;
no new database schema migration was introduced by this bootstrap. No rollback
or installation was performed against the user's working service.

M/cleanup.json verifies stopped owned executors, released inference reservations,
empty model residency, preserved nine-tag identities/model-store snapshots,
unchanged original checkouts and byte-identical accepted Qwen27 evidence/patch.
The personal Ollama service remains running. Only persisted qualification
configuration records remain; temporary request overrides ended with their owned
jobs/residencies. Logs and OS/GPU caches may have incidental runtime writes;
no model-store mutation was detected, and cache writes were not comprehensively
traced. M/storage-final.json gives measured current-batch preparation/evidence
allocation under the unchanged reservation; no retained evidence was deleted.

Both pilots, general implementation routing, production defaults/expiry,
networking, drivers, global Python and Strata remain unchanged. All human dock
checks remain outstanding. The feature/bootstrap/report changes and both accepted
Qwen UTC patches are isolated and uncommitted; nothing was merged, integrated,
pushed or published. Any future Gemma retry/tuning, pilot activation, global
routing, integration or publication needs separate authorization. No additional
installation is required for the exact scoped Qwen35 path just demonstrated.
