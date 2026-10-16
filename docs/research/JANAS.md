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
