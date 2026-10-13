# Selective local execution implementation report

## Serving-patch qualification — 2026-10-13

**A and B passed with the LAB-specific serving patch. The unchanged RAM guard
then stopped the owned runtime; C and deliberate live safety checks did not run.**
This demonstrates one bounded inference and one durable LAB advisory, not a
qualified OpenHands/Strata implementation path or safe general Strata routing.
The latest owner amendment was applied from clean local/remote **e5a3a7e**;
no newer work or uncommitted edits were reset. Active **a9a4bad/Ollama** remains
unchanged. Main is still **f6df420**, latest release **v0.4.1**; work is published
only on the development branch and draft PR #1.

| Component | Implemented | Fresh live verification | Enabled | Published where | Remaining work |
|---|---|---|---|---|---|
| LAB v0.5 / dock | Existing orchestration and controls preserved | 89 frozen e5c6337 package files match checkout runtime; no new human UI checks | Active a9a4bad/Ollama | Development branch / draft PR #1 | Human ledger and merge gates |
| Strata serving | One-file fail-fast patch over pinned source | One native 0.1.43 CUDA 12 start; exact imports/processes/weights checked | Test-only, now stopped | Sanitized patch/tests below; private runtime | Resolve RAM growth before another attempt |
| LAB → Strata advisory | Existing MCP/store/worker/adapter | One correlated advisory succeeded and Codex accepted its text | Test-only provider restored to disabled | Development report / PR | This is bounded advisory evidence only |
| OpenHands → Strata | Existing restricted SDK/mailbox adapter | C not dispatched after RAM stop | Disabled/unqualified | Existing development code | Memory admission, protected fixture and review |
| Ollama / OpenHands | Existing qualified paths | No new inference; Qwen27/Qwen35 fixture and UTC results reused | Existing project configuration | Active installation and earlier reports | No new performance/qualification claim |

### Exact modified identity and offline review

Runtime label: **Strata 0.1.43 engine with LAB-specific serving patch**.
Two exact patch revisions are distinguished below; only the first was loaded.
Native engine, dependencies, model data and original upstream bytes were not
modified. The separate source copy contains 2,976 source files; only
`serve/server.py` differs. Full upstream MIT attribution is retained in
[STRATA-LICENSE.txt](qualification/STRATA-LICENSE.txt).

- Upstream base: `7695859aa13afb248bdb4d36f9b2e95707db079d`.
- Original server SHA-256: `55ee9d1160f0da457cabe6f9dfea9884296b6d70fd3d14abd4ed42e6f79dd72b`.
- [Live-tested patch](qualification/strata-serving-tested.patch) SHA-256: `f680795863739a005113a96ea3d6ce496a40222b9b9e3f50b20e65e27e0199f2`.
- Resulting server SHA-256: `87072ef429bcfbf009ba9989bcd09f578b4f4b88d008b2b05377cbb506f86078`.
- [Live-tested provenance](qualification/strata-serving-tested-provenance.json),
  [strict reproduction helper](../scripts/strata_serving_patch.py) and
  [offline tests](../tests/test_strata_serving_patch.py).
- Qualification launcher SHA-256: `151815d1e065bd2f08a4903b875651e0e6609e451d1c3b2c66c79d08bc49df4f`;
  effective config SHA-256: `8f5b843910db86f142940d5195950afa7c1953c481cd290adf0e0bb624cc07be`. Private manifests retain exact paths,
  argv, process creation times and all 286 binding artifacts. The binding includes
  base commit and patch/result hashes separately; the engine's stock version
  string is not presented as unmodified serving-source identity.

**Final offline correction:** post-run protocol review found upstream's
`cancel` → `stop` mapping. Although LAB disconnects withheld those responses,
that mapping could present a server-side cancellation as normal completion.
The final [patch](qualification/strata-serving.patch) rejects queued/mid-response
cancellation with explicit JSON/SSE errors before finalizing partial content or
tool calls, retaining cancellation history and cleanup. Its SHA-256 is
`3a0ca878f80c66e26c26b429e00db71ccb3c9febcc34056728602ee996d05190`; resulting server SHA-256 is `670a36ec733fadfd0880035180e1345483ea21576a90b3501b807d68209d39f0`, recorded in
[final provenance](qualification/strata-serving-provenance.json). A second isolated
source copy preserves the exact earlier live-tested bytes. The final 286-artifact
candidate manifest is disabled, has no live process identities, and cannot pass
admission. **No live start followed this correction** because the RAM stop had
already occurred; A/B evidence below applies to the preceding exact patch only.

The patch rejects the first non-finite result, including partial output and
`DONE nonfinite` received during STOP/drain. Native detection remains enabled.
A locked process-wide allowance permits one initial native start; `restart` and
`ensure_loaded` refuse resurrection. HTTP errors, SSE errors/`response.failed`,
cleanup and cancellation remain; failed partial tool calls are withheld by LAB.
Qualification config explicitly disables reasoning-close retry, reasoning-loop
recovery, tool-call recovery, lazy loading, replicas, runtime MCP, vision,
API monitor, context fitting and prompt/conversation caching. No native code changed.
LAB transport retries and SDK `num_retries` are zero; SDK streaming remains false.
Successful budgeted tool-loop turns are separate requests, not failure retries.

The live-tested revision passed **34 offline tests** (21.33 s), including normal and first/mid-response
failures across Chat Completions, Responses and Messages, streaming/non-streaming,
LAB rejection, partial tools, cancelled/disconnected requests, real Python child
startup failure/death and counted no-respawn checks. **49 unchanged upstream
regressions passed** (31.03 s), including tools, usage, disconnect and silence
cleanup. Upstream tests expecting replay/restart are intentionally replaced by
the new assertions, not falsely reported as unchanged passes. These fake-engine
results are distinct from live model qualification. No weights were corrupted. The final correction passed **41 offline tests**
(35.35 s), including cancellation errors over all six HTTP route/stream combinations
and zero-start queued cancellation. The same **49 unchanged upstream regressions passed again** (31.14 s)
against that final copy; validation results below distinguish revisions.

### Preparation, stages and measured stop

Zero downloads and **no repeated packing**. The two isolated source copies add
**96,484,158 logical / 107,637,904 allocated bytes** on D:. The existing
1,485,311,220-byte direct pack is reused, not additional disk in this amendment.
A private pre-packaging evidence snapshot measured 233,868,038 logical bytes;
final validation/evidence allocation is recorded in the close-out manifest.
Fresh full verification checked all
6,840 existing source/dependency/model/MTP files in 403.245 s. The existing direct
pack was independently rechecked in 17.058 s: all dense bytes/index rows, tokenizer,
48 expert rows and references to both approved shards. The quarantined incomplete
pack stayed untouched. Actual native process open files/mappings contained both
approved GGUF shards; the engine log selected second-shard PLE and mmap experts
with no `experts.bin`. Actual CUDA libraries and serving import path were checked.

| Stage / check | Actual result |
|---|---|
| A startup | One engine start; ready in **52.7 s**, context 16,384; exact native/PLE files and 286-artifact binding verified |
| A bounded inference | **Passed**, `READY`; max 64 output tokens, 120 s request / 600 s attempt, no replay. 36.139 s including identity checks; provider 20 input / 2 output tokens, 0 cached |
| B LAB advisory | **Passed** through real `companion_contract_submit` MCP → durable job → existing independent worker → Strata. 66.107 s including submission; 56.801 s worker/admission interval; 122 input / 34 output tokens, 0 cached |
| B correlation/review | One additional server request; job/attempt, exact binding, server/engine identity, timestamps and token counters agree. Codex accepted one relevant test suggestion without correction; no model-authored code |
| C restricted OpenHands fixture | **Not dispatched**: RAM stop invalidated its prerequisite. No candidate edits, tool round trip or protected acceptance result |
| Deliberate live failure / cancellation | **Not run** after the unexpected resource stop; offline tests are separate. Guard-triggered termination is not a completed cancellation qualification |

| Fresh live interval | Peak summed owned-process RSS | Minimum available host RAM | Peak whole GPU |
|---|---:|---:|---:|
| Startup through readiness | 7,273,971,712 bytes | 15,550,148,608 bytes | 9,790 MiB |
| A request and identity checks | 11,766,378,496 bytes | 10,854,604,800 bytes | 9,970 MiB |
| B / subsequent guard stop | **20,046,356,480 bytes (18.67 GiB)** | **2,512,232,448 bytes (2.34 GiB)** | **10,036 MiB** |

Samples cover the whole owned server tree and host/GPU. Available RAM stayed
below 3 GiB for **15.606 s**, triggering the unchanged sustained-pressure guard
at **661.5 s after launch**, after the successful advisory had completed.
The hard 2 GiB floor and 11,776 MiB GPU ceiling were not crossed. Startup 600 s,
request 120 s, one inference, 2,048 MiB engine VRAM reserve, native/mmap mode,
loopback-only endpoint and all other limits were retained. No other process was
terminated or model unloaded to create headroom.

Before B, the isolated cap changed from absent/**Medium** to **Maximum** as
already approved. A-based Strata admission planning reserved **31,789 MiB** of
32,557.9 MiB, including measured runtime rounded up with an extra GiB, a separate
GiB for context, 512 MiB LAB, 2 GiB Docker-host allowance, 2 GiB sandbox and 3 GiB
headroom. **That plan proved insufficient as mmap residency grew during B**;
it is not valid C admission evidence and is no longer enabled. B/C resolved
budgets were recorded before dispatch: **8 steps, 1,536 output tokens / 16 KiB,
16,384 context, 120 s/request, 600 s/attempt, 1 attempt, 0 transport retries,
0 self-repair cycles, 15 s tests, 2 GiB/no-swap sandbox and 2 CPUs**. None increased.

### Restoration and remaining decision

The test store shares neither mutable settings nor admission state with the
active installation. Its original absent cap row was restored (effective Medium),
and original config bytes restored, disabling its Strata provider and removing
the temporary memory plan. The completed advisory and review evidence remain.
No test inference reservation remains. The first shutdown snapshot still showed
two children exiting; later independent PID/create-time checks confirmed all
owned identities gone and port 8080 absent. Shared Ollama, active configuration,
settings, job states and defaults remained unchanged. Docker was unavailable and
was not started; no OpenHands web application or other installation occurred.

Another live start needs a **new decision following this measured RAM failure**:
a source-reviewed way to bound native mmap working-set growth within the same
physical limits, or a separately approved hardware/resource change. Neither is
implemented or presumed viable here. Do not restart unchanged, tune repeatedly,
raise limits, disable guards or enable routing. The existing B/C and isolated
Maximum approvals need no duplicate permission if a new approved plan satisfies
their prerequisites. Keep the reusable verified pack and original source.

### Final source validation and publication checks

Final source regression: **655 passed / 1 skipped**, 731.64 s; the skip is
Windows developer-mode symlink support. This includes the 41 final optional
Strata tests. The earlier 648/1 run (716.82 s) used the live-tested patch and is
retained as earlier evidence, not added to the final count. The 49 upstream
checks are a separate external suite; repeated runs are not additive coverage.
Ruff, generated documentation, 46 Markdown files, 343 local links, 64 anchors,
43 source-map symbols and the 239-file public-source audit passed. Both published
patches apply cleanly to the exact base; the helper reproduces final bytes.

Wheel/sdist inspection, separate non-editable install, v0.4.1 retention checks,
archive identities and exact published-commit CI are recorded in the private
close-out and [draft PR #1](https://github.com/nishdel/OmniLAB-Local-Agent-Bridge-/pull/1).
Installed checks overlap the source suite. No private configuration, database,
raw session log, weight or personal path is included in the published material.
All eight README/workflow Mermaid blocks are unchanged; prior eight local and
six GitHub renders are reused evidence, with **no fresh visual-render claim**.
The eleven human checks remain two incomplete and nine untested.

## Direct-GGUF amendment outcome — 2026-10-13

Historical preparation/retry-policy stop; superseded by the serving-patch qualification above.

**Preparation passed; stage A stopped at a source-verified retry-policy
incompatibility before server startup. Strata remains disabled and unqualified.**
The owner approved the one direct-GGUF attempt and conditional test-store
Maximum cap at `7cbaa117fac2913c2fa6a7246f711a5489fe1503`. Neither approval is
missing. No new download, model inference or runtime modification occurred.

| Component | Implemented | Freshly verified | Enabled | Published where | Remaining work |
|---|---|---|---|---|---|
| LAB / dock | Existing v0.5 and Strata adapter | 89 isolated runtime files match reviewed e5c6337 and 7cbaa11 source | Active a9a4bad/Ollama unchanged | Development branch / draft PR #1 | Human acceptance |
| Strata preparation | Same 0.1.43 CUDA 12 / pinned dependencies and Coder weights | All 6,840 input hashes; complete direct-GGUF pack independently checked | Files only; no server/profile | Private installation; sanitized report in PR | Safe serving retry policy, loaded identity |
| LAB → Strata advisory | Existing adapter / durable jobs | Not dispatched | Disabled | Development branch / PR | Stage A, measured admission plan, then B |
| OpenHands → Strata | Existing restricted SDK/mailbox path | Not dispatched | Disabled | Development branch / PR | A/B, protected fixture and independent review |
| Ollama / OpenHands | Existing qualified paths preserved | No new inference; earlier Qwen27/Qwen35 successes reused | Existing project configuration | Active a9a4bad and development branch | No new qualification claim |
| Main / release | Separate older implementation | Remote main remains f6df420; latest release v0.4.1 | Unchanged | Default branch / release | Human/review/merge gates |

### Fresh preparation evidence

The clean checkout and published development head both began at **7cbaa11**;
no newer work was reset. The reused non-editable LAB wheel is
`15ff00b806600d8f13db336d9d7109234cc65067e58bf1cb2ebbbf1610de1499`.
Imports resolve to that isolated installation, not the older workspace root or
active a9a4bad package. Input verification freshly hashed both source exports,
serving dependencies, both complete main GGUF shards, and raw/generated MTP
assets: **6,840 unique files in 420.674 seconds**. Exact upstream commits, engine
and weight identities are retained in the historical installation section below.

The pinned `tools/iq_pack.py --gguf <first-approved-shard> --out
<fresh-pack-direct-gguf>` ran once, **without `--experts-bin`**. The fresh directory
was absent before launch, contains nine files, no expert copy or partial output,
and cannot fall through to the quarantined pack. Independent checks verified:

- All **1,475,120,640 dense bytes** against the original tensor spans; **1,079**
  index rows and **302** native quantized tensors, offsets, shapes and padding.
- **48** native expert rows, **256** experts per layer and **25,146,163,200**
  referenced expert bytes in the first approved shard; no converted extra data.
- Both freshly hashed shards and their metadata; the second shard's
  `per_layer_token_embd.weight` requires explicit `--ple-gguf`. Source selection
  with `experts.bin` absent is verified; **actual engine file selection is not**,
  because no engine was started.
- Token IDs, token types, vocabulary, merge ordering and template against GGUF
  metadata. Dense SHA-256:
  `99853263806e25450074fc9945f1e955b175bea05aa171ceeb6b5837bf6a1d9d`;
  native expert table SHA-256:
  `9ace1b92e1fe12595de469409e69dd52c8d5418c7981c405d9a51aa9d574dd3b`.

| Fresh operation | Elapsed | Peak summed owned-process RSS | Minimum available host RAM | Peak whole GPU |
|---|---:|---:|---:|---:|
| Full input hash verification | 420.674 s | 37,957,632 bytes | 22,476,906,496 bytes | 361 MiB |
| Single direct-GGUF preparation | 13.981 s | 1,771,102,208 bytes (1.65 GiB) | 20,003,127,296 bytes (18.63 GiB) | 361 MiB |
| Independent pack validation | 12.472 s | 135,970,816 bytes | 22,499,262,464 bytes | 361 MiB |

These are sampled process-tree and system measurements, not inference peaks.
The owned Windows job and descendants stayed within two CPU affinity slots.
All owned processes exited. Admission/stop limits remained 6 GiB / 2 GiB hard /
3 GiB for 15 seconds, 11,776 MiB whole GPU and 900 seconds per preparation step.
New pack disk: **1,485,311,220 logical / 1,485,321,080 allocated bytes** on D:,
measured per file with Windows FileStandardInfo (excluding directory metadata).
Private qualification evidence before regression added about 3.4 MB. No payload
was downloaded. The previous incomplete pack's paths, sizes and mtimes are unchanged.

### First compatibility stop and staged result

At pinned Strata commit `7695859aa13afb248bdb4d36f9b2e95707db079d`,
[`Service.run`](https://github.com/Niko1221/Strata/blob/7695859aa13afb248bdb4d36f9b2e95707db079d/serve/server.py#L3917-L3933)
reissues generation once when non-finite logits occur before any output. There
is no inspected configuration opt-out for that retry. The separate
`reasoning_close_retry=false` option does not control it.
[`ensure_loaded`](https://github.com/Niko1221/Strata/blob/7695859aa13afb248bdb4d36f9b2e95707db079d/serve/server.py#L3000-L3043)
can also call `restart`, whose default allows three starts. LAB transport retries
of zero cannot prevent these server-side actions. Disabling the NaN guard would
weaken safety and was not attempted. A polling monitor cannot reliably prevent
an in-process replay that has already begun.

Three existing upstream `NonFiniteLogits` tests were run offline with their fake
engine: first-token failure retries once, mid-reply failure does not replay,
and two failures end in error. **3 passed in 0.196 s** (0.916 s process interval),
confirming the conflict; they are not live inference or deliberate backend-failure
qualification. The inspected server SHA-256 is
`55ee9d1160f0da457cabe6f9dfea9884296b6d70fd3d14abd4ed42e6f79dd72b`.

| Stage / check | Actual result |
|---|---|
| Preparation | Passed once; independent pack validation passed |
| A: startup, loaded identity, initial 64-token inference | **Blocked before startup** by the unchanged runtime's retry behavior; zero live requests |
| B: durable LAB advisory | Not dispatched; no job/request correlation or usage exists |
| C: restricted OpenHands implementation | Not dispatched; no candidate, model-authored edit or protected test result |
| Representative live backend failure | Not run; offline source diagnostic above is separate |
| Live cancellation / inference termination | Not run; no generation existed to cancel |

The first unexpected compatibility finding stopped further model execution.
No controller or sandbox was launched. Stage A's authorized 600-second startup,
120-second request / 600-second attempt, zero retries, 64-token initial probe,
16,384 context / 1,536 response ceiling, native/mmap mode and 2,048 MiB engine
VRAM reserve remain unchanged and **unexercised**. B/C budgets were not dispatched
or relaxed. No measured Strata loading/inference plan can yet be established;
the copied Ollama memory plan remains explicitly unverified.

### Isolation, cleanup and next decision

The new qualification data directory and companion SQLite file are physically
distinct from the active installation. It has no inherited mutable settings,
jobs or inference reservation. Compute cap belongs to `telemetry.Store` in
`data_dir/usage.sqlite3`, separately from companion admission state. That test
file was never created; the effective original and final cap are **Medium**.
Conditional Maximum authorization remains valid after A passes, but was never
used. The original test configuration is byte-identical; no restoration write
was needed. Active configuration hash, settings and job states are unchanged.
No owned process, port-8080 listener or test reservation remains. Shared Ollama
stayed running without unloading a model or terminating another application.

A new decision is required only for a **reviewed fail-closed serving change**:
retain the pinned native engine/dependencies/weights and NaN detection, reject
the first non-finite result, and prohibit automatic engine restart. Review and
offline failure tests must precede a newly authorized single Stage-A attempt;
rebind the changed serving source hash. This is outside the approved unchanged
runtime scope. No patch, new version, guard relaxation or restart was applied.
The approved direct pack can be reused; repeating preparation is unnecessary.

Private reproducible receipts are `verified-inputs.json`,
`direct-packing-result.json`, `model-pack-verification.json`, per-stage host/process
logs, `upstream-retry-diagnostic.json`, `unexpected-stop.json` and `closeout.json`.
Only this sanitized summary is public. Codex performed the authority-sensitive
preparation/review; the intended local advisory was blocked, not replaced with
Ollama or cloud inference. No token-saving claim or human acceptance is made.

Validation and publication results are recorded with this amendment in draft
PR #1. The README/workflow Mermaid blocks are unchanged: earlier eight local
renders and six GitHub renders are reused evidence, not a fresh graphical check.
The existing eleven human checks remain two incomplete and nine untested.

## Approved Strata preparation — 2026-10-13

Historical first attempt; superseded by the direct-GGUF amendment outcome above.

**The exact approved runtime and raw assets are installed; main expert packing
hit the unchanged RAM stop. Strata remains disabled and unqualified.** No model
was loaded, no inference was attempted, and no stage A/B/C or live generation
cancellation result is claimed. The prior LAB/Ollama deployment is unchanged.

### Starting point and installed identity

The owner authorized isolated preparation and bounded qualification of the
[exact e5c6337 package](SELECTIVE-SETUP.md#concrete-optional-installation-approval-package),
not general activation. The development checkout and remote both remained
`e5c6337717be4df285c2817732efde5cf7b38a51`; PR #1 was open/draft. The older
workspace root is not the Git checkout. Main remains
`f6df420181f21856cb421619e2c1310f6cf46685`, latest release v0.4.1.
Existing edits and the qualified Ollama models/configuration were preserved.

| Component | Implemented | Live verified in this follow-up | Enabled | Published where | Remaining work |
|---|---|---|---|---|---|
| LAB v0.5 / dock | Existing durable jobs, controls and adapter | Isolated e5 runtime imports/tests; no new human acceptance | Active a9a4bad deployment retained | Development branch / draft PR #1 | Human ledger and review gates |
| Ollama advisory / OpenHands | Existing qualified paths retained | No new inference; earlier Qwen27/Qwen35 results remain historical | Existing project settings | Development branch / draft PR #1 | No new general quality claim |
| Strata runtime / assets | Exact approved installation completed | Engine version/help, small CUDA operation, hashes, metadata and MTP pack | No server or runnable profile | Private installation on C: and D:; public evidence summary in PR | Main preparation, loaded identity, A/B/C |
| Strata LAB adapter | e5c6337 implementation retained | Mocked provider tests only | Disabled; no qualification bypass | Development branch / draft PR #1 | Actual tool/SDK round trip and live cancellation/failure |
| Main / release | v0.4.1 | Historical scope | Separate from development | Default branch / release | Human acceptance, review and merge; no release authorized |

All **64,664,303,372 approved payload bytes** were retrieved and verified against
the pinned manifests. Transfer retries/HTTP overhead are not extra unique assets.
No one-click installer, driver change, administrator install, global Python/PATH
change, service, firewall rule, autostart, cloud inference or model substitution
was used. Installed components are:

- Core `strata.exe`, `strata-vision.exe` and `BUILD.json` under
  `%LOCALAPPDATA%/StrataLAB/0.1.43` on C:. Engine 0.1.43 CUDA 12 archive SHA-256
  `344998f7b91af0b028e8e5241db39bbc5abd9c93a0a33d6dbc33108bb8a837fb`;
  executable SHA-256 `5f359e2d08e73b11fd7b0edc72652125c12f836394dbf1732cec0d461324cd6b`.
- Source, CPython 3.13 isolated venv, 18 pinned wheels, models, caches and generated
  data under `LocalAI/StrataLAB/0.1.43` on D:. Strata source
  `7695859aa13afb248bdb4d36f9b2e95707db079d` (2,976 checked blobs); llama helper
  `3cf03257f219afbe7334045ff7c6a06ac68c627d` (3,608 checked blobs). CUDA runtime
  12.9.79 and cuBLAS 12.9.1.4 are process-local dependencies; driver stays 560.94.
- Coder revision `5348543e0147355ac9cbcb031184a3546350988e`: two GGUF v3 shards,
  **58,408,584,928 bytes**, full SHA-256 values
  `e11083ba855e7666b48ea3f2db6a9c3a20c18751a012cc24f948de91b7087fad` and
  `316b46f3a2dbd68c900f43136ab9449f9dcc3725dfd8c794847c204bc161e113`.
  Actual metadata: `qwen4exp`, Qwen3.8-Flash-Next GSQ-RCO Coder, 48 blocks,
  256 experts / 10 active, embedding 2560. The IQ1_M filename describes a mixed
  quantization, not uniform one-bit tensors. All 1,224 tensor spans fit the files.
- MTP revision `de4b8e4d43b917e7706784d8bb445c9af86a3540`: 31 tensor inputs,
  **5,214,301,696 bytes**, all pinned hashes checked. Generated Q2_0 MTP GGUF
  SHA-256 `a22206a4d74eafbf31063a84610292535fb3b49af9a339963817fd04aed81e4d`.
  Independent checks compared all 512 expert blobs, 29 dense tensors and 30
  sampled Q8 blocks. Main tokenizer vocabulary/merges/types/template comparisons
  and six small round trips passed; none proves model tool behavior.

The installed Ollama 35B-A3B model remains `qwen3.6:35b`, qwen35moe / Q4_K_M;
its [earlier exact inventory](SELECTIVE-SETUP.md#independent-strata-status) is
retained. It was neither replaced nor mistaken for the Flash-Next weights.

The isolated LAB installation actually exercised was the reviewed e5c6337 wheel,
SHA-256 `15ff00b806600d8f13db336d9d7109234cc65067e58bf1cb2ebbbf1610de1499`.
All **89 runtime files** equal that source and imports resolve to its isolated
environment. It has separate configuration, job storage and evidence. The active
LAB remains the **a9a4bad** wheel
`df9b041c8198213b9237078e39fe71ff18e7c6e55112c771ee7d516f88db2429` (88 files).
The active configuration hash remained
`51809e7f341aea8f6c10f64400da6a7374d75491c48c32bf46dea015ed999f35`.
The copied Ollama memory plan was explicitly unverified for Strata.

### First failed prerequisite, resources and cleanup

Pinned `tools/iq_pack.py --gguf <first-approved-shard> --out <isolated-pack>
--experts-bin` stopped after **352.18 seconds**. The LAB host guard observed
**1,721,860,096 bytes (1.60 GiB) available RAM**, below its unchanged 2 GiB hard
reserve. Observed peak individual packing-process RSS was **20,378,791,936 bytes
(18.98 GiB)**; GPU use peaked at **358 MiB**. The wrapper failed; its recorded
child return code of zero after owned cleanup is **not** successful packing.
The source constructs each layer with memory-mapped arrays and concatenation;
these observations do not prove a leak or an inference-memory requirement.

| Preparation operation | Result | Elapsed | Observed process RSS peak |
|---|---|---:|---:|
| 2-by-2 cuBLAS SGEMM on existing RTX 3060 | Passed; exact result, buffers freed, owned process exited | 1.18 s | Small CUDA probe; not a model load |
| MTP quantization | Output independently verified | 731.63 s | 4,730,978,304 bytes |
| MTP runtime layout | Passed and independently verified | 6.73 s | 1,404,751,872 bytes |
| Main expert copy | **Stopped by hard RAM guard** | 352.18 s | 20,378,791,936 bytes |

A private monitor initially raced the successful MTP process exit and reported
`NoSuchProcess`. Its original receipt was preserved; the completed artifact was
independently verified, the monitor was corrected, and quantization was not
repeated. That monitor race is distinct from the real later main-packing RAM stop.

Unchanged limits: 6 GiB admission reserve, 2 GiB hard / 3 GiB for 15 seconds
sustained reserve, whole-GPU ceiling 11,776 MiB, two CPU affinity slots during
packing, 900-second packing-step deadline. Planned inference stays one job,
16,384 context, at most 1,536 output, zero retries; no inference limits were used
to claim a measured pass. Hardware: 34,139,435,008 bytes RAM, i7-8750H AVX2,
RTX 3060 12,288 MiB, SATA data SSD.

The owned packer exited. Read-only checks found no remaining Strata/packing
process, no port-8080 listener, no active inference reservation and no queued or
running active LAB jobs. The shared Ollama service was retained, with no model
loaded at cleanup. Available RAM recovered to **23,182,364,672 bytes**. No active
configuration restoration was necessary because it had not changed.

All incomplete files were preserved under `data/pack-incomplete-20261013` in the
approved Strata directory; the planned `data/pack` path is absent. Its partial
`experts.bin.tmp` is **17,845,452,800 bytes** and is not a usable pack. Raw weights
and verified MTP outputs are retained. No serving identity was created.

At cleanup, C: core files occupied **396,791,058 logical / 396,796,184 allocated
bytes**. D: Strata files occupied **86,670,324,113 logical / 86,689,630,672 allocated
bytes**, including the quarantined partial pack and retained download assets.
Private LAB/evidence added about 38 MB. Allocation is summed per file using
Windows FileStandardInfo, excluding directory metadata. Free disk was about
140.86 GB on C: and 2.821 TB on D:. These are measured partial-install totals,
not a successful serving footprint or a loading estimate.

### Staged outcome and next action

| Stage | Result | Required next gate |
|---|---|---|
| A: loaded identity + bounded inference | **Not run: preparation failed first** | Explicit retry amendment, complete/verify native pack, safe owned startup and identity |
| B: LAB durable advisory through Strata | **Not run**; no job/request correlation exists | A plus scoped admission authorization; one useful bounded advisory |
| C: restricted OpenHands → Strata → edits/tests → review | **Not run**; no local-agent patch | A/B, measured memory plan and supervisor-controlled qualification fixture |
| Live generation cancellation / representative backend failure | **Not run** because readiness was not established | Owned live runtime and confirmed terminal/reservation cleanup |

The smallest retry proposal uses the **same pinned upstream native-GGUF path**:
omit `--experts-bin` when preparing a fresh pack; retain `--native` and
`--mmap-experts`. Pinned `iq_pack.main` returns after the dense/index/tokenizer
outputs in that mode; `FileExpertSource::open` selects `open_gguf` when
`experts.bin` is absent. This avoids the **25,146,163,200-byte** expert copy.
See the [concrete amendment](SELECTIVE-SETUP.md#bounded-retry-amendment-after-the-ram-stop).
It has not been run here and does not establish safe loading or output quality.
No larger RAM/GPU allowance, new artifact, model substitution or driver change
is proposed. The owner's explicit instruction to stop on resource failure
requires an amendment before another full preparation or loading attempt.

A later independent admission gate remains: `selective.execute` requires the
Strata compute cap to be **Maximum**, while the isolated test resolves Medium.
Authorization to change only that test-store cap is pending; active defaults and
all physical/context/output ceilings would remain unchanged. No cap was changed,
profile pre-qualified or admission rule bypassed. General activation remains a
separate later decision: suitability has **not** been demonstrated.

### Validation and handoff

Installed e5 package checks: **114 passed** (overlapping source tests). Pinned
upstream protocol suite: **23 passed with mocked engines**. Neither is live
SDK/Strata evidence. Fresh Windows source regression: **614 passed / 1 skipped**
(Windows symlink support), `python -m pytest -q`, 703.41 seconds. Production
code, tests and scripts are byte-identical to e5c6337; this follow-up publishes
seven Markdown files only.

Ruff, generated CLI/config references, **46 Markdown files / 323 local links /
58 anchors / 43 source symbols**, and the **232-file public-source audit** passed.
The first publication audit caught absolute installation paths in new prose;
they were generalized before the passing audit. No audit rule was relaxed.
Wheel/sdist contents were inspected; a fresh offline wheel install passed **114
overlapping checks**, and a disposable v0.4.1 upgrade retained usage and its
checkpoint. The tested follow-up wheel SHA-256 is
`f6fc55bc079b8772f39c2c56d8b0c5afc24c86198d393310837f95415203d3f8`;
all 89 runtime files equal the e5 runtime actually used for preparation.
It did not replace that test runtime or the active controller.

All **eight Mermaid blocks parsed** with the existing local Mermaid 11.12.2.
Each is byte-for-byte equal to e5c6337. Rendering evidence is explicitly reused:
eight prior local pixel inspections, plus six prior actual GitHub-renderer
inspections covering both README and all four workflow diagrams. No new graphical
inspection is claimed in this follow-up; no private source/evidence was uploaded.
The detailed sequence remains dense at fitted width and supports GitHub zoom.

Publication is through `codex/selective-local-execution` and
[draft PR #1](https://github.com/nishdel/OmniLAB-Local-Agent-Bridge-/pull/1), whose
opening summary records the latest preparation result. The exact published SHA
and corresponding Windows CI result are verified there and in the private
publication receipt. A queued check is not a pass. Main/default-homepage README,
release v0.4.1 and the existing human review/merge gates remain unchanged.

The [single guided owner session](MANUAL-RELEASE-TESTING.md#strata-follow-up-one-guided-owner-session--2026-10-13)
retains every acceptance criterion and the [eleven-row human ledger](release-testing/selective-execution-issue-draft.md).
No new human observation occurred. Earlier widget launch/some selection evidence
remains partial; persistence, displayed live identity, progress, errors,
cancellation, telemetry and retained-control acceptance remain open. Dependent
Strata steps cannot run while preparation is blocked.

Private reproducible evidence is retained as `model-downloads.json`,
`mtp-downloads.json`, `mtp-pack-verification.json`, `tokenizer-precheck.json`,
`lab-build-identity.json`, `model-packing-result.json`, resource JSONL, original
logs and `preparation-failure-cleanup.json`. Those local files, configuration,
databases and weights are excluded from publication. Installation, ownership,
resource diagnosis and final review were direct Codex work; the planned bounded
LAB/Strata advisory was blocked before execution. No new model-authored
contribution or token-savings claim is made.

<a id="strata-upgrade--2026-10-12"></a>
## Historical adapter upgrade — 2026-10-12

**At the e5c6337 checkpoint, adapter/configuration work was delivered; Strata
was not functional or enabled.** Stage A stopped at missing runtime/compatible assets. No Strata
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
