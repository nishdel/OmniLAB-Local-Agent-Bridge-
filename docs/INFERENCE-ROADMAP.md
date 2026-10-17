# Inference qualification roadmap

**Current implementation:** Ollama and Strata are the two allowed backend values
in [Contract](../localagentbridge/task_contract.py#L73) and
[ChatProvider](../localagentbridge/inference.py#L105). They supply inference.
OpenHands supplies implementation tools and the agent loop. The three task lanes
and their independent gates are documented in [Workflow](WORKFLOW.md).

## Preserve the working baseline

Ollama advisory remains a supported path regardless of Strata's outcome.
Qualified OpenHands/Ollama cases remain limited to their recorded identities,
contexts, task scopes and resource profiles. A matching model name alone is not
qualification. Fresh admission rechecks identity, resource fit and ownership.
See [Ollama/OpenHands evidence](OPENHANDS-STRONGER-QUALIFICATION.md).

## Strata: implemented, experimental, not enabled by this roadmap

Strata is an alternative inference provider behind the existing OpenHands SDK →
restricted mailbox relay → trusted OmniLAB worker → inference backend transport.
The adapter and exact context accounting are implemented; historical patched
text/protocol probes and offline SDK evidence do not establish live implementation
qualification. See the [existing implementation report](SELECTIVE-IMPLEMENTATION-REPORT.md)
and [provider tests](../tests/test_selective_providers.py).

The next target is **Qwen3.8-Flash-Next GSQ-RCO Coder, IQ1_M**. Strata's official
[model guide](https://github.com/Niko1221/Strata/blob/main/docs/MODELS.md) recommends
Coder for 32 GB systems. The linked artifact publisher is
[ISTA-DASLab](https://huggingface.co/ISTA-DASLab/Qwen3.8-Flash-Next-GSQ-RCO-Coder-GGUF),
not the Qwen organization itself. Record that provenance accurately rather than
calling an unverified conversion an official Qwen release.

At the 2026-10-17 inspection the personal Strata installation already contained
both target shards (29,608,446,496 and 28,800,138,432 bytes), and its frozen serving
configuration selected `qwen3.8-flash-next-coder-iq1_m`. No additional download is
needed merely to select this target. File presence and byte counts are inventory,
not proof of RAM fit. The addendum's full checksum reconciliation and pinned
publisher identities are recorded in the [standalone guide](STRATA-STANDALONE.md).
Recheck all selected artifacts before the next authorized run. Do not silently
upgrade the pinned runtime.

The manufacturer's size recommendation is not this Windows machine's acceptance
result: OS/apps, model mappings, GPU staging, cache/context, Docker and OpenHands
must fit together with retained headroom. The existing memory, context, output,
retry, ownership and cancellation gates remain unchanged.

## Required sequence before implementation enablement

| Gate | Required evidence | Current status |
|---|---|---|
| Provenance | Exact model shard hashes, publisher revision, engine/serving/tokenizer identity and license | Fresh shard/publisher and installed-artifact hash reconciliation passed; recheck before the authorized run |
| Preflight | Available/committed RAM, GPU use, pagefile activity, disk/evidence budget, idle competing workloads, exact LAB reservations and an exclusive owner | Must be sampled immediately before the authorized session |
| Standalone serving | Approved bounded localhost startup, browser/API checks, correctness, resource telemetry, cancellation, unload/shutdown and restart | BLOCKED: independent live launcher unqualified, approval consumed and resource gates fail; earlier narrow probes are historical |
| Real OpenHands work | Disposable fixture, exact permitted edits, actual `file_editor` and `terminal` invocations, protected baseline/candidate tests and independent diff review | Not qualified for Strata |
| Negative cases | Forbidden path/test/tool refusal; invalid response; timeout; bounded retries; worker/provider failure and evidence retention | Offline coverage is distinct from live evidence |
| Cancellation/recovery | Owned process termination or honest unresolved-inference state, reservation retention/reconciliation, no replay, no effect on unrelated apps | Live qualification incomplete |
| Acceptance | Exact backend/identity/category/context/image/SDK record and independently accepted candidate | No production admission granted |

Use the existing [selective contract](SELECTIVE-EXECUTION.md) and qualification
fixtures. Require a baseline that detects the defect and protected tests that
pass only after the permitted change. Retain tool messages, before/after hashes,
test argv/exit status, output truncation, elapsed time, usage and resource peaks.
An API response containing a tool call is not evidence that the tool executed.

Stop on admission failure, paging/driver/resource violations, ambiguous ownership
or cancellation uncertainty. A proposal to change limits needs its own evidence
and explicit authorization. A successful text answer does not waive these gates.

Independent Strata operation is a mandatory **BLOCKED** acceptance item. The
installed Control opens, but it does not yet provide a qualified live Strata
launcher. Browser/API source exists; current standalone inference, cancellation,
shutdown and restart have not passed acceptance. Follow the separate
[standalone guide](STRATA-STANDALONE.md), then the
[OpenHands/Strata guide](OPENHANDS-STRATA.md). Neither can be marked successful
from installation or synthetic checks. Independent local-supervisor research is
tracked separately in [future directions](research/JANAS.md).
