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
| Strata | Optional adapter; no runnable installation/assets found in bounded known locations | Disabled; no verified Strata URL or live qualification |
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

The inspected upstream remains
[fb58e0dbc8399662c0e47c76578c6e878b14f6cf](https://github.com/Niko1221/Strata/tree/fb58e0dbc8399662c0e47c76578c6e878b14f6cf).
[Models](https://github.com/Niko1221/Strata/blob/fb58e0dbc8399662c0e47c76578c6e878b14f6cf/docs/MODELS.md)
supports Flash-Next variants, not the dense qualified Qwen27 combination.
The bounded path/process/loopback checks found source/approval records, not an
installed runtime or complete compatible weights. No installed commit, loaded
weight identity, effective settings, tool round trip or safe fit is established.
The proposed Coder package is a different model and needs its own qualification;
no assets were downloaded or duplicated.

Strata code is MIT; proposed Coder weights declare Apache-2.0. The standard
CUDA 13 engine's driver requirement is not met by the recorded 560.94 driver;
the documented CUDA 12 alternative remains unqualified. These facts do not
authorize driver changes. See the retained setup detail below.

The disabled example `http://127.0.0.1:8080` is a configuration example, **not an
available service address**. There is no verified Strata start/stop command on
this machine because no launchable installation was found. Before enabling it,
trusted orchestration must verify installed architecture/assets/hash/template,
effective runtime configuration, loopback-only sockets, and process/config binding.
Keep lifecycle and Strata MCP/control tools outside model control. The adapter
rejects aliases without a verified weight binding, unloaded services and broad
listeners. Its blocker does not disable Ollama/OpenHands.

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
manifest estimates 90â€“95 GB retained, approximately 100 GB peak, and reserves
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

For exact identity configure a trusted provider binding with family=coder,
identity, config_path/config_sha256, model_path/build_info, process identity and
artifact records. Each artifact records path, size, mtime_ns, SHA-256 and
verified_by_supervisor after independently hashing the installed bytes. The
identity is the canonical task_contract.digest of config_sha256 plus the artifact
path/size/hash list. Record the server's process_control.identity(), verify its
command names that configuration and that it owns the listening socket. LAB
rechecks process identity, socket, config hash, metadata and artifact stat records
at admission. It does not rehash tens of GB on every request. This binding trusts
the operator-controlled serving installation; a restarted/reconfigured server
requires a fresh binding. An echoed request name is never sufficient.

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
