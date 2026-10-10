# Live selective-execution qualification

Current bounded stronger-model evidence: [qualification report](OPENHANDS-STRONGER-QUALIFICATION.md). Earlier results below retain their original scope.

## Scoped OpenHands qualification — 2026-10-09

This pass supersedes the installation, adapter and model-safety status below.
Evidence is retained in workspace `data/openhands-scoped-20261009/` (N);
I and B below remain historical evidence. Source stays on the existing worktree
and base `0b817c572a81a22c94988cdbf163d214957985b7`. Only the explicitly approved
174-artifact OpenHands package was downloaded; no models or base images were
pulled. The comparison pilots, Strata and production implementation remain inactive.

| Area | Current result | Evidence and limits |
|---|---|---|
| Approved dependencies | **Installed, verified** | 174 exact artifacts / 101,666,057 bytes; SDK/tools 1.53.0. Accounted disk upper bound 1,164,693,186 bytes < 2 GiB reservation. |
| Model store | **Protected; no unexpected mutation in this pass** | Owned NoPrune server; read-locked Qwen-only view; zero copied large weights. Five view setups add expected hard links only. Original/converted GPT assets retained; GPT requires reassessment. |
| Sandbox/SDK | **Live verified** | Read-only root; all tmpfs limits reached ENOSPC; fixed mailbox transport, actual SDK editor and context checked. Default unsupported quota still blocked. |
| Exact model/context/hardware | **Live verified at 32,768** | Qwen3.8 digest `aaee06c39dcf2437cde036998d960e1fc1494b8191be7cc9657d01e509097813`; RTX 3060 12,288 MiB, driver 560.94, Windows 19045 / 32 GB RAM. 65,536 attempt failed the RAM guard. |
| Fixture and review | **Accepted; disposable integration passed** | Four real calls: terminal read, file_editor edit, terminal test, finish. Independent baseline failed / candidate passed; awaiting-review state preserved before exact Codex acceptance. |
| Recovery/cancellation | **Live verified within stated scope** | New controller recovered the same real SDK pending mailbox; owned cancellation confirmed, zero provider dispatches, reservation released. Active first-run model process was stopped by the RAM guard. No token-stream resumption claim. |
| Regression / installed artifact | **523 passed / 1 skipped; 112 overlapping installed checks passed** | Separate source and installed counts are recorded below; they overlap. |
| Remaining activation | **Blocked / not tested as applicable** | Category/general reliability, comparative savings/equivalence and human focus/DPI are not established. Strata deferred; comparison pilots and production implementation inactive. |


### Approved preparation and bounded adapter

The approved manifest SHA-256 is
`9c8d3c4f9ddcde56f223028ccdbc2d65e50c575758a9a9062d2167a9a077f8d9`.
Its reviewed fields matched the previous proposal. All **174 exact artifacts**,
**101,666,057 bytes**, passed their recorded source/checksum checks. SDK and tools
are **1.53.0**, source `54daf056bd863bb46f922a2fe9324dd736b37ff6`.
They were installed offline with `--no-index --no-deps --require-hashes` in a
private container prefix, with no cache, bytecode or global Python changes.
`pip check`, imports and exact version inventory passed. Existing cached base:
`sha256:fd4b2c1255e1daac21e1a6b4dae0e21d77cc943c74ea193452f4f004d415ca39`.

Installed prefix allocation was **408,236,032 bytes**; successful build writable
snapshot **408,248,320 bytes**; new compressed SDK layer **95,518,219 bytes**.
Downloads, retained build snapshot, committed unpacked layer, compressed layer,
small failed/adapter layers and conservative metadata reserves total an upper
bound of **1,164,693,186 bytes**, below the approved **2,147,483,648-byte** reservation.
The bound counts the shared base once as pre-existing. It is component accounting,
not an exact whole-VM physical high-water measurement. Temporary extraction used
enforced 768 MiB RAM tmpfs with no swap; the initial 256 MiB tmpfs failed with
ENOSPC before installation. No disk extraction copy, BuildKit cache or image export
was made. `preparation-footprint-final.json` retains the distinction between
artifact bytes, lock-file overhead, allocator accounting and volume free space.

The opt-in `readonly_tmpfs_v1` profile keeps the root filesystem read-only and
uses bounded `/workspace` 64 MiB, `/tmp` 32 MiB, `/state` 32 MiB, `/exchange`
16 MiB and `/dev/shm` 8 MiB mounts. Nonzero allocation reached **ENOSPC at every
limit**; root and device-file creation were denied. The original unsupported
containerd quota path still fails closed. Agent containers have no network,
host mounts, model store, host credentials, LAB database, GPU devices or Docker
socket; no capabilities, no privilege escalation, 128 PID ceiling, bounded CPU/RAM,
and no Docker log growth. The controller alone performs safe discovery and
inference over loopback; the SDK sees only a fixed mailbox Chat Completions relay.
Controller artifact writes have a separate aggregate 128 MiB limit.

Transport uses fixed root/worker seeding phases and seals directories before
execution. Completion/results are collected durably while tmpfs is alive; stopped
tmpfs is never restarted or treated as a result. Verification checkpoints bind
files, contract, image and attempt-specific path, keeping candidate verification
separate from integration checks. The actual SDK's reasoning field is preserved
and translated to Ollama 0.40.2's `reasoning` wire field. Optional sampling/context
settings are validated; loaded context is checked after each complete response
before any proposed tool call reaches the SDK. Production defaults are unchanged.

The first actual run exposed SDK editor sibling-temporary-file creation in a sealed
directory. The final adapter retains SDK editing, history and encoding logic but
uses an exact-file, no-follow write on the already permitted worker-owned inode.
Directories remain mode 0555; authoritative files remain root-owned/read-only.
A real SDK editor probe passed and denied unrelated/authoritative-file writes.
This write is deliberately non-atomic inside the disposable snapshot: a crash may
leave partial candidate bytes, which must be discarded or independently verified.
No host/original file is edited by this extension. The immutable ToolDefinition
construction error and all preliminary probe failures are preserved in N.

### Ollama side effects, protection and retained identities

The binary was `ollama.exe` **0.40.2**, SHA-256
`9eaec399fd941073f8ddfbd56e0447f77fca5c006b26b8b1874a7fb12719b2a0`.
The earlier owned `serve` PID **5520**, guardian **18384**, started with
`OLLAMA_NOPRUNE=false`; at **13:29:11.314 +02:00** it logged two unused blobs removed
from a count of 55. No deleted identities or sizes were logged, and no complete
pre-prune blob inventory was retained. Their identities, byte loss and restoration
cannot be established. Calling them unused reflects the runtime's reference scan,
not independently established permission to delete them.

Later owned PID **22252**, guardian **20768**, ran with pruning disabled. The first
GPT-OSS request at **13:31:59.574 +02:00** preceded compatibility migration start
at **13:32:00.397**, completed **13:36:28.683**. Pinned
[0.40.2 migration code](https://github.com/ollama/ollama/blob/v0.40.2/compatmigrate/migrate.go)
and the log support a load-triggered background conversion. Its overlap with later
screening is a performance confound. No GPT-OSS load occurred in this pass.

| GPT-OSS identity | Full SHA-256 |
|---|---|
| Original screened API manifest, retained | `17052f91a42e97930aa6e28a6c6c06a983e6a58dbb00434885a0cf5313e376f7` |
| Current selected llama.cpp manifest | `9ba9cc2b4e02463b933096090530aef679d534dd91ecc9afadfb2dbfdc59f3c5` |
| Original weights, retained | `e7b273f9636059a689e3ddcab3716e4f65abe0143ac978e46673ad0e52d09efb` |
| Converted weights, retained | `8ecb5d4ad6172c63f9cbf1a07a04e525985a8a11a6e516da02b674c4010de716` |
| Original wrapper hash (old bytes not retained) | `0779c8db9e8123241fe1774cef8538450857c4354c52d8a9bf6d8733d719378c` |
| Current wrapper | `772f45cc11275c34238da8c5d8242967395a0e0a25d2d8e3aa87ca1bceb9acf1` |

The old 859-byte manifest still hashes exactly to its original identity. Both weight
files are GGUF, with **459 tensors**, equal type/dimension multisets and unchanged
file-type metadata; tensor names and architecture keys changed (`gptoss` to
`gpt-oss`), and `tokenizer.ggml.pre` changed from `default` to `gpt-4o`. Declared
quantization remains MXFP4. Template, parameters and license blobs are unchanged;
config and manifest metadata changed. Only bounded headers were inspected
(13,791,789 / 13,792,479 bytes), not tensor payload equivalence or model quality.
A digest change alone does not establish corruption or equivalence.

Apparent sizes are **13,793,422,144 / 13,793,422,816 bytes**. Windows
`FileStandardInfo.AllocationSize` reports **13,793,423,360 bytes each**, with distinct
file identities and one link each: the converted asset is a separate allocated
copy. The net historical volume delta remains unknown because pruning sizes and
other concurrent changes were not recorded. `gpt-oss-forensics.json` contains the
full manifest/blob reference graph, config identities, headers and allocation data.
Both variants remain reachable from the current GPT wrapper/list; the converted
variant also has a llama.cpp alias. Neither weight is an unreferenced cleanup candidate.

Pinned [NoPrune parsing](https://github.com/ollama/ollama/blob/v0.40.2/envconfig/config.go)
confirms `OLLAMA_NOPRUNE=1` on the owned server disables startup pruning; it does
not disable conversion or metadata writes. Each new server used a Qwen-only private
view: small metadata copies and hard links to existing weights, **zero new large
weight data**. Read handles deny writes/deletion through source and view names;
private directory ACLs deny new children and directory handles prevent renaming.
Original store ACLs and personal Ollama settings were untouched. A disposable
probe verified read success and denied write/create/delete/rename. Real optional
metadata-cache writes were denied by the protection during inference.

Snapshots include manifests, blob inventories, file identities, small-file hashes,
allocation and free space before/after startup and each attempt. Expected hard-link
count changes during view setup are recorded separately. This is protection against
ordinary runtime writes, not a security boundary against a malicious host user
rewriting ACLs. The agent has no host-store access. All source and converted assets
are retained. N/GPT-OSS-RECOVERY-PROPOSAL.md separately explains possible original
selection recovery, incomplete wrapper rollback evidence, repeated-migration risk,
reference-aware cleanup prerequisites, and unknown pruned-blob recovery. Nothing
in that proposal was executed. GPT-OSS requires reassessment; historical results
remain bound to the original digest.

### Live fixture, supervisor decision and final validation

The first attempt used 65,536 loaded context and exposed the sealed-directory
SDK write mismatch. A fourth request was in flight when physical RAM stayed below
2 GiB for three samples; the Windows Job guard closed only its owned server/runner.
Three completed receipts and the uncertain fourth dispatch are retained. This is a
**failed capacity/adapter attempt**, not a model-quality failure. No model mutation
was observed. The orphaned reservation was explicitly reconciled after the exact
server process identity was confirmed dead; no uncertain response was replayed.

The **one corrective execution** used the same two-file fixture, exact model,
8-step / 1,200-output-token limits and no generation deadline. Only the execution
configuration changed: repaired SDK file-write adapter, explicitly assessed
**32,768 context**, and a tighter **1,024 MiB / 2 CPU** sandbox. A fresh private
qualification record links the previous failed job; the ordinary contract correction
API does not mutate an existing contract's resource limits. These are exactly two
fixture executions, not a restarted comparison campaign or extra model sweep.

Actual final SDK requests measured **27,529–29,468 UTF-8 bytes**, conservatively
below 32,768 even after reserving 1,200 output tokens. Provider prompt counts were
**6,385 / 6,522 / 6,683 / 6,823**, and each receipt verified `/api/ps` context
**32,768** before tool delivery. Runner logs reported `truncated = 0`; requirements,
tool results and reasoning history remained in the serialized requests. The initial
non-inference 27,552-byte SDK diagnostic used the earlier boundary fixture;
no model ran that diagnostic. The live fixture reuses an existing disposable Git
baseline (`312c0b1343eabff1bb6c72cbb2693e774f5921fc`) rather than creating a commit.
It requires changing `subject.py` from `x=1` to `x=2`, with authoritative `check.py`
outside worker edit authority. This is a minimal compatibility fixture, not a
complex coding or quality benchmark.

The corrected run completed in **427.86 seconds**, with four
provider intervals totaling **365.13 seconds** and **323
reported output tokens**. Minimum available system RAM during that fixture was
**3.70 GiB**; peak GPU use **10,160 MiB**, leaving
**2,128 MiB** VRAM. These are measured headroom observations, not promises for larger
tasks or concurrent workloads. The final owned server PID was **22648**, guardian
**11520**, bound only to 127.0.0.1:11435. Its protected-view identity and source hashes
are recorded in `protected-runtime-5/ownership.json`; the personal server on 11434
was not restarted or stopped. The final guard closed with no failures.

Actual candidate SHA-256:
`f72007c9c65b7d89ec0c22de8f5763658701207567ebb4784dd81042720c7bde`.
Only `subject.py` changed, including SDK normalization of its CRLF to LF. Codex
inspected that patch, both source files, actual successful editor/tool observations,
and authoritative baseline-exit-1 / candidate-exit-0 checks. LAB first retained
`awaiting_review` with no accepted hash; Codex then accepted the exact candidate.
Fresh combined integration checks passed before copying only those reviewed bytes
into N/live-fixture. Its Git HEAD did not change and no commit was made. Private
review-harness newline assertions initially rejected the CRLF baseline; evidence
and original bytes were rechecked before acceptance. A temporary fixture-local Git
setting change was restored before integration; no personal/global Git setting changed.

Final image:
`sha256:55a41aeb84f1e9b7cbc06fc7fc27864b6e34f76101d04019d8fef6c834ab4e7c`.
The active controller used the hashed `runtime-source-3` snapshot; its imported
paths and hashes were recorded before job ownership and it was never upgraded
while running. `sdk-dependency-identity-final.json` confirms all 174 installed
versions and both executor assets match. Live receipt/review/integration details
are in `live-result-2-before-review.json`, `supervisor-acceptance.json`,
`disposable-integration.json`, and `sdk-control-result.json`. Private model views
and all historical evidence remain retained. No generated model-view cleanup was run.

The final full source suite passed **523 passed / 1 skipped** in
**711.84 seconds**. All **509** prior cases are present and
nonfailing; the unchanged skip is the Windows symlink privilege condition.
There are **15 added regression cases**, covering reasoning/context
validation, storage/resource drift, stopped-tmpfs rejection, artifact budgets and
attempt-specific verification recovery. Real process/lifecycle tests remain in the
full suite. **112 tests passed against the non-editable candidate**;
these overlap the source suite and are not added to it. The first isolated installed
harness lacked the existing PyWin32 bootstrap paths and failed collection; after
adding those existing dependency paths, the complete installed set passed. No extra
dependencies were downloaded or globally installed to resolve that harness issue.

Ruff, documentation checking, public-source audit (218 files) and whitespace checks
passed. Wheel/sdist contents were inspected; **84 installed package assets** match
source and wheel exactly. Wheel SHA-256:
`92185269dfab4f678680056599b2213f7b63a908110ab4f4f10fe5e83808b09a`.
The final source manifest and sdist hashes are in N/final-package-identity.json.
The final executable bytes equal those in the accepted live controller snapshot;
only documentation changed afterward. A separate fresh 0.4.1-to-candidate install
rehearsal preserved seeded usage and checkpoint rows, with a retained pre-upgrade
backup; existing companion/schema/history regression checks also passed. The
original environments and historical evidence were not upgraded in place.


The source, original development and original release heads remain unchanged;
both original checkouts remain clean. Personal model tag identities match the
pre-pass inventory. No production default, personal Ollama setting, driver,
Docker-engine/WSL/network configuration, release publication, commit, push or merge
was changed/performed. Human focus, keyboard/DPI, responsiveness and fresh-machine
acceptance remain **not tested**; the manual table is not marked passed by automation.


The complete historical sections below remain unchanged evidence for their own
candidate identities and dates; their earlier "not installed" status is superseded
only by this scoped pass. One fixture does not establish general coding reliability,
Codex token savings, category qualification, or equivalence to Codex-only results.

## Installed-model follow-up — 2026-10-09

Current evidence is in workspace `data/installed-models-20261009/` (I below).
The previous blocker evidence remains in `data/selective-blockers-20261008/` (B).
This section supersedes earlier inventory and regression status, while preserving
all earlier evidence. The source remained on `codex/selective-local-execution`,
base `0b817c572a81a22c94988cdbf163d214957985b7`, with its existing uncommitted
changes. This pass changes qualification documentation only. Runtime code,
production defaults, model selection, role/skill mapping and both pilots remain
unchanged. No SDK/dependency installation, image/model pull, driver change,
production integration, commit, push, merge or publication was performed.

### Regression and executable provenance

The complete source run passed **508 passed, 1 skipped in 1,060.23 seconds**.
All **225** cases from the prior 222-passed/3-failed run are present and passed;
they are a subset, not an additional count. The skip remains the Windows symlink
privilege condition. `regression-summary.json` checks case identity and confirms
no source changes during execution. Runtime providers in these automated tests
are synthetic; the separate model screen below is live.

Tested source allowlist manifest:
`48f05aec20a8d2a9f78b8ad0711ab882db906a1ef0e6159084c42ac196bbddb8`.
All executable package bytes, including MCP server, controller/worker, executor,
runner and dock, match the installed wheel exactly. The earlier line-ending-only
difference is absent: no normalization was needed. The retained final wheel is
`localagentbridge-0.5.0.dev0-py3-none-any.whl`, SHA-256
`42de265e805c4b2216f40cb5db5bea5f6fe238275f45eccf49b26768785c4233`.

The final installed-wheel run passed **97 passed in 82.23 seconds**, outside the
checkout, using copied current tests and isolated state. Imports resolve to the
non-editable candidate environment, not an older release or the source tree.
These 97 tests overlap the complete source suite. An initial copied-test run
had 96 passes and one missing `prepare_selective_pilot.py` fixture file; the
entire 97-test set was rerun after copying that unchanged script. The failed
harness run is retained and is not represented as a product regression.

The 15-second fixture lease changes only crash-test allowance. A fresh installed
store diagnostic advances only that process's module clock: reserve succeeds
just before the stored expiry; reserve, result and finish reject at expiry and
immediately after it; recovery retains 15 seconds spent and hands off as
interrupted. No sleep, stored-expiry edit, production timeout change or assertion
relaxation was used. These six boundary assertions are not added to pytest counts.
See `deterministic-expiry.json`. Final documentation, audit and source-distribution
identities are recorded in `final-package-identity.json`.

### Installed inventory and controls

Ollama CLI/server **0.40.2**, Windows 10 Home **19045**, **34,139,435,008 bytes RAM**,
external **RTX 3060 / 12,288 MiB / driver 560.94** were rechecked. Exact device
identities and current free memory/storage are retained privately. The internal
GTX 1060 Max-Q remains Code 31 with assigned 582.66; only the RTX is available to
NVIDIA inference. Its VRAM was never pooled with the GTX.

I contains `/api/tags`, `/api/show` for all nine exact tags, complete templates,
parameters, context ceilings, architecture metadata and full digests. The
reported names, short IDs and disk sizes below are retained verbatim. Actual
local byte sizes are separate; neither is peak memory usage. Eight current local
manifest wrappers have a different file hash from the API digest: each references
an original-manifest blob whose SHA-256 equals that API digest. The 4b-instruct
manifest itself equals its API digest. All referenced blobs exist with the
reported sizes. This verifies identity binding and presence, not a fresh hash
scan of every large weight file. `local-manifest-bindings.json` records both levels.

| Exact tag | Reported short ID / disk | Full API digest before inference |
|---|---|---|
| qwen3.8:27b | aaee06c39dcf / 17 GB | `aaee06c39dcf2437cde036998d960e1fc1494b8191be7cc9657d01e509097813` |
| qwen3.6:35b | a7eb95c53bcf / 22 GB | `a7eb95c53bcf96b4bdd008d0fab4a5dac88047d9c1a7a9ab88ed453423fbd87c` |
| qwen3.5:9b | 56671c2ab938 / 6.6 GB | `56671c2ab9385f9cfcb404638e32cd62d88e3501d44822208363c010179a3c90` |
| gpt-oss:20b | 17052f91a42e / 13 GB | `17052f91a42e97930aa6e28a6c6c06a983e6a58dbb00434885a0cf5313e376f7` |
| qwen3:14b-q4_K_M | bdbd181c33f2 / 9.3 GB | `bdbd181c33f2ed1b31c972991882db3cf4d192569092138a7d29e973cd9debe8` |
| qwen3-vl:4b | 1343d82ebee3 / 3.3 GB | `1343d82ebee38e26a4dd6b0180b915eb91550184e67c505dea97509571c8f683` |
| qwen3-embedding:8b | 64b933495768 / 4.7 GB | `64b933495768fbd3b87c20583d379728a07471e0c66733a9df87cd1901b3c44b` |
| gemma4:26b | 001e5dafc3c7 / 18 GB | `001e5dafc3c77684c2307ebc6ab8e336e10c9b18eca52acf547d72fc83c3ca8c` |
| qwen3:4b-instruct | 0edcdef34593 / 2.5 GB | `0edcdef34593eac1aa2be9c7d06c432dcf81945adca5eca2f27662c18f168ba0` |

GPT-OSS changed after its screen through automatic runtime migration; its new
digest is recorded under side effects below and is **not** qualified by this run.

| Exact tag | Architecture / parameters / quantization | Local bytes | Metadata context ceiling | Advertised capabilities |
|---|---|---:|---:|---|
| qwen3.8:27b | qwen35 dense; 27.3B; Q4_K_M | 17,741,872,154 | 262,144 | completion, vision, tools, thinking |
| qwen3.6:35b | qwen35moe MoE (256 experts, 8 used); 35.5B; Q4_K_M | 22,621,314,381 | 262,144 | completion, vision, tools, thinking |
| qwen3.5:9b | qwen35 dense; 9.0B; Q4_K_M | 6,550,825,550 | 262,144 | completion, vision, tools, thinking |
| gpt-oss:20b | gptoss MoE (32 experts, 4 used); 20.9B; MXFP4 | 13,793,441,244 | 131,072 | completion, tools, thinking |
| qwen3:14b-q4_K_M | qwen3 dense; 14.8B; Q4_K_M | 9,276,198,565 | 40,960 | completion, tools, thinking |
| qwen3-vl:4b | qwen3vl dense; 4.4B; Q4_K_M | 3,295,636,135 | 262,144 | completion, vision, tools, thinking |
| qwen3-embedding:8b | qwen3 dense; 7.6B; Q4_K_M | 4,676,805,193 | 40,960 | tools, embedding |
| gemma4:26b | gemma4 MoE (128 experts, 8 used); 25.2B; Q4_K_M | 18,731,025,629 | 262,144 | completion, vision, tools, thinking |
| qwen3:4b-instruct | qwen3 dense; 4.0B; Q4_K_M | 2,497,293,803 | 262,144 | tools, thinking, completion |

Qwen3.8 supports local thinking values false/low/medium/xhigh (default medium);
GPT-OSS supports low/medium/high (default medium). Qwen3.6, Qwen3.5, Gemma4,
Qwen3-14B and Qwen3-VL report true/false with default true. The 4b-instruct tag
advertises thinking but its show response does not enumerate controls; no
control value or qualification was inferred. Embedding metadata advertises a
tools capability too, but it has no completion capability and was excluded from
chat/tool-use tests. Vision and embedding assets remain retained.

Qwen3:4b-instruct is not the earlier qwen3:4b identifier; no prior acceptance was
transferred. A new digest, template, reasoning setting, client or runtime version
requires reassessment. The upstream [Qwen3.6 model card](https://huggingface.co/Qwen/Qwen3.6-35B-A3B),
[Qwen3.8 model card](https://huggingface.co/Qwen/Qwen3.8-27B),
[GPT-OSS documentation](https://developers.openai.com/api/docs/models/gpt-oss-20b)
and [Gemma overview](https://ai.google.dev/gemma/docs/core) were reviewed as
architecture/control references, not proofs of local artifact equivalence or
coding correctness. The Qwen3.5, Qwen3-14B, VL, embedding and 4B-Instruct upstream
cards were also inspected; installed metadata governs this pass.

### Predeclared small screen and independent review

`screen-plan.json` was saved before inference. The same six-line `reserve`
function contains two deliberate boundary bugs: `now > expiry` admits an expired
lease at equality; `amount >= remaining` rejects exact spending. The supervisor
reproduced both failures and checked the two minimal operator fixes independently.
No model received another model's answer or the fixed implementation.

Per candidate: one coding advisory and two two-turn realizations of the same
synthetic read-only tool probe, native and OpenAI-compatible. Maximum five
requests, 1,200 output tokens each, no correction run, 16,384 context, one active
model/job, 262,144 native transport bytes and 65,536 compatibility bytes. No new
wall-clock inference deadline was imposed. Only `read_fixture(path="budget.py")`
was allowed. The controller checked the exact name/arguments and supplied fixed
data `{marker:R17, passed:2, failed:1}`. Passing required actual tool calls and
association, then bare JSON `{marker:R17, total:3, accept:false}`, no further call,
and a complete stop. No model-chosen command touched the host.

Advisory requests use the real installed Bridge streaming transport, schema,
parser and accounting, with its existing opt-in fixture request override to
retain installed model-specific sampling defaults. This is direct Bridge
assistance, not a new durable MCP/controller qualification or an SDK execution.
Native tools use the installed Ollama API. Compatibility responses pass through
the real installed `validate_completion` parser. Each model's supported default
reasoning was retained; no speed-oriented disabling/tuning sweep was performed.
Temperature was the installed value 1 for the first four candidates, with each
model's own top-k/top-p/penalties and draft settings preserved. Production Bridge
and ChatProvider temperature/default settings were not changed. Effective runtime
selection was Harmony for GPT-OSS; renderer/parser qwen3.5 for Qwen3.6; gemma4
for Gemma4; and renderer qwen3.8/parser qwen3.5 for Qwen3.8. Complete local
template text and SHA-256 are retained in each metadata file.

Model digests below use the preserved short IDs from the full binding table.
The OpenHands fixture is **blocked/unrun for every row**.

| Model / screened short digest | Effective context / reasoning | Advisory | Native / compatible tool probe | Codex corrections | Qualification |
|---|---|---|---|---|---|
| gpt-oss:20b / 17052f91a42e | 16,384 / medium | Both boundary findings, but out-of-domain zero-amount finding/test, ambiguous summary and four tests exceeding cap | Pass / pass | Two supervisor editorial groups; no model retry | Corrected advisory baseline only; changed current digest requires reassessment |
| qwen3.6:35b / a7eb95c53bcf | 16,384 / true | 1,200-token limit entirely thinking; no final answer | Pass / final fenced JSON fails format (call/semantics correct) | None attempted; advisory needs another run | Not qualified within declared output budget |
| gemma4:26b / 001e5dafc3c7 | 16,384 / true | 1,200-token limit entirely thinking; no final answer | Fenced JSON fails format / same; actual calls/semantics correct | None attempted; advisory needs another run | Not qualified within declared output budget |
| qwen3.8:27b / aaee06c39dcf | 16,384 / medium | Both bugs, minimal fixes and three correct tests; no unsupported finding | Pass / pass | Zero | Provisional advisory candidate for this bounded fixture |

Independent decisions and the actual supervisor-edited GPT advisory are in
`supervisor-screen-review.json`. No runtime patch or durable acceptance was made.


| Model | Whole screen s | Advisory s | Cold load s | Prompt s | Generation s | TTFT s | First final text s | Advisory input/output tokens |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| gpt-oss:20b | 119.82 | 100.70 | 63.52 | 2.33 | 34.18 | 66.64 | 95.54 | 447 / 854 |
| qwen3.6:35b | 290.14 | 242.86 | 169.37 | 6.60 | 66.19 | 176.65 | none | 386 / 1200 |
| gemma4:26b | 192.53 | 163.19 | 90.99 | 4.62 | 65.14 | 98.22 | none | 396 / 1200 |
| qwen3.8:27b | 437.50 | 310.70 | 63.19 | 8.71 | 238.16 | 72.51 | 227.84 | 386 / 623 |

| Model | Native / compatible warm probe s | Peak physical GPU MiB | Peak owned process RSS GiB | Minimum available system RAM GiB | Logged main-model CUDA / host buffers MiB |
|---|---:|---:|---:|---:|---|
| gpt-oss:20b | 8.79 / 10.28 | 10,608 | 4.30 | 12.48 | 9,475.02 / 3,666.27; 25/25 GPU layers |
| qwen3.6:35b | 28.10 / 19.13 | 10,925 | 13.32 | 6.37 | 8,193.56 / 12,507.38; 42/42 GPU layers |
| gemma4:26b | 9.46 / 19.84 | 11,241 | 10.32 | 11.22 | 7,951.35 / 9,065.07; 31/31 GPU layers |
| qwen3.8:27b | 68.97 / 57.80 | 10,164 | 10.88 | 10.87 | 7,440.75 / 8,580.71; 30/66 GPU layers |

MoE GPU-layer counts do not imply all expert weights fit in VRAM: host buffers
remain substantial. Gemma also loads a 5/5-layer auxiliary model (425.34 MiB
CUDA and 272 MiB host). Its `/api/ps` size/VRAM values materially underreport
the physical/process observations, so they are not used as a complete memory
budget. Qwen3.8 logs 576 MiB CPU plus 448 MiB CUDA KV and 64 MiB draft KV at
16,384 context. Full per-model cache/buffer evidence is retained in runtime logs.

These are preliminary fixture observations, not general coding rankings or
pilot results. Cold refers to first model load in the owned process, not an OS
filesystem cache flush. Warm probes reused the resident model. Provider load,
prompt and generation durations, counts, TTFT and first final-text latency are
saved separately. Non-streaming compatibility TTFT is unavailable. Whole-screen
time includes the advisory and tool exchanges but excludes server bootstrap and
post-screen unload. CPU load, regression/Docker activity and the automatic GPT compatibility
migration overlapping Qwen3.6 were not controlled as an efficiency experiment. Tokenizer counts are not compared as a quality or
speed ranking.

All loaded contexts were checked using `/api/ps`; physical GPU activity,
process RSS and whole-system available RAM were sampled every two seconds.
Sampled peaks can miss shorter transients. API `size`/`size_vram` are runtime
accounting, not interchangeable with process RSS or whole-system RAM. The CUDA
12 backend actually loaded; unsupported CUDA 13 discovery did not require a
driver change. Model weights, CPU offload, KV/cache and buffers are visible in
owned runtime logs. The successful screening server selected the RTX UUID
only, loopback port, one resident model, one parallel request and cloud disabled.
Shared-server residency was checked before each candidate and monitored during
execution. No unrelated model was unloaded or process terminated.

The native streaming probes kept thinking separate from final text and returned
the assistant thinking field on the tool follow-up. OpenAI-compatible responses
use a `reasoning` field; the installed parser's normalized reasoning property
only reads `reasoning_content`, while its raw response retains `reasoning`.
Therefore full reasoning/context preservation through pinned SDK 1.53.0 remains
unverified. Streaming tool execution is explicitly rejected by candidate
ChatProvider; it is not qualified by the native streaming diagnostic. Markdown
fences in a semantically correct final response are a model instruction-format
failure, not evidence that the actual function call was missing.

**Provisional advisory choice: qwen3.8:27b**, exact digest above, installed
Ollama 0.40.2 template/controls, medium thinking and 16,384 context. Its whole
screen took 437.50 seconds versus GPT-OSS's 119.82, but it needed no correctness
or instruction correction. This is fixture evidence, not product-wide routing.
GPT-OSS's screened artifact remains useful evidence of native/compatible tool
behavior; its changed current artifact must be reassessed before reuse. None is
qualified for implementation. After the environment/context gates, Qwen3.8 and a
reassessed GPT-OSS binding are at most two prospective finalists, not approved
implementation defaults. No lower-footprint fallback was needed because Qwen3.8
passed. Qwen3.5:9b, Qwen3-14B and 4b-instruct remain untested alternatives; VL and
embedding remain outside this text-coding screen.

### OpenHands isolation, image and context gate

The already-installed Docker Desktop engine was stopped initially and was started
for this check. Docker **29.6.2**, WSL2 **6.18.40.1**, cgroup v2 and containerd
`overlayfs` remain in use, backed by ext4 Docker data. No global storage setting
changed. The cached Python 3.13.12 base image is still exact local ID
`sha256:fd4b2c1255e1daac21e1a6b4dae0e21d77cc943c74ea193452f4f004d415ca39`.
It contains neither `openhands-sdk` nor `openhands-tools` distributions; this
was checked inside a disposable restricted container.

A new actual-allocation probe passed for read-only root plus workspace 64 MiB,
tmp 32 MiB, home/state 32 MiB, exchange 16 MiB and shm 8 MiB. Each wrote nonzero
bytes until ENOSPC; `st_blocks*512`, apparent size and bytes written agreed.
Root writes failed EROFS; worker creation under `/dev` was denied. The largest
sampled cgroup allocation was about 104 MB under a 512 MiB/no-swap/0.5 CPU/32-PID
limit. Only loopback existed, no Docker socket or host mount was present, no GPU
was passed through, and the logging driver was none. The probe container exited
and was removed. This is trusted environment diagnostic code, not an SDK agent.

The SDK-version image is published and anonymously reachable. Its Linux/amd64
digest remains
`sha256:a6865fc1da99c6e1038c70fde59df237d16d48ac30aadcc9a98916dc56bcf7a0`,
compressed layers **1,202,198,853 bytes**. It is missing locally, not an auth,
network, unpublished-tag or platform problem. It is a packaged server executable,
not the Python SDK environment expected by this runner; no `latest` substitution
or SDK upgrade was attempted. The separate pinned-source build plan remains
SDK/tools **1.53.0**, source **54daf056bd863bb46f922a2fe9324dd736b37ff6**.

The smallest compatible environment is the cached base plus that isolated SDK,
with the tested read-only/tmpfs profile. The existing adapter still relies on
`docker cp` and container exit before collection. Live tmpfs needs bounded fixed
exec initialization/mailbox/collection while the container remains alive, durable
collection before shutdown, and escalation if tmpfs disappears. The existing
quota gate continues to reject this backend; it was not weakened. Proposed SDK
limits remain 2 GiB RAM/2 CPU/128 PIDs, 152 MiB writable data charged within RAM,
8 MiB shm, bounded file/descriptor/message-queue limits and 128 MiB controller
artifact capacity. The aggregate controller allowance and transport/recovery
lifecycle require implementation and verification. Network-none plus the
controller-owned inference mailbox keeps the trusted controller outside the
agent tool sandbox without a broad host listener.

The [documented OpenHands setup](https://docs.openhands.dev/openhands/usage/llms/local-llms)
requires approximately 22,000+ context, commonly 32,768. That is not a measurement
of this smaller custom SDK integration. Pinned prompt/tool source was inspected:
its reference OpenAI static-prompt snapshot is 14,824 UTF-8 bytes; the selected
implementation-proposal instruction is 184 bytes. Those are source/reference
sizes, not the exact rendered system+tools+task+history token count. Actual SDK
construction/tokenization and tool-output headroom remain unavailable because
the pinned dependencies are absent. Do not infer implementation fit from the
16,384-context screen. The prepared fixture proposes 32,768 only after actual
measurement and loaded-context confirmation, with combined Windows/WSL/LAB/
SDK/model/KV/cache headroom. No prompt truncation or context reduction was used
to claim success. The existing advisory skill also says not to edit/execute;
its precedence within a real implementation contract needs review before dispatch.

No real `LAB -> OpenHands -> Ollama -> read/edit/test -> independent verification
-> Codex review` job was submitted. No implementation candidate, acceptance,
integration or executor-specific cancellation/recovery result is claimed.
`implementation-fixture-plan.json` preserves fresh identical baseline inputs,
protected acceptance tests, eight steps and at most the existing one correction
for at most two later finalists. Both implementation and pilots remain inactive.

### Independent approval packages and Strata decision

I/approval-openhands.json and I/approval-strata.json retain exact component,
source/digest, local-reuse, privilege and rollback manifests from the previous
blocker pass and add current rechecks. Their detailed per-artifact hash lists
remain in B; no dependency was installed. Planning estimates/reservations below
are distinct from measured installed or peak preparation usage.

| Package | New download | Installed/preparation storage | Privilege, scope and rollback |
|---|---:|---|---|
| OpenHands SDK/tools 1.53.0 and 174 locked artifacts | 101,666,057 bytes | Expanded wheels 363,741,223 bytes; func-timeout source 236,830 bytes; incremental install estimate 0.5 GB; reserve 2 GiB preparation. Reuse existing approximately 5.05 GB base. | Existing Docker access; root only for build/trusted init, UID 10001 worker. Private image/SDK/wheelhouse only. Remove recorded new artifacts after owned jobs stop; preserve shared base, models and history. No host Python change. |
| Strata pinned source/llama tooling, Coder IQ1_M, MTP, Python and standard CUDA 13 runtime | 64,439,597,563 bytes | Estimated retained 90–95 GB, preparation peak about 100 GB; reserve 120 GiB. Actual generated overhead/peak remain unmeasured. | Private directories/venv; engine 0.1.41 and exact model revisions/hashes retained in manifest. Standard runtime needs driver >=580, separately unresolved. Remove only newly approved assets after owned-process stop. |
| Strata experimental CUDA 12 alternative, replacing CUDA 13 row components | 64,652,937,028 bytes total package | Same planning envelope; detailed differing expanded runtime sizes in manifest. | Current driver exceeds documented numerical floor, but this path remains experimentally unqualified. No driver change or activation approved. |

Pinned and current [Strata model documentation](https://github.com/Niko1221/Strata/blob/main/docs/MODELS.md)
were byte-identical on this check. They describe the separate Flash-Next/Coder
family. None of the nine Ollama bindings has the proposed Coder shard hashes;
there is no verified direct weight reuse merely because a model is Qwen or MoE.
The potential benefit is evaluating that distinct larger, pruned coding model
and its runtime, not enabling MoE in already-working Ollama. No near-term quality
or memory/context benefit beyond the installed candidates has been demonstrated.
**Defer Strata activation**, retain the optional adapter/preparation, and do not
make it a prerequisite for OpenHands/Ollama work. A 32 GB marketing fit statement
is not combined SDK/Windows/context qualification.

Read-only driver checks still show RTX 560.94, GTX assigned 582.66/Code 31 and a
shared service bound to 560.94. Mismatch remains a hypothesis, not a proved cause.
[NVIDIA 581.80 release notes](https://us.download.nvidia.com/Windows/581.80/581.80-win11-win10-release-notes.pdf)
cover Windows 10 and the two GPU families, but
[NVIDIA's security bulletin](https://nvidia.custhelp.com/app/answers/detail/a_id/5821)
flags earlier R580 versions for Pascal, and
[582.66](https://www.nvidia.com/Download/driverResults.aspx/272768/en-us/1000/)
is a legacy-family security package. A currently maintained common package with
confirmed exact Dell subsystem INF binding was not established. No driver package
is recommended for installation in this pass. Preserve the working RTX setup;
obtain exact OEM/NVIDIA support guidance first. Any later separately approved
change needs signed-INF matching, retained working installer and driver-package
exports, a recovery plan and a repeat of the exact RTX/Ollama check after rollback.
No driver removal/install, device disabling, cleanup utility or BIOS change occurred.

### Evidence limits, side effect and next action

Local assistance was the actual installed Bridge screen. Codex authored the
fixture/oracle/harness, independently reviewed outputs, investigated environment
and upstream evidence, and wrote this report. No model authored an accepted
runtime patch; no cloud-token savings, Codex-equivalent quality or long-term
stability is inferred. Human focus, keyboard, DPI, readability and hide/reopen
acceptance remain untested in the compact manual ledger.

Two pre-inference harness failures are retained separately: startup readiness
returned a timeout while GPU discovery continued, and a Windows default-codepage
read failed on UTF-8 metadata. Neither generated a model result; the repaired
harness did not erase or rerun a failed inference. During the first startup,
Ollama's default maintenance logged **two unused blobs removed**, an unintended
side effect. Their identities were not logged and restoration was not established.
At that initial check all nine wrappers and referenced blobs were preserved;
subsequent owned startups explicitly set `OLLAMA_NOPRUNE=true`.

Final verification found a second automatic side effect: Ollama migrated GPT-OSS
to a local compatibility GGUF during inference (11:32:00–11:36:28 UTC). It generated
a **13,793,422,816-byte** derived weight blob,
`8ecb5d4ad6172c63f9cbf1a07a04e525985a8a11a6e516da02b674c4010de716`,
and metadata, and changed the tag's wrapper. The final API digest is now
`9ba9cc2b4e02463b933096090530aef679d534dd91ecc9afadfb2dbfdc59f3c5`
(local reported size 13,793,441,546 bytes); the wrapper hash changed from
`0779c8db9e8123241fe1774cef8538450857c4354c52d8a9bf6d8733d719378c` to
`772f45cc11275c34238da8c5d8242967395a0e0a25d2d8e3aa87ca1bceb9acf1`.
The screened GPT resident used the original e7b273f9 weight and completed before
migration finished; its result does not qualify the changed tag. This was local
conversion, not a download. Original GPT weight/manifest blobs and every original
referenced blob for all nine models remain present with matching sizes; the other
eight wrappers are unchanged. Large weights were not fully rehashed. See
`final-model-preservation.json`. No rollback/deletion was attempted. These
unintended runtime actions mean the model inventory was **not fully unchanged**,
and this pass must not claim zero model/cache changes. Shared residency is empty,
the owned server exited successfully and no safety instability was recorded.

The next useful action is to approve the **OpenHands-only pinned private build**
(101,666,057 download bytes; estimated 0.5 GB incremental install; 2 GiB preparation
reservation). That approval is not granted by this request: its prompt expressly
excludes missing-dependency installation. The component/source/hash/privilege/
rollback package is I/approval-openhands.json with the locked artifact list in B.
Then finish the existing adapter's bounded tmpfs transport and recovery, resolve
implementation-skill precedence and SDK reasoning propagation, construct and
measure the real SDK prompt/context, and qualify one disposable implementation
fixture before considering a second finalist. Do not bypass any gate to dispatch.

Strata's independent approximately 64.4 GB download/120 GiB preparation proposal
remains deferred. Driver changes need a separately supported plan and approval;
none is currently recommended. Restoring the previous GPT tag binding or removing
its newly generated compatibility copy would need a separately reviewed recovery
action; neither was attempted here. No further model loading was performed after
the final identity change was discovered.

The original eight-case pilot is not ready. A narrower Codex-only versus
Ollama-hybrid advisory comparison could be designed around the qualified Qwen3.8
fixture, but it is not prepared as completed evidence or activated, and requires
separate explicit approval. Implementation comparisons remain gated by the real
SDK result. Both pilots stay inactive. Human package launch/upgrade/rollback,
focus/keyboard/DPI/readability, hide/reopen/responsiveness and the other compact
manual-ledger rows remain untested; hidden Tk and automated/live protocol checks
do not count as human acceptance. The manual ledger remains 0 passed / 0 failed /
1 blocked / 9 not tested. No issue or release was published.

## Historical qualification — 2026-10-08

Candidate: `codex/selective-local-execution`, base
`0b817c572a81a22c94988cdbf163d214957985b7`, with uncommitted changes.
The original development/release checkouts remain unchanged. Nothing was committed,
pushed, merged, published or integrated into a production tree. Defaults and the
eight-case pilot remain unchanged/inactive.

Private evidence is under workspace
`data/selective-egpu-qualification-20261008/` (abbreviated Q below).
It contains the initial diff/status, complete source/package/import hashes, job
databases, actual outputs, runtime logs, GPU samples and test reports. Public
documentation intentionally omits personal paths, device UUIDs and job IDs.

The later [blocker-resolution pass](SELECTIVE-BLOCKER-RESOLUTION.md) closes the
regression gap, resolves image/dependency identities and probes an enforceable
read-only sandbox. It also records that the previously qualified qwen3:4b tag is
now absent. This report retains the historical live runs; its earlier image/size
uncertainties are superseded by that follow-up, not silently erased.

## Current hardware evidence

Read-only observation at **2026-10-08T17:14:47.8599842Z** supersedes the earlier
same-day “eGPU absent” observation:

- Dell G5 5587, Windows 10 Home 19045; **34,139,435,008 bytes installed RAM**
  (nominal 32 GB, 31.79 GiB reported).
- External **RTX 3060, 12,288 MiB VRAM, driver 560.94**, PCI 07:00.0,
  observed PCIe Gen3 x4. Its exact NVIDIA UUID is in Q/hardware evidence and
  Q/nvidia-baseline.csv.
- Internal **GTX 1060 Max-Q** remains enumerated by Windows with **Code 31**,
  driver 32.0.15.8266 (582.66), but is absent from nvidia-smi. Its current NVIDIA
  UUID/VRAM cannot be queried. Earlier 6,144 MiB evidence is historical, not a
  current successful detection. WMI's approximately 4 GB AdapterRAM is capped and
  is not used as VRAM evidence. Intel UHD 630 is also present.
- Samsung 970 EVO Plus 500 GB and Crucial BX500 4 TB SSDs. Initial free space:
  C: 98,489,749,504 bytes; D: 3,031,050,932,224 bytes. Final free-space evidence
  is recorded separately after the user's concurrent model relocation.

Only the RTX UUID was selected through the test process's CUDA_VISIBLE_DEVICES.
VRAM was not pooled. No device, driver, BIOS, global runtime setting or system
network configuration was changed. The user moved the existing Ollama models
during these checks; only the test instance's model-directory setting was updated
after verifying the same exact manifest digest. Missing-model admission evidence
was preserved.

## Component qualification

| Component | Actual hardware/model | Live check | Result | Evidence | Remaining blocker |
|---|---|---|---|---|---|
| RTX inference / Ollama 0.32.5 | RTX 3060 alone; qwen3:4b Q4_K_M; 16,384 context | One raw bounded request, two completed structured advisories, one owned cancellation | **Live verified for these short checks**; raw 64-token response ended at its output limit and did not satisfy its wording instruction | Q/raw-generation.json, gpu-summary.json, runtime logs, ollama-ps-final.txt | Longer-term connection stability, larger models/context and general quality remain unqualified |
| Final candidate MCP → controller → worker → Ollama | Same exact tag/digest; code-review@1.0; no deadline, 1,024 output limit | Actual stdio submission; MCP client closed before worker finished; reconnect read same job | **Live verified**; result finished/awaiting_review, then Codex recorded corrected advisory review | Q/live-final/mcp-submit.json, mcp-advisory-status.json, installed-live-identity.json, supervisor-review.json | Use the independently started companion controller; no automatic implementation permission |
| Dock and review state | Installed candidate Tk dock, same database/job | Actual hidden Tk controls read running and finished job state and reported usage | **Automatically observed with live data**; human UI acceptance **not tested** | Q/live-final/dock-observations.json | Human focus, keyboard, DPI and hide/reopen checks |
| Cancellation / restart / duplicate prevention | Owned test Ollama process tree; exact job/attempt | Cancel after runner sampler started; client already closed; stop owned runtime; restart worker | **Live verified**: cancellation_pending/escalated retained; reservation released only after identity-checked runtime termination; no new attempt | Q/cancellation-*.json, relocated-runtime/runtime-closed.json, stale-reservation-recovered.json | OpenHands-specific cancellation/restart remains untested |
| Linux sandbox prerequisites | Existing Docker 29.6.2, WSL2, cgroup v2, containerd overlayfs; cached agent-server 1.15.0 image | Trusted diagnostic Python under UID 10001, network none, no mounts/socket; kernel memory/CPU checks and actual allocation | **Storage enforcement failed**: size=2G accepted but 2,214,592,512 bytes allocated. CPU throttling observed; memory-limited probe OOM-killed within its container | Q/sandbox-enforcement-probe.json, sandbox-cpu-proof-final.json, sandbox-cpu-memory-proof.json, final-sandbox-gate.json | Quota-capable Linux storage; final candidate rejects this engine |
| OpenHands SDK executor | Candidate pins SDK/tools 1.53.0; no suitable image available | Candidate preflight against installed engine; cached image metadata inspected | **Blocked** before SDK agent execution; no model-tool-use conclusion | Q/final-sandbox-gate.json; packaged executor assets | Enforced quota plus approved immutable SDK 1.53.0 image and dependencies; real terminal → edit → test loop |
| Strata advisory / inference | RTX driver 560.94; Coder IQ1_M assets not found in checked locations | Current upstream metadata/source rechecked, local runtime/assets inventory | **Blocked; no live Strata request** | Q/upstream; pinned sources in SELECTIVE-SETUP.md | Standard engine requires >=580; experimental CUDA 12 path untested; assets and exact binding absent |
| OpenHands → Strata / implementation review and disposable integration | Neither prerequisite combination qualified | No real implementation candidate generated | **Blocked / not tested live**; existing deterministic tests remain separate | Regression reports; qualification instructions | Both independent lanes must pass first; then inspect actual patch and independent acceptance execution |
| Eight-case comparative pilot | Prepared same-base cases retained | Readiness review only | **Not ready; inactive** | SELECTIVE-PILOT.md and existing prepared manifest | Implementation qualification, combined memory plan and explicit pilot activation |

The final advisory reported **1,105 input / 275 output tokens**, **6.944 s loading /
11.031 s provider total**, and **23.318 s** controller execution. Queue and total
timestamps are retained in its database. Final generation samples observed up to
**5,494 MiB total RTX memory**, **100% utilization**, and a minimum
**17,658,212,352 bytes host memory available**. ollama ps reported 5.1 GB,
100% GPU and 16,384 context. Runtime CUDA logs bind the runner to the RTX UUID;
nvidia-smi compute PID samples corroborate that physical GPU, rather than relying
on ollama ps alone.

No device loss, unexpected CPU model fallback, GPU out-of-memory or connection
failure was observed during these short requests. CUDA discovery probes that
intentionally stop after inventory, expected ROCm absence, idle unloading and
the requested cancellation are distinguished from generation failure. The system
event query found no matching GPU/display/WHEA/PnP events in the observation
window. This does not establish that all earlier connection problems are resolved.
The measured host headroom excludes an actual OpenHands agent and Strata workload.

The advisory supplied two cloud-rejection suggestions consistent with selection.py.
It omitted the requested exact-selection case and included a speculative non-dict
finding and an unfinished finding. Codex inspected the source and existing tests,
retained only supported suggestions and recorded a **corrected** handoff tied to
the exact output hash. No model-authored patch was integrated. The old GTX
advisory is not a controlled timing comparison; there is no improvement or savings claim.

## Targeted fixes and package identity

Only qualification failures prompted code changes:

1. Add opt-in companion contract submission/status MCP tools using the existing
   contract admission/store; no review/integration endpoint. Require the existing
   controller to be started separately with `companion start`. The MCP server
   only queues; it reports `controller_not_running` when appropriate.
2. Give Git identity probes DEVNULL input and no Windows console. Actual stdio
   tests exposed a hang when Git inherited the MCP input pipe.
3. On worker restart, retain an orphaned completed-job reservation as
   cancellation_pending for explicit reconciliation. Do not replay inference.
4. Fail sandbox preflight closed on the current containerd overlayfs storage,
   whose declared quota was empirically unenforced. Supported overlay2/XFS storage
   still requires an actual enforcement qualification; its label is not proof.

An intermediate candidate exposed the MCP client's Windows job-object cleanup
killing descendant workers. The final candidate uses the original independently
started controller, with no breakaway flags or host-isolation bypass. The final
non-editable package was installed in an existing task-only environment with
--no-index --no-deps. MCP, controller, worker, dock and executor asset imports/hashes
are recorded together in Q/live-final/installed-live-identity.json and
Q/candidate-final.json. Earlier packages/evidence are retained. The live-tested final wheel is 175,306 bytes,
SHA-256 f4485a4590c12bd69583388ada0e1928e99faa2d61cccbfd7939df1fe11d0dff.
The final packaging pass normalizes CRLF to LF in the two touched runtime files
so Git reviews show only substantive changes. The final wheel/source hashes are
in Q/candidate-final.json; normalized source bytes match the live-tested wheel
and installed tests rechecked the final package. There are no later runtime logic changes.
Final wheel: 175,274 bytes, SHA-256
42de265e805c4b2216f40cb5db5bea5f6fe238275f45eccf49b26768785c4233.

Exact changes since the prior implementation: companion.py, server.py,
selective_cli.py, sandbox.py, the focused MCP/process/sandbox tests and the crash-test fixture allowance,
PUBLIC-FILES.txt and the linked qualification/setup/report/manual documents.
No inference adapter, SDK pin, model configuration or production default changed.

The broader regression run recorded **222 passed / 3 failed** across 225 cases
(Q/regression-complete.xml). All three failed before the requested crash boundary
because the fixture's four-second workflow lease expired; saved database evidence
records the guard rejecting late results. An unchanged isolated retry passed two,
while the third again expired. The fixture now allows 15 seconds for normal Windows
file/SQLite work; production limits are unchanged. Actual lease-expiry assertions
still wait for the recorded lease. The three affected cases and two explicit
expiry/crash boundaries **all passed** in 67.84 seconds (Q/regression-crash-final.xml).

**97 selective tests passed against the installed final package** in 79.80 seconds
(Q/installed-reviewed.xml). This overlaps the source suite and is not added
to it. An initial copied-test run lacked the pilot preparation script; after copying
the existing script into the harness, all 97 passed. The pilot test only creates
fixtures and runs no inference. Ruff, documentation checks and the public-source
audit passed. The earlier incomplete piped-stdin harness run was aborted during
investigation and is not counted. Initial MCP and diagnostic probe failures are
retained. No real implementation patch, correction loop or integration is claimed
from deterministic tests.

## Consolidated remaining actions and approval boundary

1. **Hardware/runtime choice:** review the internal GPU Code 31. Strata's standard
   CUDA 13 engine requires driver >=580; a driver change would require administrator
   privileges and a restart. No driver was selected or changed. Pinned upstream
   [OLDER_GPUS guidance](https://github.com/Niko1221/Strata/blob/fb58e0dbc8399662c0e47c76578c6e878b14f6cf/docs/OLDER_GPUS.md)
   also permits explicit --cuda 12 on RTX with Windows driver >=528, but calls
   this experimental and says older drivers were not tested upstream. Thus 560.94
   is not an unconditional Strata incompatibility. Choosing that unqualified path
   still needs deliberate approval and live qualification; keep RTX alone.
   Version 0.1.41 Windows CUDA 12 engine archive: **198,572,838 bytes**, SHA-256
   646ded0105aa5213a75e16621d559670d09dac26b5c720c9fd651ca83bdf14ec;
   standard archive: **137,164,559 bytes**, SHA-256
   3dd7715f4844c0f9d2f28eb5067af0198f386df060c93523cd17e1d65b757f13.
   Those exclude separately installed CUDA/Python dependencies. Neither downloaded.
2. **Sandbox and SDK preparation approval:** select a Linux Docker storage
   configuration that demonstrably enforces the existing 2 GiB writable quota.
   This can require administrative Docker/WSL/VM changes and disk space; no change
   is authorized here. Then prepare the existing executor image with a verified
   Python >=3.12 base digest, SDK/tools **1.53.0**, and acceptance dependencies.
   Direct PyPI wheels are 911,858 and 200,392 bytes; they are **not** the complete
   dependency download. Base image, transitive versions/download bytes and peak
   storage must be resolved into one exact manifest before installation approval.
   Cached agent-server 1.15.0 is an ELF-packaged application, not this SDK image.
3. **Strata preparation approval:** source revision
   `fb58e0dbc8399662c0e47c76578c6e878b14f6cf`, engine 0.1.41, Coder IQ1_M at
   `5348543e0147355ac9cbcb031184a3546350988e`, Apache-2.0 weights.
   Its two GGUF shards total **58,408,584,928 bytes** with hashes in the setup
   guide. This excludes runtime/draft/preparation. Upstream setup explicitly
   writes approximately **23.4 GB** of experts for this low-RAM path and retains
   draft source/packed/runtime artifacts; the generic ~80 GB free recommendation
   is not a verified peak. Exact draft/runtime/dependency sizes and peak
   preparation space remain unresolved. No blanket download approval is sought.
   Complete that manifest and whole-system fit plan before one consolidated
   install/download approval; then bind only loopback, disable runtime tools/MCP,
   and qualify startup, identity, inference, stream and cancellation independently.
4. **Manual qualification / pilot:** after the environment gates pass, execute
   the existing disposable SDK fixture with Ollama first, then independently
   qualify Strata and repeat the fixture through it. Review actual tool results,
   patch and trusted checks before disposable integration. Human dock checks
   remain outstanding. Only then request explicit eight-case pilot activation.

Proposed initial qualification settings remain one inference at a time, RTX-only,
qwen3:4b exact digest, 16,384 context, 1,024 output tokens, existing step/retry
budgets, and no generation wall-clock deadline. Proposed sandbox limits remain
2 CPUs / 2,048 MiB RAM / 2 GiB writable storage; actual SDK context fit and total
Windows + LAB + runtime + KV + executor headroom must be measured before the pilot.
No eight-case cost/resource prediction or quality equivalence is established.

Feature rollback remains `selective.enabled=false`; retain schema-3 databases and
artifacts. Older runtimes use the retained pre-upgrade copy in another directory.
Only owned test processes/containers were stopped/removed. Starting the existing
Docker engine resumed its pre-existing containers; those were left untouched.
No callback, notification, production integration or release action occurred.
