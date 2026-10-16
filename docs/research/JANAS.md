# Independent Janas supervisory-agent research

> Janas is an independent experimental inference runtime being evaluated with Qwen3-Next-80B-A3B as a potential foundation for future local supervisory-agent research. It is not integrated with OmniLAB, is not required to install or operate OmniLAB, and is not an approved alternative to Codex.

**Research objective, not an approved architecture change.** The target is
[Qwen3-Next-80B-A3B-Instruct](https://huggingface.co/Qwen/Qwen3-Next-80B-A3B-Instruct).
The model publisher identifies it as an 80B total / 3B active-parameter MoE with
instruct-only output. Active parameter count does not specify total memory or
storage requirements. [Janas upstream](https://github.com/prabanta-dev/janas)
reports support and measurements on its own hardware; those numbers do not
establish performance on this Windows computer.

## Deployment boundary

Preserve the separately installed Janas Control application, its existing models
and historical evidence. Keep new tests, manifests, logs and any future agent
harness outside OmniLAB production and development configurations. Do not add a
provider, OpenHands backend, routing choice, dependency, Docker service, default
or automatic fallback to OmniLAB. Existing experimental preparation is historical,
including any earlier proposal to integrate it; this scope supersedes that proposal.

The current OmniLAB schema accepts only `ollama` and `strata`
([Contract](../../localagentbridge/task_contract.py#L73),
[ChatProvider](../../localagentbridge/inference.py#L105)). No change to that schema
is part of this research. Shared use of the Windows computer still requires fresh
resource and ownership checks; isolation is not permission to compete for memory.

## Phase 1: establish feasibility on the actual computer

Before downloading or loading the 80B model, produce an explicit approval package:
exact Janas release/source/binary hashes and license; exact Instruct model and
conversion/quantization provenance and checksums; measured available disk and
download/temporary/evidence budget; Windows CPU/GPU/driver compatibility; current
RAM/commit/pagefile state; SSD read evidence; competing workloads and a finite
exclusive window. Preserve existing thresholds. Do not reuse the 35B model's
startup authorization for 80B or assume identical quantization labels mean
identical tensors.

After authorization, start with a bounded correctness and resource probe under
independent containment and monitoring. Measure prompt processing, time to first
token, generation speed, peak private/committed/resident and mapped memory,
paging, disk I/O, GPU use and cancellation/timeout behavior. Record cold and warm
conditions separately. No large artifact download, heavy inference or admission
relaxation is authorized by this document.

## Phase 2: separately controlled capability tests

Only after practical inference feasibility is established, freeze an isolated
fixture suite with hidden acceptance checks and explicit read/edit/test permissions.

| Capability | Controlled evaluation |
|---|---|
| Reasoning and planning | Identify missing requirements, dependencies and uncertainty; compare plans against an independent rubric |
| Implementation decomposition | Split a small feature into bounded contracts without inventing authority or omitting acceptance |
| Tool-call reliability | Valid schemas, correct arguments, denied paths, malicious repository instructions and bounded recovery |
| Code review | Seeded defects, false positives, security implications and evidence-backed findings |
| Verification | Detect failing/omitted tests, stale results, incomplete changes and unsupported success claims |
| Supervision/recovery | Durable state, interruption, budgets, permission enforcement, rollback and independent final acceptance |

Report model-only outputs separately from orchestration supplied by a harness.
Use equivalent tasks and account for rejected results, retries, repairs and review
time. Successful inference of an 80B model is not proof that Janas replaces Codex.
A viable local supervisor also needs workspace tools, permissions, recovery,
verification and acceptance controls that the evaluated model cannot waive.

**Status:** 80B feasibility and supervisory qualification are not established.
No claim of Codex replacement, passed supervisory evaluation or OmniLAB integration
is made. The normal [OmniLAB workflow](../WORKFLOW.md) continues independently.

The separate installed 35B CPU probe later returned `JANAS_OK` (22 prompt tokens,
4 output tokens; about 14.52 seconds to first token and 18.19 seconds for the full
request). This is a short correctness observation from 2026-10-16, not an 80B
measurement, a representative speed benchmark or supervisory qualification. It
supersedes older private notes saying that no Janas inference had yet run; it
does not change this research boundary or authorize another startup.

## Dated feasibility inspection: 2026-10-17

**VERIFIED: metadata and installed-source compatibility declarations.** The
installed v2026.10.14 source snapshot
[`afb874e4`](https://github.com/prabanta-dev/janas/blob/afb874e4da84d72584175b59ea153dc15ce648e1/src/common/catalog.c)
lists the Instruct target, its Q4_K_M input, JNS output and expected hashes;
[`arch.c`](https://github.com/prabanta-dev/janas/blob/afb874e4da84d72584175b59ea153dc15ce648e1/src/llm/arch.c)
registers the Qwen3-Next architecture. This establishes intended support, not a
successful Windows load or tool-use evaluation.

| Candidate | Pinned metadata | Download size and SHA-256 |
|---|---|---|
| Qwen's Q4_K_M GGUF input | [Qwen revision 4c8630cf](https://huggingface.co/Qwen/Qwen3-Next-80B-A3B-Instruct-GGUF/tree/4c8630cf7af926a9c5095cb4bbbbc65d36e20f77) | 48,410,988,384 bytes; `d103b2733ec1012a52d01edda66b7e5c24ae50508c9f99f5297ea459ef3c061a` |
| Janas publisher's prepared JNS | [prabanta-dev revision 2ee57d76](https://huggingface.co/prabanta-dev/Qwen3-Next-80B-A3B-Instruct-JNS/tree/2ee57d760d376b590f10342617709632087e4c19) | 48,411,922,432 bytes; `fa3255c73106391e9cb5a97efd30f77a928fb4518d40060f795a8cff6656daed` |

Both metadata records declare Apache-2.0. The prepared JNS is about 45.1 GiB;
the old catalog's approximate `jns_gb=49.35` is not the current file byte count.
Prefer exact pinned metadata for a future storage budget. The known model
directories contain the existing 35B model, not this 80B target. No 80B artifact
was downloaded. Do not download both GGUF and JNS unless conversion comparison
is explicitly required; reserve extra space for partial files, conversion,
optional MTP and evidence before requesting a download to D:.

**BLOCKED: practical host fit and live feasibility.** The inspected computer has
32 GB physical RAM, an i7-8750H and a 12 GB RTX 3060 eGPU. The model file exceeds
RAM, so viable operation depends on Janas's disk-backed expert loading/cache
behavior, context and bounded workspace; 3B active parameters do not make the
whole artifact resident. The older Windows CPU and eGPU/SSD path need their own
measurements. No representative SSD-streaming benchmark or 80B throughput has
been measured here, and upstream throughput is not transferred to this host.

Fresh readiness sampled about 19.2 GiB free, below the unchanged 22.5 GiB gate,
with competing Docker/VM processes and a consumed single-start approval. No
listener was present. The installed configuration and supplied screenshot both
show **port 18086**, correcting the addendum's 8086 transcription. The current
configured model remains Qwen3.6-35B-A3B Q4_K_M; its short historical CPU success
does not establish present operation or qualify the 80B model.

Janas Control's presentation and Start Menu location now identify independent
research. Its installed supervisor, model, approval record and admission limits
remain unchanged. Historical shared-host pause checks in that private controller
are admission safeguards, not an OmniLAB inference route or production dependency.
Keep future 80B manifests and any supervisory harness isolated from LAB stores
and configurations; do not convert this research into an integration.

**NOT TESTED:** 80B startup, memory/VRAM and disk behavior, sustained throughput,
stability, cancellation, coding, structured tool calls, planning, review and
supervisory verification. Next: prepare the isolated artifact/storage/containment
plan, secure an exclusive admitted window and obtain new download/live-test
authorization. Do not reuse the old 35B approval or relax its guards.
