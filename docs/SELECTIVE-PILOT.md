# Matched pilot protocol (prepared, not run)

## Readiness comparison

The new [bounded plan](../examples/comparison-plan.json) and
[runner](../scripts/benchmark_readiness.py) extend the existing fixture,
qualification, measurement and usage infrastructure. The historical eight-case
pilot below is preserved. **No live comparison has run.** The runner prepares
snapshots, contracts and empty paused stores, verifies their hashes, exercises the
real LAB path using in-process fakes, and reports supplied evidence. It has no
live-dispatch mode. After approval, the supervisor uses the existing trusted
contract CLI for each frozen case; it never turns the plan into an automatic
production routing rule.

### Configurations and frozen work

| Arm | Exact installed identity and retained settings | Current eligibility |
|---|---|---|
| A: Codex only | Proposed fixed `gpt-6-astra`, xhigh, standard speed; record actual model/version/settings and cache usage for every dedicated session | All six fixtures after approval and availability/accounting check |
| B: Codex + LAB + Ollama Qwen27 | `qwen3.8:27b`, digest `aaee06c3…`; Q4_K_M, 65,536 context, 1,536 output, 28 GPU layers, draft 4, thinking off | Existing scoped advisory/implementation evidence; new fixture/category approvals and current admission still required |
| C: Codex + LAB + Ollama Qwen35-A3B | `qwen3.6:35b`, digest `a7eb95c5…`; Q4_K_M, 65,536 context, 1,536 output, 14 GPU layers, stored draft 2 with no request override, thinking off | Separate accepted fixture/UTC evidence; exact profile/tool proof and scoped fixture approvals required |
| D: Codex + LAB + pinned Strata Coder | `qwen3.8-flash-next-coder-iq1_m`, binding `9f69a2de…`; patched 0.1.43 CUDA 12, IQ1_M-labelled mixed GGUF, 16,384 context, 1,536 output, int8 KV, spec 4, mapped experts | **Blocked for this package.** No startup; memory/exclusivity prerequisites unresolved. OpenHands C and live failure/cancellation must qualify before implementation trials. |

Full identities, wrapper-manifest hashes, templates, image and settings are in the
plan. Read-only installed manifest/API inventory verification on 2026-10-13 matched
the historical Ollama serving identities. Ollama's wrapper-manifest file hashes
are different from its reported underlying serving digests; both are recorded.
Strata identities come from existing verified manifests; no weights were loaded
or rehashed for this preparation. This is a **configuration comparison**, not an
engine-only comparison: models, quantizations, templates, allocations, reasoning,
offload, cache behavior and executor envelopes differ.

| Fresh synthetic fixture | Lane for B/C | Frozen independent acceptance |
|---|---|---|
| Source explanation | Advisory | Expiry/missing/zero behavior with source references; independent prose review |
| Defect review | Advisory | Reproduce both defects, correct lines and causal explanation; no invented findings |
| Regression tests | Implementation | Correct baseline passes; four distinct behavior mutants fail; nonempty, non-skipped unittest suite |
| Bounded fix | Implementation | Half-open time buckets, duplicate edges/invalid input, boundaries and input preservation |
| Small multi-file refactor | Implementation | Shared label normalization across three files, preserved signatures/behavior and dynamic shared use |
| Structured logs | Advisory | Replay deduplication, failed/retried costs, blocked versus rejected outcomes, unknown duration |

[Fixture source](../scripts/comparison_fixtures.py) contains requirements, starting
files and protected checks. These are newly authored synthetic cases, not the
old benchmark answers. The evaluator necessarily knows the checks; they are not
advertised as a blind held-out study. Test-only reference controls prove the
checks can reject baselines and accept correct behavior. Never supply those
controls, another arm's output, repairs, receipts or conversation to generation.
Separate sessions start from the same file hashes; Git commit hashes may differ
because independent snapshot metadata differs. Each manifest records its exact base.

The common file envelope is at most 10,000 UTF-8 bytes, with no trimming. It is a
size bound, not a token count. Retain each profile's qualified context allocation.
The full SDK/system/tools/history envelope still needs per-request context
admission against the smallest applicable 16,384 budget. Strata's saved 7,408-token
initial-envelope evidence is historical, not a count of these new fixtures.
Rejection means split/rescope a future comparison, not silently truncate or enlarge
context. Keep model response limits, reasoning and offload unchanged. The proposed
600-second attempt watchdog narrows the qualified ceiling; it does not extend it.

### Reproduce the offline preparation

Use an existing candidate Python environment with the project's dependencies.
Nothing here installs packages. Use new directories so earlier evidence survives:

```powershell
python scripts/benchmark_readiness.py prepare --output data/comparison-prepared
python scripts/benchmark_readiness.py check --manifest data/comparison-prepared/manifest.json
python scripts/benchmark_readiness.py mock --manifest data/comparison-prepared/manifest.json --output data/comparison-mock
```

Preparation creates 48 slots: six fixtures × two trials × four arms. Twelve Strata
slots are blocked, and the other 36 are not run. Every case identifies repository,
Git base, protected file hashes, request/contract hash, settings and separate store.
Contracts have `supervisor_approved=false`; stores are paused and empty. The
candidate is bound by Git HEAD plus the complete public-source hash manifest,
so an uncommitted preparation is not mistaken for that HEAD's source. The final
owner package additionally binds the reviewed wheel and imported package tree.

The read-only `next` command proposes one frozen slot and checks cumulative
budgets/acceptance/accounting before continuation; it starts nothing:

```powershell
python scripts/benchmark_readiness.py next --manifest data/comparison-prepared/manifest.json --attempts data/comparison-attempts.json --usage data/comparison-usage.json --elapsed-seconds OBSERVED_SECONDS --evidence-bytes OBSERVED_BYTES
```

For the initial proposal supply an empty JSON array of attempts and an object
with `records: []`. Later use all retained live attempts and the complete existing
usage report (its CLI `investment` envelope is supported). The owner manifest
binds private disabled per-case configurations and the installed candidate; after
approval the supervisor records an enabled copy and each exact scoped approval,
runs `companion contract-route --request APPROVED_CONTRACT`, and uses
`contract-submit --run RUN --request APPROVED_CONTRACT`. These commands perform
real admission and must not be run as an offline mock. Use existing `companion create`,
local review, correction and integration controls; no new dispatcher bypasses them.

Mock execution uses separate stores and `httpx.MockTransport`, with application
sockets and non-Git subprocesses blocked. It calls real `prepare`, `execute`,
durable submission/review and usage attribution. The fake sandbox deliberately
returns unsuccessful proposals: synthetic protocol completion is not fixture
acceptance or a model-quality failure. On Windows, asyncio initializes its internal
wakeup socketpair before dispatch guards; no serving HTTP/inference environment
is started. Preparation stores remain empty after the mock.

### Measurements and reporting

[Attempt schema](../localagentbridge/comparison.py) `empty_attempt` records
candidate/settings/fixture identity, admission/reason, lane, outcome, first-pass
acceptance, correction/rejection/failure, independent checks, regressions, phase
times, owner interventions/review time, usage references, cache state, resources
and per-domain energy. Use the actual attempt/job IDs privately. Do not edit a
failed attempt into a success: append the next attempt and retain the old one.

Start the end-to-end clock and local telemetry **before planning/queueing/loading**;
finish after review, repair/fallback, verification/integration and owned cleanup.
Exact-counting helpers, tools, failures and retries belong inside that boundary.
Record loading/queue/request timings from existing receipts where available.
The controller's `end_to_end` ends at job completion and does not cover later
supervisor review; the comparison's longer clock must include it. Phase timers
may overlap: never sum overlapping phases as the end-to-end duration. Keep observed
owner review time separate from callback duration or a guess about effort.

Bind a dedicated complete cloud session and every LAB run/fallback session to
one accounting task identity using `contract-usage-bind`, then import and export
with the existing `contract-usage-import/report` commands below. One task identity
includes all its attempts. Report `implementation` as setup/investment,
`evaluation`, `operating`, and `unattributed` separately; do not rename historical
categories or allocate fractions of a mixed turn. The comparison reader consumes
`usage_report.investment`'s deduplicated records; it is not another counter stream.
All cloud planning, dispatch, review, repairs and fallback must be accounted for,
including separate sessions. Missing phase coverage stops a savings comparison.

```powershell
python scripts/benchmark_readiness.py report --attempts data/comparison-attempts.json --usage data/comparison-usage.json --equivalence-evidence "Reviewed equivalent fixtures, supervisor settings and complete session coverage" --output data/comparison-report.json
```

The report rejects duplicate attempts/usage receipts, missing prior attempts,
overlapping task accounting and false acceptance. It computes B−H only for
equivalent independently accepted live work with complete counters and coverage;
negative savings remain negative. Cached/reasoning subsets are not added again.
Mock, blocked, not-run, failed acceptance and unknown usage cannot establish
savings. Advisory and implementation remain separate by fixture/lane. Local tokens
and preflight counts never become avoided cloud tokens.

### Power and resource boundaries

The existing LaptopPower project was inspected read-only. Its timestamped NVML
export reported eGPU board power; CPU package power was explicitly unavailable
(`CPU MSR access unavailable: package power not validated`). Internal GPU power
was unavailable too. No monitor, CPU probe, driver or power-setting change was
started. A read-only `nvidia-smi power.draw` query is the alternative board source.
The [sampler](../localagentbridge/comparison_telemetry.py) can read the existing
status file without importing or starting that project's service. It ignores
its configured estimates/subtotals. Choose one source per physical device, never
add NVML and nvidia-smi readings of the same board.

```powershell
python scripts/benchmark_readiness.py sample --seconds 60 --output data/task-power.jsonl
python scripts/benchmark_readiness.py summarize-telemetry --samples data/task-power.jsonl --start START_UTC_SECONDS --end END_UTC_SECONDS --output data/task-energy.json
```

Sampling is explicit and read-only, bounded to 1,800 seconds and 8 MiB per file.
For an already-running LaptopPower export add `--power-status PRIVATE_STATUS_FILE`;
use `--max-gap 25` for its existing cadence. Native sampling defaults to two
seconds and a five-second maximum interpolation gap. Missing power stays null.
No TDP, power limit or utilization percentage is consumption evidence.
An offline-preparation availability probe obtained three read-only GPU board
samples over approximately four seconds. It establishes sampler availability,
not task energy, idle calibration or a local/cloud comparison result.

Energy uses trapezoidal integration: `(W0 + W1) / 2 × seconds / 3600 = Wh`.
It clips only bracketed endpoints, rejects conflicting duplicates/mixed streams,
and leaves gaps, missing sensors, restarts and clock discontinuities uncovered.
Gross observed Wh, coverage, gap reasons and any separately supplied idle-subtracted
estimate are distinct. No extrapolation; negative idle-subtracted estimates remain
negative. An exported UTC-only source has a stated clock/suspend limitation.

Resource peaks/minimum available RAM are sampled whole-host observations, not
process allocations; disk counter deltas include unrelated host activity and
become unknown on counter reset/missing data. Power samples include concurrent
local client/other loads. CPU-package, GPU-board and whole-system streams stay
separate. Whole-system wall energy is currently **unavailable**. Any later existing
wall meter must cover both laptop and eGPU supplies and identify battery charging/
discharging plus other measured loads. GPU-only Wh cannot establish total
electricity cost, and local client energy cannot estimate cloud-datacenter energy.
Per-accepted-task energy includes all unsuccessful tasks/attempts in scope;
incomplete coverage produces an unknown full total alongside known observed Wh.

### Delegation decision worksheet

| Task category | Eligible configurations | Acceptance | Cloud usage reduction | Time/owner effort | Energy | Recommended lane | Evidence strength |
|---|---|---|---|---|---|---|---|
| Source-grounded documentation | A/B/C after approval; D blocked | Historical Qwen27 scoped paragraphs accepted; new fixture not run | Unknown | Historical small sample only | Unknown | Retain supervised bounded advisory | Narrow prior acceptance; no matched savings |
| Code review | A/B/C after approval; D blocked | New fixture not run | Unknown | Unknown | Unknown | Advisory pilot only | Synthetic checks prepared |
| Regression tests | A/B/C after scoped approval; D blocked | Prior Qwen27 tests needed retry; new mutation task not run | Unknown | Unknown | Unknown | Scoped implementation pilot | Prior task-specific evidence |
| Bounded fix | A/B/C after approval; D blocked | Prior Qwen27/Qwen35 UTC cases accepted; new task not run | Unknown | Unknown | Unknown | Preserve currently qualified small-fix scope | Narrow historical acceptance |
| Multi-file refactor | A/B/C after scoped approval; D blocked | Not run | Unknown | Unknown | Unknown | Codex direct until pilot evidence | No demonstrated category expansion |
| Structured log analysis | A/B/C after approval; D blocked | Not run | Unknown | Unknown | Unknown | Advisory pilot only | Synthetic checks prepared |

Retain delegation only for demonstrated categories that preserve acceptance and
reduce complete cloud work without unacceptable elapsed time or owner review.
Two trials are a screening sample, not statistical proof. Report failures and
negative/inconclusive results. Do not expand production permissions/routing from
these recommendations. Strata qualification failures are infrastructure blockers,
not zero quality scores.

### Subscription worksheet and two-week operating trial

Private owner inputs (blank until explicitly supplied):

| Actual plan | Billed currency/amount and period | Required reasoning-model access | Research | Files | Voice | Other required features |
|---|---|---|---|---|---|---|
| | | | | | | |

Official documentation checked 2026-10-13: the published US monthly examples are
Plus $20 and Pro $100/$200/$500. Included subscription allowances, purchased
ChatGPT credits and API-key billing are separate. Task/model/speed affect usage;
token rates do not determine included plan allowance. Check current account
limits/reset windows. [Official pricing and usage](https://learn.chatgpt.com/docs/pricing),
[speed settings](https://learn.chatgpt.com/docs/agent-configuration/speed),
[separate API pricing](https://platform.openai.com/pricing).

These are published reference prices, not the owner's bill or a localized tax
quote. Subscription-only differences are $80/month (Pro $100 → Plus $20),
$100 (Pro $200 → Pro $100), or $300 (Pro $500 → Pro $200). For each scenario:
`net cash difference = actual old subscription − actual new subscription − added
credits − added API charges − incremental whole-system kWh × actual tariff`.
Use the same billed currency/tax basis and actual incremental charges; never price
included subscription tokens as API usage. Today the full net result is unknown:
owner prices, incremental charges, tariff and whole-system energy are missing.
Board-only electricity is a partial component, not a total bill. Keep owner time
in minutes unless the owner supplies a monetary value.

After the initial benchmark, propose 14 representative operating days using only
categories that earned delegation. Preserve the supervisor model/settings first;
a cheaper supervisor is a separate later comparison. Privately record busy usage
windows, weekly resets, throttling, extra credits/API charges, task mix, failed
delegation/repair, acceptance and owner time. Include non-coding reasoning,
research, file work and voice requirements. Compare peak windows as well as
averages; propose at least 20% spare capacity at representative peaks, not a token
conversion to lower-plan limits. If actual lower-plan limits/features or peak
consumption cannot be established, plan-fit stays unknown. No plan/authentication
change, credit purchase or trial subscription switch is authorized here.

### Single bounded live-comparison approval package

The generated manifest plus the reviewed candidate package identity is the single
approval object. Approve its hashes and A/B/C scope only after reviewing the
remaining prerequisites; D stays blocked. No open-ended campaign is requested.

1. **Freeze and bind:** use the published candidate SHA/wheel, final manifest,
   exact profile/qualification files and declared stores. Record available fixed
   supervisor settings. Recheck all hashes with `check`. Supervisor approval of
   each contract is explicit and recorded in a new approved copy; keep the
   unapproved manifest intact. Required profile/context/resource gates still run.
2. **Exclusive session:** owner saves/finishes competing work and pauses participating
   LAB stores, resolves active jobs/reservations and agrees that all other clients
   will avoid inference. Reuse the [existing exclusive-session procedure](SELECTIVE-IMPLEMENTATION-REPORT.md#next-session-readiness-decision--2026-10-13)
   and read-only loading-runner gate. Reservations in separate stores are not a
   machine-wide lock. No unrelated application is closed or process killed.
3. **Pilot:** trial 1, source explanation then bounded fix, A → B → C: at most six
   task sessions, two attempts/session, 600 seconds/attempt, 1,800 seconds total
   per task and **three hours total**. One inference at a time. Each attempt allows
   eight local requests, 1,536 output tokens/request, zero transport retries,
   existing repair ceilings, 15-second checks and the unchanged 2 GiB/no-swap,
   two-CPU/128-PID sandbox. Run accounting/telemetry from pre-planning to cleanup.
4. **Continuation gate within the same package:** after all six pilot records are
   reviewed for correct scope/acceptance, complete counters, telemetry coverage,
   ownership and stops, the supervisor may run the remaining frozen A/B/C slots.
   Trial 2 reverses order C → B → A. Maximum **36 task sessions / 72 attempts /
   18 hours total / 2,000,000 actual cloud total tokens / 12 GiB new evidence**,
   including pilot, failures and retries. Stop on missing accounting, any safety
   failure, one failed pilot acceptance or exhausted budget; do not add tasks.
   Unknown quota/counter coverage blocks continuation, not a free extension.
   The supervisor checks actual counters, elapsed time and evidence size during
   each phase, stops before the ceiling, and retains any in-flight/unknown cost.
   `next` is a between-slot check, not a hard real-time token or disk watchdog.
   If timely counters/budget enforcement are unavailable, do not start that slot.
5. **Startup/switch/shutdown ownership:** a later authorized supervisor starts only
   the dedicated candidate controller and, for implementation, the existing
   qualified executor. Owner-authorized existing Ollama serves the exact selected
   profile. Do not download/install anything. Before switching, finish/cancel and
   reconcile owned work; owner must authorize any required release of a resident
   model. Only exact owned test resources may be stopped; never kill shared Ollama.
   Restore recorded paused/default states afterward and preserve all evidence.
6. **Stops and excluded work:** retain 6 GiB admission, 2 GiB hard RAM floor,
   3 GiB for 15 seconds sustained floor, 11,776 MiB GPU ceiling, missing GPU
   diagnostic/identity/context/output/storage stops and uncertain-reservation
   retention. Strata retains **22.5 GiB pre-start / 11 GiB pre-C provisional
   screens**, including the additional **0.5 GiB counter/IPC allowance**; uncertain
   further growth still prevents a positive fit claim. No Strata startup, C trial,
   live failure injection, managed callback activation, merge/release or subscription
   change is included. Those require their applicable qualification/authority.

The owner still needs to approve the exact package, exclusive window and specific
startup/model-switch/owned-shutdown actions. The eleven human acceptance rows
remain the sole human ledger, with core UI/customer gates separate from experimental
Strata gates. This preparation does not waive any merge/release requirement.

The [accounting diagram](WORKFLOW.md#accounting-and-observability) shows the separate
report utility, explicit attribution and dock boundary. Historical totals below
are dated report windows, not current lifetime totals.

## Close-out attribution

Operators attribute usage by binding complete sessions, turns, or jobs to specific tasks and categories. Cloud receipts track Codex activity, while local receipts cover LAB runs. Bindings link entire units to a single run, rejecting overlaps or conflicting labels. All retries and failures count toward that run. If counters are missing, usage remains unknown. Unbound activity is reported as unattributed, and shared controller overhead stays visible without invented allocations. Savings are only confirmed when equivalent baseline and hybrid runs, including full supervision and repair, are independently accepted. Local tokens do not equal cloud tokens saved. Historical comparisons lack isolated planning costs, so they cannot establish savings.

The close-out starts at 2026-10-10 10:16:10 UTC, after the original milestone.
A binding is trusted bookkeeping in the existing usage database; it contains no
second token counter. Bind cloud sessions (or exact complete turns) and local LAB
runs (or exact jobs) to a common accounting run/task identity:

~~~text
companion contract-usage-bind --kind cloud --session SESSION --run RUN --task TASK --category operating --evidence "Complete isolated supervisor run"
companion contract-usage-bind --kind local --session LAB_RUN --run RUN --task TASK --category operating --evidence "All local attempts for this task"
~~~

For a whole turn/job use --logical-id EXACT_ID. Categories are implementation,
evaluation, operating and unattributed. Repeating an identical binding is safe;
conflicting relabels and overlapping session/turn bindings fail. A session-level
binding includes later receipts, retries, cloud repairs and fallback in that
session. Separate fallback sessions require their own binding to the same run.
The reporting view separates cloud/local counters per category and run; source,
session, turn/job, request, status, model and cutoff remain inspectable.
Cached input and reasoning remain subsets. Empty/missing coverage is unknown.
Bindings are available through trusted CLI, not model-controlled tools.

Before a measured comparison, bind complete dedicated supervisor sessions from
planning and dispatch through final review/repair; import all their metadata.
Do not infer completeness from a binding or from a successful final answer.
Validate actual counters and duplicate imports before running either arm.
Never bind one interleaved shared turn to a single operating task.

The historical generation-only baseline reported 23,173 input, zero cached
input and 1,127 output tokens (393 reasoning subset; total 24,300). It omitted
isolated planning and independent acceptance costs. Hybrid task review shared
the implementation session, so its cost cannot be recovered from cumulative
events. Task labels do not create missing phase counters. Close-out validated
the new bindings with those real receipts and synthetic missing/conflict/replay
checks; it did not repeat an incomplete comparison. Net operating savings remain
**not established**. There is no new baseline, percentage estimate or bill claim.

The shared controller turns include implementation, reporting and evaluation
work. Their actual cloud counters are retained as mixed/unattributed overhead,
with a run identity and reason; no fractions are invented. Dedicated local setup
work is implementation investment; the old isolated baseline and explicit
validation probes are evaluation overhead. Normal operating work has no measured
matched sample in this milestone. These disjoint views do not silently charge
all local tokens as savings or add the same cloud receipt twice.

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

**Original investment view (before category attribution):** all measured planning, bootstrap, local work,
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
