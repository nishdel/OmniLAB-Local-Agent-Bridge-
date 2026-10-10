# Matched pilot protocol (prepared, not run)

## Milestone accounting

The standard-model milestone is separate from the historical qualification work
and from the still-inactive eight-case pilot. Its start is the current Codex
session at 2026-10-10 07:57:54 UTC. The preserved starting manifest hashes the
uncommitted checkout before implementation; earlier fixtures, UTC acceptances
and their tokens are not charged to this milestone.

Use the existing companion usage database and job receipts:

```text
companion contract-usage-import --rollout ABSOLUTE_CURRENT_ROLLOUT
companion contract-usage-report --since UNIX_START --cutoff UNIX_CUTOFF --session SESSION_ID
```

Import reads only usage/lifecycle metadata and persists byte checkpoints.
Repeated cumulative snapshots produce no new usage. First inherited totals
without a last-response counter are not attributable; missing fields remain
unknown. Request IDs deduplicate local receipts; recovery imports a durable
receipt idempotently. Unreceipted/cancelled requests retain unknown usage.
When both OTEL and rollout cover a session/model, select the more complete
stream rather than summing them. CLI turn.completed events are per-turn, not
additional cumulative totals.

Input includes cached input; output includes reasoning. Cache-write and other
available subset counters are preserved separately. Never add subset counters
to input/output again. Context capacity, reserved output, serialized prompt byte
bounds, and provider-reported actual consumption are different measurements.
Provider counters do not establish cloud savings. Every report states its
cutoff and missing coverage; the final conversational response lies after its
last measured cutoff.

**Implementation investment:** all measured planning, bootstrap, local work,
failed attempts, retries, repair, integration, validation and review in the
milestone. The small isolated Codex baseline is explicitly evaluation overhead,
separate from productive local contributions. Shared coordinating-session work
cannot be truthfully split into exact per-task phases after the fact.

**Operating savings:** for equivalent independently accepted task workloads,
B is all Codex-only cloud usage and H is all hybrid cloud usage, including
supervision, handoffs, retries and repairs. Net cloud tokens avoided = B - H;
reduction = 100 * (B - H) / B when B > 0. Negative results remain negative.
Unknown/partial B or H, failed acceptance, incomparable inputs or missing
overhead produce **not established**, not zero savings.

The bounded test-generation comparison retains identical input-file hashes,
requirements and protected Linux acceptance for both artifacts. Neither arm
receives the other arm's solution. Codex baseline uses installed CLI
0.162.0-alpha.2, gpt-6-astra, xhigh effort, a fresh ephemeral context and reported
cache counts. The local arm uses the exact qualified Qwen profile. A successful
artifact-generation baseline alone is not complete end-to-end B/H attribution.
See the milestone section of [qualification](OPENHANDS-STRONGER-QUALIFICATION.md#standard-model-milestone)
for actual counters and coverage. No sample supports exact monthly or
implementation-wide savings; token reductions do not imply subscription-bill
reductions.

## Retained preparation and historical protocol

Run scripts/prepare_selective_pilot.py --output NEW_DIRECTORY to create eight
small synthetic cases, each in three independent arms: Codex-only, local advisory
plus Codex implementation, and local implementation plus Codex review. No inference
runs during preparation. Cases cover a boundary bug, UTF-8 accounting, stable
deduplication, boolean configuration, pagination, unavailable usage, retry limits
and execution/review state separation. These are starter cases, not a claim of
representative performance across architectural or security work.

Before each comparison, initialize one immutable Git base from the generated
case and create three isolated checkouts at that exact revision. Record the
revision and compare the source/acceptance hashes against manifest.json. No
cross-arm solution, diff, transcript or corrected prompt may be reused. Randomize
arm order and record warm/cold loading conditions. Use the same acceptance tests
and independently review each candidate. Tests and criteria remain read-only.

New-GPU execution requires installation, detection and explicit activation.
Confirm GPU model/VRAM/driver, connection, OS, RAM and free SSD space again.
Record whole-system memory residency/headroom, provider/version, artifact/digest,
quantization, context, SDK image, generation options and sandbox test dependencies.
Do not infer eGPU timing from upstream desktop results. Start one local inference
at a time. Do not launch an unattended campaign.

Record phase measurements through companion contract-metric using a JSON object
with key, phase, metrics, kind and evidence. Phases include planning, handoff,
queue, model_loading, local_inference, review, repair, verification, integration,
end_to_end and operator. kind is observed, estimated or unavailable. Missing
counters are null; zero is only an observed zero. Controller queue/end-to-end and
available provider counters are automatic. Native Ollama load timing is retained
when reported. Cloud input/cached-input/output requires attributable existing
Codex telemetry or a supervisor-supplied observation. Never invent attribution
from a subscription limit or convert tokens into euro savings.

For each arm retain:

- Input, cached-input and output tokens where attributable, and the planning,
  handoff, review and repair work separately.
- Local inference, loading, queue time, total elapsed, retries, corrections,
  acceptance/rejection and operator intervention.
- Baseline failures, skipped/unrun checks, missing metrics, actual diffs and
  independent requirement coverage.
- Exact candidate/base identity and acceptance authority.

Review the eight results together before enabling any automatic task category.
Retain delegation only where observed total Codex work falls without an
unacceptable correctness or operator burden. Report mixed, inconclusive and
negative results. This implementation reports no quality parity, speedup or savings.
