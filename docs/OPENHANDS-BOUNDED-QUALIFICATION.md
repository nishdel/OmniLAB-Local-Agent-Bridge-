# Bounded OpenHands qualification — 2026-10-09

**No local implementation was accepted in this pass.** The requested exact
qwen3:4b-instruct completed real SDK tool calls, but its generated code failed
protected acceptance. The useful repository task remains gated. No other model
was substituted, and no Codex replacement patch was supplied.

Evidence directory: workspace `data/openhands-bounded-20261009/` (R). Historical
scoped/installed-model reports remain evidence for their own configurations;
their Qwen3.8 result does not qualify this model or the new bounded tool profile.
Branch remains codex/selective-local-execution, base
0b817c572a81a22c94988cdbf163d214957985b7, with uncommitted work preserved.

## Approved package and direct bootstrap

The approved 174 artifacts were already cached and installed by the retained
scoped pass. All artifact sizes and SHA-256 values were checked against the
original approval manifest: **101,666,057 bytes**. **New external downloads: 0**.
The existing SDK image's layer ancestry includes exactly the approved cached base
sha256:fd4b2c1255e1daac21e1a6b4dae0e21d77cc943c74ea193452f4f004d415ca39.
All 174 installed versions were checked; SDK/tools remain **1.53.0**. No dependency
resolution, version change, host Python installation or model download occurred.
R/approval-reuse.json and installed-sdk-identity.json retain the bindings.

The earlier measured SDK prefix allocation was **408,236,032 bytes** and its
conservative preparation accounting **1,164,693,186 bytes**, below the approved
2,147,483,648-byte reservation. New adapter layers are small measured additions;
final accounting is in R/preparation-final.json. Shared base layers are not counted
again. Accounted storage is not an exact whole-VM physical high-water reading.
No dependency/base substitution or budget increase was authorized or used.

Codex directly implemented and reviewed the bootstrap controls because this
implementation combination was not qualified. That is a **direct-execution
exception**, not work attributed to the local model.

## Bounded path and real control tests

The opt-in read-only profile now uses a bounded SDK terminal executor: only `cat`
of exact readable files and exact contract acceptance argv are permitted. It uses
no shell, denies chaining/redirection/input/reset, enforces command time/output
limits, and kills the created process group on timeout, cancellation or overflow.
OpenHands 1.53.0 still owns the agent loop. The SDK editor retains its exact-file
write restriction and now also limits reads to the declared snapshot paths.
Independent verification uses the same bounded process capture; truncated,
timed-out or incomplete checks cannot pass.

Resource/access boundaries remain: read-only root, 152 MiB combined writable
mounts, 8 MiB shm included in that total, 2 GiB RAM with no swap, 2 CPU quota,
128 PIDs, bounded descriptors/file sizes/message queues, disabled container logs,
no host mounts/credentials/database/model store/Docker socket, and network none.
Actual nonzero allocations reach ENOSPC at each writable limit. Root and device
writes are denied. Host artifacts have a separate 128 MiB per-job allowance,
including temporary writes; resource monitoring has an 8 MiB file allowance.

Live Linux checks exercised command denial, timeout, cancellation, output overflow,
storage exhaustion and missing command-audit collection. A fixed PID1 lifecycle
supervisor is required: Linux namespace init ignored the initial SIGSTOP attempt.
The supervisor leaves the SDK as an ordinary child; the controller can quiesce
owned worker processes, collect actual bytes/audit, then stop the container.
The successful and intentionally incomplete collection cases both remained failed
or cancelled diagnostics, never accepted work. The initial freeze failure is kept.
Host evidence exhaustion also guarantees an owned stop attempt; an unconfirmed
stop retains cancellation_pending. See R/live-controls.json,
final-live-collection-confirmed.json and the bounded regression cases.

The real model run exposed an earlier failure path that stopped before collecting
the partial candidate. Its SDK requests/tool observations and errors are retained,
but **its final candidate bytes were lost with tmpfs**. They were not reconstructed
from a model message. The subsequent collection fix was verified on actual SDK
startup/cancellation without further model inference. It cannot recover that old
candidate or turn the failed run into success.

Final sandbox image:
sha256:b0ec53df107bdbb7b9df9c397ee56d4f7f74bc49d6e6550b16ca6f23e5748090,
with bounded_v3 command/lifecycle binding. R/bounded-image-collection.json records
each asset hash. Live model inference used the earlier f1372ddf image; final
collection controls used the final image. These distinct live scopes are explicit.
Legacy quota restrictions and production defaults remain unchanged.

## Exact model, real SDK request and outcome

The existing Ollama **0.40.2** service at **127.0.0.1:11434** was reused, not
restarted. The tested tag is **qwen3:4b-instruct**, Qwen3 4.0B / Q4_K_M, digest
0edcdef34593eac1aa2be9c7d06c432dcf81945adca5eca2f27662c18f168ba0.
Per-request native Ollama context controls were added behind explicit
native_context=true; defaults retain the existing Chat Completions path. The SDK
continues to use Chat Completions at its isolated mailbox. Native conversion
preserves text blocks, reasoning and structured tool calls; unsupported content
fails rather than disappearing. No cloud fallback exists.

The scoped request used **32,768 context**, temperature 0, native think=false and
**1,024 maximum output tokens/request**, with the fixed SDK system prompt and
terminal/file_editor/finish/think schemas. The request/response transcripts remain
local, bounded artifacts; they are not copied into shared agent conversations.
Observed prompts were **5,707–6,939 provider tokens**. All nine completed receipts
verified loaded context 32,768 before tool delivery. The next request hit the
existing conservative byte-based admission guard; this was **not measured KV
context exhaustion**. No requirements, failures or history were truncated to pass.

There were two durable probe attempts: an initial HTTP 400 transport rejection
before generation (SDK text-block conversion was missing), then one explicit
correction of the same frozen fixture. No third attempt or model switch ran.
The corrected run made nine real inference calls. The model read the seed,
hallucinated an initial replacement without reading the source, added `self` to
a module-level function, received TypeError, then moved the function into a class
and received ImportError. Those are observed model/code errors, distinct from the
transport bug and final admission guard. The model was not accepted and no general
claim about its coding quality follows from this one configuration.

The scoped qualification entry point no longer requires activating a comparison
pilot or creating a Git commit. It still requires explicit activation, exact
identity/context/tool support, isolated enabled configuration and sandbox/memory
checks. Generated fixture inputs are frozen and hashed. Corrections retain their
original baseline and protected supplemental tests. No task/category qualification
record was fabricated after this failed fixture.

Observed run: **86.791 seconds controller elapsed**, **36.514 seconds summed
provider intervals**, **56,099 input tokens summed across requests / 762 output
tokens**. Cached/cloud token metrics are unavailable. These are smoke observations,
not savings, quality equivalence or a comparative result. Store attempt count is
two; only the corrected attempt reached model inference.

## Hardware and model preservation

RTX 3060 is **12,288 MiB**, driver **560.94**, on the same recorded UUID/PCI device.
Runtime logs identify CUDA0 as RTX 3060 and report 37/37 layers offloaded, 32,768
loaded context and 4,608 MiB GPU KV cache. `ollama ps` reports the exact tag,
7.5 GB allocation and 100% GPU. Physical GPU samples independently show activity
up to 100%, with **7,775 MiB peak sampled GPU memory**. CPU host buffers/control
still exist; “100% GPU” is not a claim of zero CPU use. Minimum sampled available
system RAM was **21,662,363,648 bytes**. Peak SDK cgroup usage during this failed
inference run was not collected; its enforced ceiling was 2 GiB. No OOM, device
loss or connection drop was observed in the completed requests. This is short
qualification evidence, not a stress or long-term stability result.

Model inventory was captured before and after. Existing tags/digests and weight
file identities remained unchanged, with no pruning, replacement, retagging or
large model write. The running service added **one 891-byte manifest blob**,
sha256:0ae3a216bb63b4270cd402040cccd50e8aa35d800775621ea319050f60bf047c.
That runtime side effect is retained and disclosed in R/model-runtime-side-effect.json;
it is not described as zero filesystem mutation. Selected existing blobs/manifests
were read-locked during the run without changing original ACLs. No driver, GTX
repair, Docker/WSL, host networking, firewall, DNS or Tailscale change was made.

## Useful repository task and review boundary

The prepared task targets only `timestamp(value)` in localagentbridge/codex_usage.py:
interpret timezone-free rollout timestamps as UTC while retaining explicit offsets,
fractional/pre-epoch values, invalid-input errors and every surrounding AST node.
The repository source and new protected acceptance/AST authority were frozen before
running anything. A fresh restricted verifier under a non-UTC timezone fails with
1767218400 instead of the required 1767225600. See R/task-scope.json,
task-contract.json and repository-baseline-confirmed.json.

That useful task **was not dispatched**: the required SDK fixture failed, so its
qualification/review gate did not pass. No Codex-written fix, substitute model,
weakened acceptance, acceptance record or integration was used to call it successful.
Its proposed budget remains two attempts, eight requests per attempt, 1,536 output
tokens/request, 15-second commands and 16 KiB command output within the same resource
profile. No new attempts are implied by retaining that prepared contract.

The failed jobs remain escalated/unaccepted. Owned stopped containers and the
now-idle service were reconciled before releasing the reservation. Historical
cancellation_pending state is retained in the pre-reconciliation snapshots; no
uncertain generation was replayed. Final-job-reconciliation.json records the
explicit supervisor action. Human dock checks remain untested.

## Final validation and remaining decision

Final regression/package results are recorded in R/final-validation.json and
R/final-package-identity.json. Source and installed counts overlap and must not be
added. Production expiry is unchanged. Actual final wheel imports and packaged
assets are checked, rather than inferred from line endings. The final collector
was exercised against the exact final sandbox image, with zero new inference.

The current qwen3:4b-instruct configuration is **not qualified for implementation**.
The next model/configuration attempt requires an explicit new bounded decision;
this pass does not reset its exhausted attempt count. General implementation
routing and both comparison pilots remain disabled. Strata assets/configuration,
production defaults and drivers remain unchanged. Rollback is the existing feature
switch and retained data backup; preserve job history and failed evidence. No
Git commit, push, merge, production integration or publication occurred.


## Qualification summary

All evidence paths below are relative to R. Final validation counts are in the
linked machine-readable records; installed checks overlap source coverage.

| Component | Result | Evidence | Remaining blocker |
|---|---|---|---|
| Installation | Verified reused approved SDK 1.53.0; zero new downloads | approval-reuse.json; installed-sdk-identity.json; final-sdk-identity.json | No dependency/base change authorized |
| Exact model | Live Q4_K_M tag/digest and physical RTX 3060 binding | sdk-gpu-placement.json; live-metrics.json; preservation-final.json | One configuration only |
| SDK tools | Real read/edit/test calls; generated code failed | probe2-result.json; probe-store/artifacts | Model errors and conservative request admission |
| Sandbox transport | Live bounded execution, cancellation, ENOSPC and failed collection checked | live-controls.json; final-live-collection-confirmed.json | Final collector image not rerun with inference after attempt exhaustion |
| Useful repository task | Frozen; baseline fails; not dispatched | task-contract.json; repository-baseline-confirmed.json | Required fixture did not qualify |
| Independent acceptance | No accepted candidate; protected baseline independently failed | final-job-reconciliation.json | Failed model run lost final tmpfs candidate before collector fix |
| Regression/package | Final source, installed package, upgrade and quality gates recorded | final-validation.json; final-package-identity.json | Human dock checks remain untested |
| Resources | Enforced limits and observed GPU/time/token counters recorded | preparation-final.json; final-storage-enforcement-collection.json; live-metrics.json | SDK inference peak RAM unavailable |
| Cleanup | Owned jobs stopped/escalated; reservation released; evidence retained | final-job-reconciliation.json; preservation-final.json | No acceptance/integration; no model cleanup performed |
