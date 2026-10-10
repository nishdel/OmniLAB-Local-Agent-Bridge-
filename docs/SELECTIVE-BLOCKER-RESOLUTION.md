# Selective execution blocker-resolution pass

Latest scoped result: [bounded MoE batch](OPENHANDS-STRONGER-QUALIFICATION.md#bounded-moe-configuration-batch--2026-10-10). Qwen35 independently completed fixture and UTC with full collection; Gemma passed a safe fixture but its UTC response exhausted output. Qwen27 remains preserved and was not rerun. Both pilots and general routing stay disabled. Earlier sections retain historical scope.

Historical bounded qualification: [qwen3:4b-instruct outcome](OPENHANDS-BOUNDED-QUALIFICATION.md).
Real SDK tool calls worked, but generated code failed protected acceptance; the
useful repository task remained gated for that configuration. New terminal/collector controls preserve
failed evidence and do not activate implementation or either pilot. Earlier model
results below remain historical, configuration-specific evidence.

Latest status: see the [scoped OpenHands qualification](SELECTIVE-LIVE-QUALIFICATION.md#scoped-openhands-qualification--2026-10-09). It supersedes earlier installation, transport and model-safety blockers; the historical results below retain their original identities. Pilots and production implementation remain inactive.

Historical 2026-10-08 evidence. The [installed-model follow-up](SELECTIVE-LIVE-QUALIFICATION.md#installed-model-follow-up--2026-10-09)
supersedes its four-model inventory and timings, records the fresh nine-tag screen,
and retains the unresolved real SDK/context/transport gates and separate approval
packages. It also records later unintended Ollama cache and GPT tag changes.

This is a continuation on `codex/selective-local-execution`, based on
`0b817c572a81a22c94988cdbf163d214957985b7`. No runtime, test, dependency pin,
production default or security gate changed in this pass. Only qualification
documentation changed. No installation, image pull, model download, driver
change, commit, push, merge or publication occurred. Both pilots remain inactive.

Private evidence is in workspace `data/selective-blockers-20261008/` (B below).
Earlier evidence remains in `data/selective-egpu-qualification-20261008/` (Q).

## Regression closure and exact candidate

The complete source suite passed: **508 passed, 1 skipped, 795.89 seconds**.
All **225** cases from Q/regression-complete.xml are present and passed in this
run; they are a subset, not an additional count. The one skip is the existing
Windows symlink privilege condition. Coverage includes legacy bridge,
auto/direct/workflow routing, profiles/skills/budgets, durable recovery and real
crash boundaries, cancellation, native Tk controls, research fixtures, selective
providers/contracts/review/integration and MCP/process tests. Model services in
these automated tests are synthetic.

Source manifest at execution:
`5651d4c8172c411c2771c6e2f9704695920af92e4abd48338bfbaa3a9e999e2d`.
B/source-before.json records every file hash. B/full-regression-summary.json
confirms no source changed during the run and no old subset cases were missing.

**97 selective tests passed in 28.82 seconds against the installed final wheel**,
outside the checkout. This overlaps source coverage and is not added to it.
Wheel SHA-256:
`42de265e805c4b2216f40cb5db5bea5f6fe238275f45eccf49b26768785c4233`.
B/installed-runtime-identity.json records the actual import directory and zero
byte mismatches against every packaged runtime file, including executor assets.
This is final-artifact testing, not an inference from normalized line endings.
An initial command pointed to a nonexistent copied-test directory; it ran no
tests, is retained in installed-final.log, and is not counted as a regression.

The existing 15-second crash-fixture allowance changed no production deadline.
The complete run includes actual lease-expiry recovery and late-result guards.
An additional deterministic diagnostic on the installed workflow store advances
only that module's clock: ownership works immediately before the actual expiry;
reserve, result and finish all reject at and after expiry; recovery preserves the
spent reservation and hands off as interrupted. It neither sleeps nor changes the
stored expiry. See B/deterministic-expiry.json. These diagnostic assertions are
not added to pytest counts. No further timeout increase or weakened assertion
was needed.

Ruff, all 43 Markdown/config/CLI documentation checks, the 217-file public-source
audit and git diff --check passed after the documentation update. The final
preservation record confirms unchanged clean original development/release trees
and no remaining owned probe containers. Runtime and tests remain byte-identical
to the full regression and installed-wheel runs. Updated source-distribution
identity/contents are recorded separately; the tested executable wheel stays fixed.

## Live environment findings

| Component | Actual hardware/model | Live check | Result | Evidence | Remaining blocker |
|---|---|---|---|---|---|
| RTX / existing inference | RTX 3060, 12,288 MiB, driver 560.94; same UUID as Q | Read-only recheck; earlier inference evidence retained | Previously live verified; driver unchanged | Q GPU logs; B driver/property records | No new inference or long-term stability claim |
| Existing Ollama assets | Four exact manifests in the user-supplied model directory | Read manifests and verify referenced blobs exist | Current inventory verified | B/existing-model-bindings.json | Previously qualified qwen3:4b tag is now absent; do not substitute qwen3:4b-instruct silently |
| Docker storage / memory | Docker 29.6.2, WSL2 Linux 6.18.40.1, cgroup v2, containerd overlayfs, ext4 Docker data | Read-only root and bounded tmpfs actual write probes | Limits enforced in diagnostic container | B/readonly-probe.json | Current LAB adapter still uses the incompatible copy/exit lifecycle |
| Protected fixture files | Same cached image, UID 10001, no capabilities/network/mounts | Trusted initialization; diagnostic edit/test; deny acceptance write/chmod; collect actual bytes | Environment operations passed; **not an OpenHands execution** | B/readonly-exec-seed-probe.json, readonly-artifact-probe.json | Pinned SDK installation and adapter qualification |
| OpenHands 1.53.0 image | Linux/amd64 | Anonymous registry manifest/config inspection | Published and reachable; missing locally | B/registry-1.53.0-python.json, sdk-image-manifest.json | Published server binary is not the Python SDK environment required by this runner |
| LAB â†’ OpenHands â†’ Ollama | No qualified SDK image / suitable model combination | No SDK task submitted | **Blocked, not tested** | B/approval-openhands.json | Approval, restricted transport/lifecycle fix, real SDK tool round trip and independent review |
| Strata / OpenHands â†’ Strata | Coder IQ1_M; RTX alone proposed | Dependency/source/engine/MTP metadata investigation | Prepared; **not tested live** | B/approval-strata.json and linked manifests | Assets, driver/runtime decision, whole-system fit and each independent live gate |
| Human dock checks / pilots | Existing candidate | No human UI exercise or pilot | **Not tested / inactive** | Existing manual ledger | Explicit human checks and later pilot activation |

Read-only recheck at **2026-10-08T20:34:43.8579744Z** confirms **34,139,435,008
bytes installed RAM**, RTX **12,288 MiB**, driver **560.94**, PCI 07:00.0 and
the same NVIDIA UUID (retained privately). Idle GPU allocation was 511 MiB.
Available physical memory was 20,216,584 KiB; free storage was
135,002,558,464 bytes on C and 2,978,172,481,536 bytes on D. This idle snapshot
is not a combined model/SDK memory qualification. See B/hardware-final.json.

The model directory currently contains gpt-oss:20b, qwen3:14b-q4_K_M,
qwen3:4b-instruct and qwen3-vl:4b. In particular, the earlier qwen3:4b manifest
is absent. qwen3:4b-instruct is a possible small fixture candidate, subject to
fresh exact-binding, tool-schema, context and real SDK qualification; its name
and shared weights, if any, do not transfer acceptance from another tag.
No model was created, deleted, renamed or substituted by this pass.

Read-only inspection of the existing Ollama 0.40.1 service at
2026-10-08T20:37:10Z confirmed the 4b-instruct tag digest matches its on-disk
manifest. It reports Qwen3 4.0B / Q4_K_M, tools/thinking/completion capabilities
and a 262,144 model context ceiling; no model was resident. Those advertised
capabilities and ceiling do not prove reliable tool use or feasible context on
this machine. Keep the proposed fixture at 16,384 pending actual SDK measurement.
No generation or service change was requested. See
B/existing-ollama-model-capabilities.json.

## Selected sandbox plan and measured limits

Prefer the existing Linux engine with a read-only root and bounded writable
mounts for the small fixture. No global Docker storage migration, WSL change,
GPU passthrough, host mount or broad inference listener is required.

Diagnostic limits were workspace 64 MiB, temporary files 32 MiB, home/state
32 MiB, exchange 16 MiB and shared memory 8 MiB: **152 MiB total data capacity**.
Each allocation wrote real nonzero bytes until ENOSPC; st_blocks matched bytes
allocated, not sparse size. Root writes failed with EROFS; creating a file in
/dev failed for the worker. The default /dev tmpfs is 64 MiB and root-owned;
proc/sys/cgroup protections and all actual mount flags are recorded. POSIX
message queues, pipes and process/kernel memory also need their cgroup/ulimit
bounds preserved. No filesystem is left as an unlimited worker scratch area.

The diagnostic used 512 MiB memory, swap disabled, 0.5 CPU and 32 PIDs.
Peak sampled memory.current during its largest sequential allocation was about
86.4 MB. Tmpfs is charged inside the memory cgroup, not extra memory.
For the SDK fixture propose the existing 2 GiB RAM / 2 CPU / 128 PID limits,
152 MiB writable data, 8 MiB shm, no swap, bounded file sizes, file descriptors
and message queues. Windows, WSL, LAB, Ollama and KV headroom still require a
fresh combined measurement; the old 17.66 GB host-headroom sample excludes SDK
execution. Keep one inference job and one active sandbox at a time.

The probe selected Docker's **none logging driver**, so container stdout cannot
grow daemon log files. Controller diagnostics/artifact capture must remain bounded
by the contract and a proposed 128 MiB total fixture-artifact allowance; that
aggregate allowance still needs implementation/testing with the new profile.
Existing historical evidence is not pruned to make room.

Compatibility failure is concrete: docker cp into either / or /workspace fails
with a read-only-root error. Copying out observes the underlying image path,
not the live tmpfs content. Do not enable this profile just by dropping
--storage-opt. A trusted, fixed initialization command through docker exec
successfully creates protected root-owned files; UID 10001 can edit only the
permitted file, cannot write/chmod the root-owned acceptance file, and a
bounded exec-based read collects the changed bytes and hashes. Diagnostic
acceptance ran with exit 0. This uses ordinary Python, **not SDK tool calls**.

Before activation, adapt the existing sandbox transport to fixed, bounded
exec-based initialization/mailbox/collection, keep the container alive until
artifacts are durably collected, and reconcile interrupted collection without
replaying the agent. A lost tmpfs after container/VM shutdown must escalate,
not claim recoverable output. Run scope/ownership/cancellation/restart tests
and independent verifier checks against this exact profile. The existing
overlay2/XFS gate stays unchanged until that replacement passes. No unrestricted
host fallback or broader permissions are proposed.

## OpenHands approval manifest â€” independent of Strata

This is a prepared approval package, **not permission to install**.

| Required component | Exact identity/source | Download / installed footprint | Preparation, privilege and rollback |
|---|---|---|---|
| Reused Linux/Python/tool base | Existing ghcr.io/openhands/agent-server@sha256:fd4b2c1255e1daac21e1a6b4dae0e21d77cc943c74ea193452f4f004d415ca39; Python 3.13.12, glibc 2.41; bash/tmux/git present | **0 new bytes**; Docker reports about 5.053 GB already retained (its image-inspect Size metric differs) | Reuse by exact ID/digest, never repull mutable 1.15.0 tag. Preserve this shared base and existing containers. |
| SDK + tools and full Python dependency set | Both **1.53.0**, source 54daf056bd863bb46f922a2fe9324dd736b37ff6; upstream uv.lock for Linux CPython 3.13; B/openhands-requirements.lock and resolved-artifacts.json pin every artifact/hash | **174 artifacts, 101,666,057 bytes**; wheel payloads expand to **363,741,223 bytes**; func-timeout 4.3.5 source expands to 236,830 bytes | Offline build of the one small sdist using the base's setuptools 82.0.1; isolated SDK environment; no host Python or compiler installation. Validate import/API and pip check after build. |
| LAB executor layer and restricted profile | Existing runner/API pin plus the narrowly scoped lifecycle changes above | No external artifact; estimated incremental installed footprint **0.5 GB**, reserve **2 GiB additional preparation storage**, including downloads/cache/build overhead | Existing Docker access; root only inside build/trusted initialization, worker remains UID 10001/cap-drop ALL. Clear inherited ENTRYPOINT and create a private SDK environment. Record final image ID only after build. |

Archive payload sizes above come from package metadata and range-read ZIP
directories, not an installation. The 0.5 GB and 2 GiB values are planning
estimates/reservations, not measured installed/peak usage. B/dependency-validation.json
reports no unsatisfied base requirements; requested extras were resolved from
the pinned upstream lock. No browser, browser download, autonomous subagent or
hosted provider is activated by installing transitive packages.

Registry investigation independently resolved the published 1.53.0-python
Linux/amd64 manifest to
`sha256:a6865fc1da99c6e1038c70fde59df237d16d48ac30aadcc9a98916dc56bcf7a0`,
with **1,202,198,853 bytes** of compressed layers. Its config records the same
SDK source revision, but launches a packaged agent-server executable. It is
not selected as a drop-in Python SDK environment and is not a required download.
No mutable latest tag or SDK upgrade is proposed.

Rollback: stop only verified owned jobs/containers, remove the newly recorded
image/build references and private wheelhouse/SDK directory, and keep the
pre-existing image, user containers, models and durable evidence. No system
configuration change or administrator driver action is part of this approval.

## Strata approval manifest â€” separate and deferred

Pinned source:
`fb58e0dbc8399662c0e47c76578c6e878b14f6cf`; engine **0.1.41**.
Only Coder IQ1_M at model revision
`5348543e0147355ac9cbcb031184a3546350988e` is proposed, with Apache-2.0
weights. IQ1_M is the variant's name; upstream describes mixed precision and
expert pruning, so do not interpret it as uniformly one-bit weights.

| Component | Exact source / identity | Download bytes | Retained/preparation footprint |
|---|---|---:|---|
| Strata source and pinned llama.cpp tooling | Source above; llama.cpp 3cf03257f219afbe7334045ff7c6a06ac68c627d; every blob path/hash in B/strata-source-artifacts.json | 38,603,031 + 172,252,331 for verified raw-blob export | Same source payload plus filesystem overhead; no engine/compiler build or submodule fallback |
| Coder two GGUF shards | Model revision above; SHA-256 e11083ba855e7666b48ea3f2db6a9c3a20c18751a012cc24f948de91b7087fad and 316b46f3a2dbd68c900f43136ab9449f9dcc3725dfd8c794847c204bc161e113 | **58,408,584,928** | Retain originals; low-RAM preparation writes an additional approximately 23.4 GB experts.bin per upstream; generated dense/tokenizer files also retained |
| MTP draft source | Qwen/Qwen3.8-Flash-Next revision de4b8e4d43b917e7706784d8bb445c9af86a3540; 31 tensor hashes/ranges across 28 shards in B/strata-mtp-inventory.json | **5,214,301,696** | Packed tensor payload calculated from shapes/formats: 889,014,272 bytes; retain source, packed GGUF and generated runtime data; no whole-checkpoint download |
| Private Python dependencies | Exact Windows CPython 3.13 wheels from pinned requirements; B/strata-python-artifacts.json | **63,876,701** | Expanded payload **159,991,559** bytes; reuse installed Python 3.13.14 and existing C++ runtime 14.51.36247.0; new private venv only |
| Standard CUDA 13 engine/libraries | Engine zip SHA-256 3dd7715f4844c0f9d2f28eb5067af0198f386df060c93523cd17e1d65b757f13; nvidia-cublas 13.0.2.14, nvidia-cuda-runtime 13.0.96 | **137,164,559 + 404,814,317** | Expanded **272,636,570 + 542,057,965** bytes; RTX alone, driver >=580 required |
| Experimental alternative, replaces previous row | CUDA 12 zip SHA-256 646ded0105aa5213a75e16621d559670d09dac26b5c720c9fd651ca83bdf14ec; nvidia-cublas-cu12 12.9.1.4, nvidia-cuda-runtime-cu12 12.9.79 | **198,572,838 + 556,745,503** | Expanded **390,717,714 + 783,536,342** bytes; older-driver behavior is unqualified upstream |

Total planned payload: **64,439,597,563 bytes standard**, or
**64,652,937,028 bytes experimental CUDA 12**, excluding HTTP overhead and any
separately approved driver package. Source totals use raw blobs to make the
transfer budget explicit, not an unmeasured compressed archive. Asset integrity
must be checked after approved retrieval; metadata hashes alone are not a local
artifact verification.

Estimated retained install is **90â€“95 GB**, estimated preparation peak about
**100 GB**; reserve **120 GiB** before starting. Generated pack/filesystem
overhead and actual peak cannot be measured without preparation. These estimates
are not proof of RAM fit. No extra model family, vision asset, compiler, CUDA
toolkit or silent newer-release fallback is included.

No administrator privileges for the private directories/venv. Keep loopback
binding, disable Strata tools/MCP, use the RTX UUID alone, initially propose
16,384 context / int8 KV / vision off / low-RAM mmap, and measure actual
Windows + LAB + Strata + cache/KV headroom before adding the SDK sandbox.
Rollback removes only newly approved task-owned source/runtime/model/pack
directories after owned-process shutdown; retain Ollama assets and evidence.
Do not activate this package until the driver/runtime choice below is resolved.

## Driver investigation and recommendation

Windows 10 Home 19045 is unchanged. The RTX device is PCI VEN_10DE/DEV_2503,
the Dell GTX 1060 Max-Q is VEN_10DE/DEV_1C20, subsystem 08251028.
The GTX reports Code 31 and NTSTATUS 0xC0000182 (device configuration error).
Its assigned package is oem80.inf / 582.66; the RTX uses oem42.inf / 560.94.
The shared nvlddmkm service points to the 560.94 DriverStore binary.
SetupAPI records Windows Update installing the RTX 560.94 package on October 8
and modifying that existing service. Available logs do not contain a definitive
GTX failure transition. A driver mismatch is a supported hypothesis; neither a
broken GPU nor a proven cause is established.

[NVIDIA's 581.80 release notes](https://us.download.nvidia.com/Windows/581.80/581.80-win11-win10-release-notes.pdf)
list Windows 10 1803+ x64, desktop RTX 3060 and notebook GTX 1060. This common
WHQL package meets Strata's numerical >=580 requirement for the RTX alone.
The official desktop DCH installer HEAD reports **896,544,928 bytes**.
Exact Dell subsystem binding still needs package-INF/OEM confirmation before
installation; generic product support is not Dell certification.

**Do not use this as a routine driver-upgrade recommendation.**
[NVIDIA's May 2026 bulletin](https://nvidia.custhelp.com/app/answers/detail/a_id/5821/kw/support)
identifies pre-582.53 R580 versions as affected for Pascal. The installed newer
[582.66 security package](https://www.nvidia.com/Download/driverResults.aspx/272768/en-us/1000/)
lists legacy GPUs, not RTX 3060. A single currently security-maintained official
GeForce package covering both exact devices was not verified.
Prefer keeping the working RTX configuration for Ollama/OpenHands and obtaining
Dell/NVIDIA guidance on a common supported package before changing drivers.

A driver change would be a separate administrator/reboot operation. Before
approval: verify both hardware IDs in the proposed signed package, preserve
oem42/oem80 exports and the working 560.94 installer, record current bindings and
create an appropriate restore/recovery point. If the RTX qualification regresses,
restore the recorded working package/bindings and repeat its short exact-model
check. No driver cleanup, device disabling, BIOS change or automatic rollback
was performed.

Strata's [experimental CUDA 12 guidance](https://github.com/Niko1221/Strata/blob/fb58e0dbc8399662c0e47c76578c6e878b14f6cf/docs/OLDER_GPUS.md)
allows explicit CUDA 12 on an RTX and gives a Windows floor of 528, while saying
such older drivers were not tested upstream. Current 560.94 passes that numerical
floor but is **not qualified** for this engine. It avoids a driver change but is
a separately approved experimental route, not equivalent to the standard route.
Do not select both GPUs or pool their VRAM.

## Next decision and pilot readiness

No real OpenHands/Ollama implementation task succeeded: none was submitted because
the required SDK environment is not installed and the new restricted transport is
not yet implemented/qualified. Environment diagnostics are not substituted for
that result. Model tool-use, SDK protocol, candidate review/integration and bounded
correction behavior remain live qualification gates.

The smallest next approval is **OpenHands only**: the 101,666,057-byte pinned
dependency set and isolated image build, with 2 GiB preparation allowance. It
requires no Strata, GPU driver update or system reconfiguration. Then qualify the
restricted adapter and actual terminal/editor/acceptance loop with an existing
exact model, inspect the real diff, independently verify it, and bind supervisor
acceptance to its candidate hash. Keep implementation disabled until all pass.

A future Codex-only versus Ollama-hybrid comparison can run without Strata once
this combination qualifies. It must be an explicitly approved, separately named
protocol with fresh independent starting revisions and the same acceptance
checks. The original eight-case/three-lane protocol is unchanged and inactive.
Neither smoke checks nor this regression result establish token savings, quality
equivalence or release readiness.



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
