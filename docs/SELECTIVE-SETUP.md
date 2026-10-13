# Optional provider/executor setup and rollback

See the [complete workflow and source map](WORKFLOW.md) for entry points, actual
stored states, transport, data locations and accounting boundaries.

## Qwen27 project workflow

Activation status: enabled and live-tested for this project after independent technical acceptance. Documentation and small-fix categories use supervised local-first routing; test generation remains a scoped supervisor decision. Both broad pilots remain disabled.

The personal profile is private `config.toml` in the existing
`worktrees/selective-local-execution` checkout. It points to a separately frozen
controller/package and dedicated milestone data directory. It does not modify
the original source folder, other repositories, global Ollama configuration or
Codex registration. Generic distribution defaults remain unchanged.

| Component | Installed/configured | Tested/enabled |
|---|---|---|
| Ollama | Existing 0.40.2 service, loopback `http://127.0.0.1:11434` | Exact Qwen identity and native options checked before admission; loaded digest/context and runner flags checked before returning tool calls |
| OpenHands | Existing SDK/tools 1.53.0 in immutable Docker image below | Networkless mailbox executor; real editor/terminal tasks and protected independent acceptance |
| Strata | Pinned isolated runtime/assets and independently verified direct-GGUF pack | Disabled; patched A/B passed, then RAM guard stopped runtime; C unrun |
| Dock | Existing native Tk companion, same durable store as the jobs | Automated presentation/window checks; human interaction remains untested |

Qwen tag: `qwen3.8:27b`; full manifest identity:
`aaee06c39dcf2437cde036998d960e1fc1494b8191be7cc9657d01e509097813`.
Main weight SHA-256:
`f5f1dd8920d417aac2718b0bda3403da274301efdd6760b4f0f4b864ff2ad57d`.
Quantization Q4_K_M, dense qwen35, 27,320,697,856 parameters.
Profile: 28 GPU layers, draft 4 (MTP), 65,536 context capacity, maximum
1,536 output tokens per response, temperature 0, thinking false,
strict no-truncation/no-shift, keep-alive 120 seconds. Stored remaining sampling
settings are top_k 20, top_p 0.95, min_p 0, repeat_penalty 1 and presence_penalty 0.
The complete template is retained in private identity evidence; its SHA-256 is
`b507b9c2f6ca642bffcd06665ea7c91f235fd32daeefdf875a0f938db05fb315`.
Ollama's internal runner uses chatml with no-jinja; LAB verifies both the stored
Ollama template identity and the actual runner flags. A GPU profile also requires positive provider-reported loaded VRAM; missing or zero VRAM fails before any tool call is forwarded.

Image:
`sha256:b0ec53df107bdbb7b9df9c397ee56d4f7f74bc49d6e6550b16ca6f23e5748090`.
The model sees no host mount, Docker socket, credentials or host shell. Only
declared task files and exact approved test argv are available. The controller
alone connects to host loopback. Container localhost is not used to reach Ollama.
There is **no OpenHands web UI** in this accepted SDK deployment; use the LAB dock
and CLI. Do not replace it with an unrestricted quick-start server.

A task has at most eight inference requests, two error-recovery cycles, two
supervisor-authorized attempts, zero transport retries, 15-second commands and a
30-minute attempt ceiling. Output is bounded at 16 KiB per command/response;
the existing 2 GiB/no-swap, 2 CPU, 128-PID, read-only/tmpfs profile remains.
Require 6 GiB available host RAM before admission; stop below 2 GiB immediately,
below 3 GiB for 15 seconds, above 11,776 MiB GPU allocation, or on missing GPU
diagnostics. Resource logs are bounded. Another resident model blocks admission.
Cancellation uncertainty retains the reservation until trusted reconciliation;
do not kill a shared Ollama service.

Selection order is explicit job model, persistent companion selector, then
configured project default. Profiles bind model/backend/identity/limits/settings
independently. Overrides never inherit a different model's identity.
A context change needs qualification; output/retry/attempt limits may only narrow.
Qualified profiles use companion submit/contract-submit. Calling them through a
legacy transport fails explicitly rather than dropping their settings.
Existing legacy/adaptive/workflow configurations continue to work independently.

From the frozen runtime directory, with an absolute path to the project config:

```powershell
python -m localagentbridge --config $ProjectConfig companion inventory
python -m localagentbridge --config $ProjectConfig companion start
python -m localagentbridge --config $ProjectConfig companion status
python -m localagentbridge --config $ProjectConfig companion dock
python -m localagentbridge --config $ProjectConfig companion pause
python -m localagentbridge --config $ProjectConfig companion cancel --run RUN_ID --job JOB_ID
python -m localagentbridge --config $ProjectConfig companion shutdown
```

Shutdown stops the controller; cancel an active job explicitly and verify its
terminal/uncertain state. Dock closure does not cancel work. No cloud callback
is enabled by these commands. For implementation, the supervisor creates a
bounded contract, protected checks and immutable input snapshot, runs
contract-route, then contract-submit. Git HEAD snapshots exclude uncommitted
changes: when working on uncommitted source, the supervisor must explicitly
freeze/review the exact task bytes, as the milestone harness does.

Private `data/qwen-standard-20261010/operations.txt` records verified absolute
installation/configuration paths and concrete commands on the qualified machine.
`activation.json` records the final activation state and frozen package identity;
`rollback-before.json` retains the prior configuration/selected-model state. No machine paths enter the public
package.

Rollback: pause admission, cancel/collect owned active work if necessary, request
controller shutdown, confirm ownership/termination, then restore the saved prior
config/selection. If the private config did not previously exist, retain the
new one as evidence and use the previous explicit configuration. Keep databases,
accepted patches, model assets and history. Never reset or clean the checkout.

### Independent Strata status

As of **2026-10-13**, Strata remains **disabled for general routing**. The approved
serving patch passed one live inference and one LAB advisory; a later RAM guard
stop blocks OpenHands qualification and deliberate live safety checks.
Current upstream inspected: [7695859aa13afb248bdb4d36f9b2e95707db079d](https://github.com/Niko1221/Strata/tree/7695859aa13afb248bdb4d36f9b2e95707db079d),
including `serve/server.py`, `serve/frontend.py`, `serve/runconfig.py`, setup,
requirements, model/install guidance and cancellation/context/tool tests.
Latest release metadata inspected: **0.1.43**. Earlier 0.1.41 evidence below
remains historical, not proof of an installed runtime.

The official [model guide](https://github.com/Niko1221/Strata/blob/7695859aa13afb248bdb4d36f9b2e95707db079d/docs/MODELS.md)
limits this engine to Flash-Next variants. The locally installed
`qwen3.6:35b` is GGUF **qwen35moe**, 35,505,251,456 parameters, Q4_K_M,
256 experts / 8 active, with MTP. Its parent identifies the 35B-A3B model;
manifest digest is `a7eb95c53bcf96b4bdd008d0fab4a5dac88047d9c1a7a9ab88ed453423fbd87c`.
It is not the supported Flash-Next Coder asset. Neither this model nor dense
Qwen27 may be silently reused as Strata weights. `/v1/models` lists aliases,
and the completion `model` field can echo a request; neither proves loaded identity.

The original e5c6337 inventory found no runtime or complete compatible assets.
Following the owner's approval, the pinned 0.1.43 CUDA 12 runtime, dependencies
and all raw model/MTP inputs are installed and hash-verified. A small cuBLAS
operation passed on the existing driver. The original expert-copy RAM failure
remains quarantined. The approved direct-GGUF retry now passes independent pack
validation. The separately reviewed serving-only patch then passed A and B on
loopback port 8080 with exact loaded GGUF/PLE identity. Sustained available RAM
below 3 GiB stopped the owned runtime before C; the service is now off. See the
[current measured report](SELECTIVE-IMPLEMENTATION-REPORT.md#serving-patch-qualification--2026-10-13). Hardware and driver remain unchanged.

#### Reproducing and rolling back the approved serving patch

The final [patch](qualification/strata-serving.patch), including explicit cancellation
errors, is offline-tested only. The [preceding tested patch](qualification/strata-serving-tested.patch)
provided the A/B results; the RAM stop prevented another live start. Both change only `serve/server.py`
from base `7695859aa13afb248bdb4d36f9b2e95707db079d`. The
[helper](../scripts/strata_serving_patch.py) requires that file's exact upstream
hash and an absent destination outside the original source tree:

```text
python scripts/strata_serving_patch.py UPSTREAM_SOURCE FRESH_SERVING_COPY --evidence EVIDENCE_DIRECTORY
```

This only copies local source and writes patch/provenance records; it never
loads an engine or downloads anything. Preserve the [upstream MIT notice](qualification/STRATA-LICENSE.txt).
Use the already installed pinned dependencies for offline tests, with the
process-local `LAB_STRATA_SERVING_SOURCE` pointing at that separate copy:

```text
python -m pytest tests/test_strata_serving_patch.py -q
```

Without that optional local source/dependency input, the ordinary public suite
checks unknown-base rejection and explicitly skips the external offline cases.
The qualification launcher prepended the reviewed source copy before importing
`serve.server`, checked its exact hash/import path, allowed one start, and bound
all resulting serving bytes plus the launcher/config. Native engine, weights and
original source were unchanged. The patch/base/result hashes remain separate
in the trusted binding's model metadata and artifact manifest.

Qualification config additionally sets `reasoning_close_retry=false`,
`reasoning_loop_recovery=false`, `reasoning_budget_tokens=0`, `tool_call_recovery=false`,
`codex_compaction_cache=false`, `codex_thread_titles=false`, no disk sessions,
no replicas/lazy load and the unchanged native/mmap/loopback limits. LAB transport
and SDK retries remain zero. Tool-loop turns following successful responses
remain normally budgeted; failed responses are never replayed.

Rollback: stop only recorded owned processes, verify their exit/listener and
reconcile any uncertain reservation, restore the saved test cap/config, and
retain the separate patched copy as evidence. Original upstream bytes remain
available; **do not launch them as a rollback test**, because they restore the
known replay/restart conflict. Active LAB/Ollama never points at this copy.
The current live RAM stop requires a new reviewed decision before another start;
this reproduction command is not renewed inference authorization.

#### Configuration, diagnostics and exact selection

Use the existing `selective.providers.strata` table with an explicit loopback
**origin** (no `/v1` suffix), `enabled`, optional `api_key_env`, `temperature`,
and `enable_thinking` (default false). Authentication stays in the host process;
no key enters the container. Existing Ollama settings remain unchanged.

```text
python -m localagentbridge --config LOCAL.toml companion provider-status --backend strata
python -m localagentbridge --config LOCAL.toml companion provider-status --backend strata --model EXACT_ALIAS
python -m localagentbridge --config LOCAL.toml companion inventory
python -m localagentbridge --config LOCAL.toml companion select strata::EXACT_ALIAS
```

A configured Strata profile appears in the existing selector as
`strata::EXACT_ALIAS`, including a diagnostic reason when disabled or unavailable.
Only a loaded, identity-verified, reviewed qualified profile can be saved.
`installed`, `compatible`, `qualified`, `enabled` and `selectable` are distinct
status fields; unknown installation is null. These flags apply to the configured
runtime binding, not all files on disk. No runnable profile is supplied by this
repository. A disabled placeholder is never an executable choice.

The saved key persists in the existing companion database. An explicit job
`--model strata::EXACT_ALIAS` wins over it. A contract can instead specify
`backend="strata"`, `model="EXACT_ALIAS"` and its exact identity. Qualification
and scoped approvals still run through normal LAB admission. Models are never
substituted; failed admission records a reason and returns control to Codex.

#### Trusted serving binding

The existing adapter now requires `binding.family="coder"`, `config_path`,
`config_sha256`, `model_path`, `build_info`, exact server `process` and
`engine_process` identities, `server_argv`, `engine_argv`, `source_commit`,
`template_sha256`, `context_tokens`, `model_metadata` and `artifacts`.
Process records use `process_control.identity`. Only the reviewed Coder
`model_metadata` tuple is admitted: model `Qwen3.8-Flash-Next-GSQ-RCO-Coder`,
format `GGUF` or `Strata pack`, quantization `IQ1_M`, expert_count 256.
The supervisor must check actual model headers and the complete packing manifest;
these labels alone are not compatibility evidence.

Each artifact records path, size, mtime_ns, SHA-256, role and
`verified_by_supervisor=true`. Include every weight shard/generated pack input,
tokenizer/template and runtime source/dependency artifact; required roles are
weights, engine, server, tokenizer and template. Independently hash the complete
manifest before approving it. `identity` is `task_contract.digest` of
`config_sha256`, `source_commit`, `template_sha256`, `model_metadata` and the
ordered artifact entries restricted to path/size/sha256/role. It is local trusted
configuration, not a signature or remote attestation. Changed size/mtime invalidates
large weights; smaller runtime assets are rehashed with bounded buffers. A hostile
host administrator can defeat filesystem metadata checks and is outside this boundary.

Binding checks compare the actual listening process and child engine, exact argv,
config, loaded path, template and context both before inference and before returning
a response. Config must explicitly encode engine args (including effective options),
use one slot and loopback only, with MCP/monitor/before-load/auto-load/vision/replicas
and context fitting off. Runtime restart requires a freshly reviewed process binding.
No runtime load, lifecycle, settings or tool-execution endpoint is called by LAB.

SDK text blocks and structured calls/results use non-streaming Chat Completions;
images and unmatched tool results fail. Text-only SSE is bounded even without a
newline. Streaming tools are explicitly unsupported because the current SDK path
does not require them. Token/context/output/attempt limits remain enforced, optional
usage stays unavailable, and uncertain disconnects retain the inference reservation.
A complete HTTP rejection before generation can release it; timeout/disconnect
alone cannot. Tests exercise the transport with fixtures, not a real SDK/Strata loop.

#### Concrete optional installation approval package

**Approved by the owner for isolated preparation and bounded qualification on
2026-10-12; no general activation is authorized.** The original e5c6337 proposal
had no installation approval. Follow the [current preparation/qualification
report](SELECTIVE-IMPLEMENTATION-REPORT.md#approved-strata-preparation--2026-10-13)
for actual installed and tested status. The approved route preserves the working driver: isolated **Strata 0.1.43 CUDA 12**
from the [official release](https://github.com/Niko1221/Strata/releases/tag/v0.1.43),
server source at the commit above, and the pinned Coder assets below. This is an
experimental compatibility attempt, not a claim that driver 560.94 or the current
RAM reserve will pass loading.

| Component | Exact source/version | Download bytes |
|---|---|---:|
| Windows x64 CUDA 12 engine | `strata-windows-x64-cuda12.zip`, 0.1.43; SHA-256 `344998f7b91af0b028e8e5241db39bbc5abd9c93a0a33d6dbc33108bb8a837fb` | 200,294,528 |
| Strata source export | `7695859aa13afb248bdb4d36f9b2e95707db079d`, raw blobs | 48,247,685 |
| Existing pinned helper source manifest | llama.cpp `3cf03257f219afbe7334045ff7c6a06ac68c627d`, raw blobs | 172,252,331 |
| Coder two IQ1_M shards | [ISTA-DASLab pinned revision](https://huggingface.co/ISTA-DASLab/Qwen3.8-Flash-Next-GSQ-RCO-Coder-GGUF/tree/5348543e0147355ac9cbcb031184a3546350988e) | 58,408,584,928 |
| MTP tensor inputs | [Qwen pinned revision](https://huggingface.co/Qwen/Qwen3.8-Flash-Next/tree/de4b8e4d43b917e7706784d8bb445c9af86a3540), existing 31-tensor manifest | 5,214,301,696 |
| Pinned CPython 3.13 base/CUDA 12 wheels | Existing SHA-256 dependency manifest, official PyPI/NVIDIA wheels; no global Python changes | 620,622,204 |
| **Total planned payload** | Excludes HTTP overhead; stop for approval if dependencies/assets change | **64,664,303,372** |

The existing dependency manifest pins the upstream requirements plus CUDA 12
libraries; retain it rather than resolving latest packages. Code is MIT; Coder
weights declare Apache-2.0. Estimated retained disk is **90–95 GB**, preparation
peak about **100 GB**; reserve **120 GiB on D:**. Those were approval estimates;
the current report gives measured installation/partial-pack disk and preparation
RAM. Model-loading peaks remain unmeasured. Upstream estimates
about 23.4 GiB (25,146,163,200 bytes) of Coder expert storage, with low-RAM mmap mode on a 32 GB / 12 GB
machine. This is not proof that LAB's unchanged 6 GiB pre-admission, 2/3 GiB
hard/sustained reserve and 11,776 MiB GPU ceiling fit model-loading peaks.

Approved placement: core launcher/engine under `%LOCALAPPDATA%/StrataLAB/0.1.43`
on C:, with source, isolated venv/dependencies, models, cache, pack, logs and evidence
under the dedicated `LocalAI/StrataLAB/0.1.43` directory on D:. Private LAB test
installation, configuration/store and evidence use the existing D: project data
area, separate from the active store. No administrator privileges,
PATH edits, drivers, services, firewall rules, web application or cloud inference.
Do not run the one-click installer: even its check/setup route may bootstrap
Python/dependencies and download models. Reuse approved Python and explicit
pinned artifacts only. Initial context 16,384, output at most 1,536, one request,
vision/MCP off; safe startup/identity first, then bounded advisory and SDK fixture.
Stop when resource or compatibility gates fail; never raise them to get a pass.

Rollback stops only the recorded owned process tree, disables Strata admission,
and archives/removes only the newly created approved directories after resolving
and checking their paths. Preserve all LAB/Ollama configuration, models, databases
and qualification evidence. A driver upgrade is excluded and would need its own
specific approval. Approving this package permits preparation and bounded
qualification, not general enablement or a release.

#### Bounded retry amendment after the RAM stop

**Owner approved at 7cbaa11; single preparation completed.** The fresh direct
pack passed independent validation. Startup was held at the pinned server
retry-policy gate; see the [actual outcome](SELECTIVE-IMPLEMENTATION-REPORT.md#direct-gguf-amendment-outcome--2026-10-13).
The scope below records the authorization, not a new request to repeat packing.
The 2026-10-13 main expert-copy attempt exceeded the unchanged available-RAM
reserve. The [pinned engine documentation](https://github.com/Niko1221/Strata/blob/7695859aa13afb248bdb4d36f9b2e95707db079d/docs/DETAILS.md)
and [FileExpertSource implementation](https://github.com/Niko1221/Strata/blob/7695859aa13afb248bdb4d36f9b2e95707db079d/src/core/expert_source.cpp)
support reading this native Coder pack's experts directly from its GGUF shards.
The approved change was exactly to omit `--experts-bin` from the pinned
`tools/iq_pack.py` command, producing a fresh `data/pack-direct-gguf` directory.
Keep the quarantined incomplete pack untouched, and bind the fresh dense/index,
tokenizer, native expert table and both fully verified shards before startup.
No custom packer, new release or dependency is required.

Amendment scope: one guarded native-pack attempt (900 seconds), then only if
artifact checks and ownership/resources pass, one owned stage-A startup (600
seconds) and bounded inference (120-second request / 600-second attempt, zero
retries, initial 64-token probe; ceiling 16,384 context / 1,536 output). Preserve
6 GiB admission, 2/3 GiB hard/sustained RAM and 11,776 MiB GPU ceilings, two-CPU
preparation scope, one inference and loopback-only transport. Stop again at the
first resource/compatibility failure. The engine keeps `--native`,
`--mmap-experts`, 2,048 MiB VRAM reserve, no automatic context fitting, no
vision/runtime MCP and no prompt/conversation cache.

New download: **0 bytes**. Same Strata 0.1.43 CUDA 12, exact sources, dependencies,
weights, driver and C: executable path as the approved package above. A fresh
native pack is expected to add approximately **1.49 GB** under the approved D:
data root instead of the **25.15 GB** expert copy; the existing 120 GiB reserve
is sufficient on disk. Loading RAM/VRAM remains unknown and must be measured;
the direct-file mode is a source-supported retry hypothesis, not a qualification.
Rollback stops only the recorded owned process tree, restores test-only settings,
and retains/quarantines only the new pack; active LAB/Ollama files stay intact.
No administrator, global environment, service, firewall or driver change.

The owner also approved **Maximum only in the isolated qualification store after
A passes**, with original-setting capture/restoration. At the historical
direct-pack checkpoint A had not passed, so Medium remained unchanged. The later
serving amendment passed A, used Maximum for B, then restored the absent/Medium
setting after the RAM stop. B/C still require the existing supervisor-controlled fixture, a measured
Strata memory plan and all admission gates. This does not authorize higher
physical/context/output limits, pre-qualification, active-default changes or
general Strata routing. The serving change has now been approved and tested;
the remaining decision concerns measured RAM growth, as recorded above.

## Retained preparation and historical protocol

See [architecture and baseline](SELECTIVE-EXECUTION.md). This development feature
is disabled by default. No driver, BIOS, networking, Docker/WSL, global Python,
model inventory, cloud router or other repository is changed by setup commands
in LAB. No download or model launch occurs at dispatch.

The [blocker-resolution report](SELECTIVE-BLOCKER-RESOLUTION.md) contains the
current separate approval manifests, enforced read-only sandbox probes and driver
compatibility caveats. No installation is authorized by this guide. The existing
quota gate remains in force for the default profile. The explicit `readonly_tmpfs_v1`
alternative and pinned SDK adapter are covered by the [scoped qualification](SELECTIVE-LIVE-QUALIFICATION.md#scoped-openhands-qualification--2026-10-09); this is not production activation.

For the current strict command/collection profile, see
[bounded qualification](OPENHANDS-BOUNDED-QUALIFICATION.md). readonly_tmpfs_v1 now
requires the exact image with bounded_v3 controls. SDK generation uses only exact
read paths and approved test argv; no general shell is available. Optional Ollama
native_context=true applies context per request without restarting the shared
service or changing defaults. The tested qwen3:4b-instruct configuration failed
acceptance and must not be added to automatic implementation qualification.
Explicit compatibility qualification no longer requires a comparison pilot or a
Git commit; generated protected input bytes are bound in the durable job store.

## Interfaces and upstream pins

Examined on 2026-10-08:

- [Strata source](https://github.com/Niko1221/Strata/tree/fb58e0dbc8399662c0e47c76578c6e878b14f6cf)
  at `fb58e0dbc8399662c0e47c76578c6e878b14f6cf`, whose setup requires engine
  0.1.41. Read [AI_SETUP](https://github.com/Niko1221/Strata/blob/fb58e0dbc8399662c0e47c76578c6e878b14f6cf/docs/AI_SETUP.md),
  [MODELS](https://github.com/Niko1221/Strata/blob/fb58e0dbc8399662c0e47c76578c6e878b14f6cf/docs/MODELS.md),
  [DETAILS](https://github.com/Niko1221/Strata/blob/fb58e0dbc8399662c0e47c76578c6e878b14f6cf/docs/DETAILS.md),
  [INSTALL](https://github.com/Niko1221/Strata/blob/fb58e0dbc8399662c0e47c76578c6e878b14f6cf/docs/INSTALL.md)
  and [SECURITY](https://github.com/Niko1221/Strata/blob/fb58e0dbc8399662c0e47c76578c6e878b14f6cf/SECURITY.md).
- [OpenHands SDK v1.53.0](https://github.com/OpenHands/software-agent-sdk/tree/v1.53.0),
  source revision 54daf056bd863bb46f922a2fe9324dd736b37ff6, including hello-world,
  persistence, LLM and local-conversation implementation.
  [SDK documentation](https://docs.openhands.dev/sdk) and
  [local LLM guidance](https://docs.openhands.dev/openhands/usage/llms/local-llms).
  The optional image pins openhands-sdk and openhands-tools to 1.53.0. Its API
  was initially source-checked and mock-tested; the subsequent exact SDK/container
  live qualification is recorded above. It needs Python >=3.12, separate from
  LAB's unchanged Python >=3.11 environment.

Strata health returns service, loaded, model and max_context. Models lists serving
names/aliases and context metadata; it supplies no weight digest. The adapter also
reads props for serving model path and engine build. Chat Completions supports
bounded JSON and SSE text; reasoning_content is retained separately. Responses
and Anthropic APIs are not assumed equivalent or used by this adapter. SDK tool
exchanges use non-streaming Chat Completions. Tool compatibility requires the
separate SDK round trip, not an advertised flag or a successful chat.

Health may list an unloaded model that could auto-load on a request. LAB requires
loaded=true before Strata admission, and never requests runtime loading, unloading,
MCP execution, settings changes or model conversion. Disconnect cancellation has
no request-specific termination receipt, so uncertainty remains visible.

## Coder identity and footprint

Only the configured Coder family is considered initially. This is not support for
arbitrary installed Qwen models. The pinned setup names
[ISTA-DASLab/Qwen3.8-Flash-Next-GSQ-RCO-Coder-GGUF](https://huggingface.co/ISTA-DASLab/Qwen3.8-Flash-Next-GSQ-RCO-Coder-GGUF/tree/5348543e0147355ac9cbcb031184a3546350988e),
revision `5348543e0147355ac9cbcb031184a3546350988e`. Its model card declares
Apache-2.0; Strata code is MIT. The advertised IQ1_M variant uses mixed expert
quantization described by upstream; the label alone does not mean all weights
use one bit.

| Artifact | Bytes | SHA-256 from pinned artifact metadata |
|---|---:|---|
| IQ1_M shard 1 | 29,608,446,496 | e11083ba855e7666b48ea3f2db6a9c3a20c18751a012cc24f948de91b7087fad |
| IQ1_M shard 2 | 28,800,138,432 | 316b46f3a2dbd68c900f43136ab9449f9dcc3725dfd8c794847c204bc161e113 |

That is 58,408,584,928 bytes of GGUF downloads. Pinned MTP tensor ranges add
5,214,301,696 bytes. The complete standard-runtime/source/dependency payload is
64,439,597,563 bytes; the experimental CUDA 12 alternative is 64,652,937,028 bytes.
Preparation additionally materializes experts.bin and other packs. The current
manifest estimates 90–95 GB retained, approximately 100 GB peak, and reserves
120 GiB; actual allocation requires approved preparation. These are storage
estimates, not proof of RAM fit. No model payload was downloaded or locally
hash-verified. See the blocker report for every pinned source/artifact and rollback.

Detected RTX driver 560.94 is below the standard CUDA 13 engine minimum (>=580).
Pinned OLDER_GPUS.md also allows explicit experimental --cuda 12 on RTX with
Windows driver >=528; that alternative is unqualified, not automatically selected.
See the blocker report for exact metadata and the driver security/OEM caveats.
A numerically compatible driver version alone is not an installation recommendation.
Do not run upstream setup --check incidentally: its bootstrap can install Python
or create an environment. Low-RAM Coder setup writes approximately 23.4 GB of
experts.bin in addition to GGUF and draft artifacts; ~80 GB is not a verified
peak preparation budget. See [current live qualification](SELECTIVE-LIVE-QUALIFICATION.md).

A 32 GB host with a nominal 12 GB GPU is not automatically qualified. Account for
Windows/apps, LAB, OpenHands/Python, runtime residency, context/KV cache, sandbox
and headroom together. The default example's zero-valued memory plan intentionally
fails admission. Actual fit, eGPU transfer behavior, stable tool calling and quality
remain unmeasured. Desktop-GPU figures do not predict this Dell eGPU connection.

The original binding format described in the 2026-10-08 report is superseded.
Use the [current trusted serving binding](#trusted-serving-binding), including
server/engine arguments, complete artifact roles, source/template hashes and
model metadata. Old bindings do not establish the current exact identity.

Existing manual compute controls remain effective. The initial Strata resource
profile requires an explicit Maximum cap, plus the separate identity, context and
implementation memory/sandbox gates. Maximum is not evidence of model fit.

Keep Strata loopback-bound. Disable mcp_servers, mcp and api_monitor in its serving
configuration. Optional API keys are read through api_key_env on the controller;
keys never enter the task container. No unauthenticated LAN exposure or host
networking is required for the executor.

## Prepare the executor deliberately

The existing Linux Docker engine was started for the live check. Its containerd
overlayfs accepted size=2G but allocated 2 GiB + 64 MiB. The candidate rejects
this configuration. Existing cached agent-server 1.15.0 is not the SDK/tools
1.53.0 executor image. Qualified overlay2/XFS project quotas and actual allocation
enforcement evidence are required; a storage label is not proof. Provisioning
requires separate permission. No Docker/WSL installation or networking change
occurred. See [live qualification](SELECTIVE-LIVE-QUALIFICATION.md).

After separately approving image/dependency preparation, use the packaged
localagentbridge/executor_assets directory as build context. Supply an
operator-verified Linux Python >=3.12 base image digest:

```text
docker build --build-arg BASE_IMAGE=python:3.12-slim@sha256:VERIFIED_DIGEST -t lab-openhands:local localagentbridge/executor_assets
docker image inspect lab-openhands:local --format "{{.Id}}"
```

This is a prerequisite recipe, not an executed command. Record the resulting
sha256 image ID, dependency inventory and base digest; configure that immutable
ID, never the mutable tag. The image must include the acceptance-test dependencies
needed by the task. LAB never installs missing packages during execution.

Containers have network=none, no bind mounts or volumes, no Docker socket, no
host PID/IPC/UTS namespace, no capabilities, no-new-privileges, bounded memory,
swap, CPU, process count, file size, log size and writable storage. The selected
tracked files are copied into a root-owned read-only directory. Only explicitly
permitted existing/precreated UTF-8 files are writable by UID 10001. Initial
support excludes deletion, renaming, binary edits and arbitrary new directories.
Missing context/dependencies must return to Codex; do not broaden mounts.

The SDK talks to a loopback server inside its own networkless container.
The trusted LAB worker mediates an allowlisted inference mailbox with the chosen
host provider. There is no host address or network route available to model tools.
Only TerminalTool and FileEditorTool are registered; no subagent/task tool,
browser, plugins or runtime MCP tools are enabled. Model-authored shell commands
run only inside that container. Logs/conversation persistence remain task-local.

## Contract and review commands

Copy examples/selective.toml to a separate local configuration. Set source_root,
data_dir, exact model identity and relevant skills; do not replace personal defaults.
Start companion start outside the MCP server process tree, then create a run
using the existing companion create command. Submit an array based
on examples/selective-contract.json, approved by the supervising Codex session.

```text
python -m localagentbridge --config LOCAL.toml companion contract-route --request tasks.json
python -m localagentbridge --config LOCAL.toml companion contract-submit --run RUN --request tasks.json
python -m localagentbridge --config LOCAL.toml companion start
python -m localagentbridge --config LOCAL.toml companion status --run RUN
python -m localagentbridge --config LOCAL.toml companion contract-review --event EVENT --candidate HASH --outcome accepted --validation "Reviewed actual diff and checks" --coverage coverage.json
python -m localagentbridge --config LOCAL.toml companion contract-integrate --job JOB --candidate HASH
```

When selective.enabled is true, MCP exposes companion_contract_submit and
companion_contract_status using the same admission/store. Submission only queues;
it reports controller_not_running when the separately launched controller is
unavailable. It never spawns workers inside the MCP client's Windows job object.
Reconnection reads the same durable job. Contract review/integration are not
exposed through MCP.

Dry-run does not submit/infer. The logged override cannot bypass identity,
permissions, risk, qualification or sandbox restrictions. Missing/ambiguous
requirements return to Codex. A direct decision returns control; it does not spawn
Codex or dispatch a direct-lane callback. Existing auto/direct/workflow APIs remain
available for their original advisory stages/checkpoints. Contract jobs are
bounded units scheduled by LAB, not a new general agent framework.

Implementation normally requires a reviewed SDK compatibility record AND an
explicitly qualified backend/identity/category/context tuple. An enabled pilot
permits only listed pilot categories, and still requires SDK compatibility and
all security gates. Start the fixed disposable SDK probe only when explicitly
authorized and after hardware/environment prerequisites are met:

```text
python -m localagentbridge --config LOCAL.toml companion contract-qualify-start --backend ollama --model EXACT_TAG --context-tokens 16384 --activate
```

Start the existing worker, inspect its patch, baseline and candidate checks,
then record exact-candidate review with contract-review. Finally,
contract-qualify-record --job JOB emits a capability_evidence configuration record.
It requires observed terminal AND file-editor calls followed by tool-result
messages. It does not qualify a task category or certify general coding quality.
The probe is an exception only for its generated disposable fixture.

Candidate bytes, patch, checks, skill versions/hashes, dependency candidates,
model identity and inference receipts are under companion/artifacts/JOB.
Baseline failures are retained separately. Any failed/skipped/truncated or absent
check prevents automatic verification from passing. Worker-written success text
cannot set verification or acceptance. coverage.json maps every acceptance ID to
the supervisor's actual review evidence. Read surrounding code as well as the diff.

Only contract-integrate applies a reviewed patch. It rejects unrelated edits,
checks dependency integration order, reruns the union of acceptance commands
in a separate sandbox and records the exact combined tree. It creates no commit,
merge or publication. Direct/advisory reviews acknowledge their handoff; they do
not claim a local implementation was integrated.

Use contract-correct --job JOB --note TEXT for the single bounded correction.
The original attempt and its review remain in history. Dependencies resolve the
authorized correction, which must preserve scope, acceptance and retry authority;
review all prior attempts before finalization.
Transport retries apply only to connection establishment; uncertain inference is
never replayed. Cancellation targets only owned containers. A pending reservation
requires independent inspection and contract-resource-release --job JOB --evidence
TEXT. Do not release it while uncertain inference might still be running. Retained
containers/artifacts are intentionally not automatically deleted.

## Migration, rollback and troubleshooting

Schema 3 adds contract/audit/resource/measurement tables to the existing companion
database. Existing rows, events, recoveries, workflow packets and usage are retained.
Test upgrade on a SQLite backup made while the old controller/worker is stopped.
Keep the old non-editable runtime fixed until it has relinquished its jobs.

Set selective.enabled=false to disable new admission while keeping history readable.
To restore an older runtime, use the pre-upgrade backup in a different data
directory and retain schema-3 evidence separately. Do not lower user_version,
delete tables, overwrite the only database or point an old worker at schema 3.

- Provider unavailable/wrong model: inspect the explicit routing reason; no substitute is tried.
- Sandbox/image/quota unavailable: provision the stated prerequisites; no host fallback exists.
- Context overflow: reduce relevant context or requalify a larger window; requirements are not silently cut.
- Finished but awaiting_review/verification_failed: inspect independent checks and actual patch.
- Restart with an uncertain intent: inspect the owned executor/provider; do not queue another inference.
- UI closed: the separate worker/controller continues. Use status or reopen the existing dock.
- Slow inference: no-deadline mode retains a connect timeout and bounded steps/output, without a generation deadline.


## Scoped read-only transport profile

`selective.sandbox.storage_profile = "readonly_tmpfs_v1"` requires an exact image
ID labelled for SDK 1.53.0 and the fixed transport. Preflight performs actual bounded
allocation tests; unsupported default containerd quotas still fail closed. This
profile caps CPU at 2, memory at 2,048 MiB, PIDs at 128, disables swap/Docker logs,
and enforces the smaller tmpfs limits in the qualification report. Completed
results must be durably collected before stop; lost tmpfs requires explicit
reconciliation, not replay. The controller separately caps job artifacts at 128 MiB.

Provider settings `temperature` (0â€“2), `reasoning_effort` (low/medium/high), and
Ollama-only `verify_loaded_context` (boolean) are optional. The latter requires
`/api/ps` to report the exact contract context after inference, before forwarding
tool calls. Advertised maximum context is insufficient. The pinned SDK reasoning
adapter preserves tool history; no model alias substitution is used. The SDK editor
uses exact existing-file writes in sealed directories; interruption may invalidate
that disposable candidate. Independent verification and exact supervisor acceptance
remain mandatory. Qualification evidence does not enable a production category or
activate a comparison pilot. No new default is selected by these settings.


For explicitly scoped Ollama qualification with `native_context=true`, optional
`draft_num_predict` accepts integers 0–16. Omission preserves the installed
model/runtime default. On the examined Ollama 0.40.2 llama-server path, zero
omits speculative draft launch arguments; independently verify the actual
launch and allocation before claiming the drafter is absent. This is distinct
from `think=false`. Never change a shared service, model tag or production
default to apply this per-request override. Draft removal is not a guarantee
that the main weights, KV cache and runtime workspaces fit the memory guard.

## Local checkpoint and accounting utility

The accepted deployment is checkpointed at bec07f63bc8a0991576d7392353f1a541615eeeb.
Later close-out commits add attribution and documentation. The active controller
continues using its original immutable installed wheel; the accounting utility
is a separate offline installation from the reviewed close-out source. Use its
Python executable for contract-usage-bind/import/report only. Do not upgrade an
active controller/worker or start a second controller against the same store.
Both installations use the same additive usage schema; private operations.txt
records their exact paths and verified commands.

Rolling back attribution code does not require changing Qwen, deleting usage,
dropping the metadata table or restarting the accepted controller. Use the prior
installed utility; old readers ignore the new table. Deployment rollback remains
the tested private rollback.py procedure above. The source checkpoints are local:
no push, merge, tag, release, unrelated repository routing or new pilot activation.

Human dock acceptance remains outstanding. Follow the single compact checklist
in the [manual draft](release-testing/selective-execution-issue-draft.md), observing
idle, running, awaiting review and completed; exact model/backend/usage; cancel;
and an explicit override followed by restart persistence. An open window or an
automated widget binding test does not mark these human checks passed.
