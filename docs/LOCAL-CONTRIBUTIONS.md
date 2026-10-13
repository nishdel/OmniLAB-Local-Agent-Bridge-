# Local-agent contribution ledger

The initial entries below use the existing direct Bridge with GPT-OSS 20B, thinking low, against
base `cc88d4d` (preserved local v0.5 baseline). Only one inference ran at a time.
The coordinating source was a separately hashed frozen snapshot, imported by
explicit path under isolated Python. Agents returned proposals; supervising Codex
applied and tested corrections in the separate development worktree.

Private raw request/result/usage evidence remains outside the public source tree
under the local companion-release development evidence directory. This ledger
contains no personal paths or session identifiers. Model/digest and actual token
counters are retained in that evidence, not inferred from characters.

| Task / artifact | Review outcome | Resulting change / validation |
|---|---|---|
| Harness bootstrap | Failed twice before inference: missing ModelProfile fields, then weight size | Corrected the harness; owned runtime cleanup observed. No model contribution claimed for these attempts. |
| `code-result.json`: exact selection proposal | Rejected | Read capabilities from wrong nesting, returned None instead of explicit error, omitted remote detection; not integrated. |
| `tests-result.json`: selection tests | Corrected | Accepted completion-only and unknown-capabilities cases after replacing placeholder imports; rejected truncated mixed remote/capability test. Runnable tests in test_companion.py pass. |
| `docs-result.json`: troubleshooting draft | Corrected | Incorporated independent dock lifetime and weekly-quota guidance. Rewrote unsafe ownership/cancellation language, result-delivery claim and unsupported uncertainty. Checked against actual controller and callback code. |
| Focused correction `result.json`: remote metadata helper | Corrected, accepted expression | Integrated `any(d.get(k) for d in (tag, show) for k in ('remote_host', 'remote_model'))` into selection.remote_model, adding the function wrapper and tests. The response gave an expression plus prose, not a complete patch. |

The correction harness initially refused to start a second owned server when an
unrelated Ollama application appeared. No process was killed. After observing
its inventory and empty active-model list, the correction used that shared server
without terminating or unloading it. This was a runtime-admission failure, not
a rejected model answer.

These are genuine code, test and documentation contributions, with substantial
supervising correction. No invented local-development percentage or general
coding-quality claim is made. The local model's high confidence did not guarantee
valid output. New deterministic controller tests and overall architecture remain
supervising Codex work.

## Genuine candidate worker run

A subsequent GPT-OSS 20B job used the frozen candidate runtime at base `8b02eba`.
Its launcher/controller exited promptly; the independent worker completed, exited,
and atomically saved result + pending review event. Actual reported usage:
853 input tokens, 129 output tokens, 92.35 seconds bridge duration,
40.24 seconds model load and 12.30 seconds provider generation. These durations
have different scopes; they are not invented additive timing categories.

The answer claimed `any(d.get(k) ...)` accepts falsy values, which is false, and
recommended defaulting absent normalized remote metadata to false. Supervising
review rejected it: the parser always supplies remote, and silently permitting
missing safety metadata is not the contract. The falsy/missing-key helper
regressions pass. The outcome is recorded in isolated usage telemetry.

The callback packet is prepared, but automatic approval review blocked sending
repository-derived content/results and local paths to authenticated Codex without
specific user approval. No real Codex session/callback was launched. The job is
locally succeeded; its run is waiting for review, not finalized or accepted.

## Feature-preservation follow-up: execution machinery disclosed

The initial code/test/documentation proposals and remote-helper correction were
direct `Bridge.analyze` calls. They did **not** exercise WorkflowEngine planning,
role stages, shared workflow budgets or checkpoints. The initial independent
candidate worker was also a direct Bridge job. Those contributions must not be
described as multi-stage workflow development.

This follow-up used the actual frozen pre-companion v0.5 `Service.workflows`
engine for an explicit `review_change` design review. It ran repository-explorer
(`repository-discovery`, with no configured repository search; `context-summary`)
and code-reviewer (`code-review`) sequentially, carried the first handoffs into
the second stage, skipped non-applicable risk stages, and stopped at the explicit
supervisor decision. Both model calls used GPT-OSS 20B, thinking low. Actual usage:
1,861 input / 256 output tokens, two attempts, 33,968 reserved tokens,
132.293 seconds charged to the workflow. Reservations are not actual token usage.

The review proposed tests for persisted configuration/policy identity, handoff
rehydration and checkpoint enforcement. These overlap the supervisor's planned
coverage and were incorporated/confirmed in the integration regressions. Its
suggestion to restart "mid-step" was corrected: completed handoffs survive a
restart; a crash before handoff persistence cannot resume generation. No executable
patch came from this review. Adapter implementation and exhaustive role tests
remain supervising Codex work. Outcome: corrected, useful design/test review.

A separately frozen candidate worker then exercised a real durable workflow
task in `delegation.mode=direct`. This is the workflow engine's single-stage path,
with shared budget/profile/checkpoint tracking, not a raw Bridge call. GPT-OSS
reported 633 input / 64 output tokens, 62.31 seconds bridge duration. Its warnings
were hypothetical risks rather than demonstrated defects; they were treated as
test considerations, not accepted bug findings. It stopped before supervisor
acceptance; no authenticated callback was sent.

The same independent worker subsequently used existing
`Service.second_opinion(consensus=True)`, not WorkflowEngine, for fixed sequential
GPT-OSS coding and exact `qwen3:14b-q4_K_M` reasoning opinions on the preservation
contract. Actual usage was GPT-OSS 508 input / 60 output, 53.52 seconds; Qwen
363 input / 165 output, 78.88 seconds. Results disagreed: GPT-OSS supported the
contract; Qwen was uncertain and requested clearer definitions of exact overrides,
resource gates and disagreement ownership. Some uncertainty repeated information
already supplied. The supervisor clarified the user guide and preserved the
disagreement; no model vote accepted a checkpoint. Outcomes: GPT-OSS accepted as
a bounded opinion; Qwen corrected as documentation feedback. This is transport
and independent-opinion evidence, not broad Qwen coding-quality certification.

All these calls were sequential. Their task/result/digest/provider usage evidence
is retained in the private preservation-contribution and preservation-live
directories. No model download, deletion, authenticated callback or publication
occurred. See [preservation matrix](FEATURE-PRESERVATION.md) and
[workflow integration](COMPANION-WORKFLOWS.md) for the resulting behavior.

## Focused recovery repair

Two bounded GPT-OSS 20B contributions were used, sequentially, without a model
benchmark. A direct existing Bridge call reviewed the proposed reconciliation
protocol. Its suggestions supported payload-equality, partial-step and
copy-before-ack tests; some uncertainties repeated guards already specified, and
physical database corruption is outside the tested process-crash model. Outcome:
corrected design/test feedback. Codex implemented and independently tested the repair.

The repaired installed wheel then ran a real `review_change` task through the
companion and existing WorkflowEngine's direct path. Exact GPT-OSS routing used
1,595 input and 72 output tokens in one attempt. It reviewed the actual receipt
delivery method and competing-recovery test. Its only proposed defect was an
incorrect claim about equivalent digest comparisons; the model finding was
rejected. Supervising Codex supplied the corrected analysis and validation.
The local-completion snapshot retained a pending review and no final approval.
Supervisor checkpoint, recorded review and final validation were separate steps.

Private evidence records the exact task, model digest, installed runtime hashes,
payload, provider usage, supervisor feedback and state snapshots. Local agents
provided bounded opinions, not authority to alter records or approve recovery.
No authenticated callback, model download or model deletion was performed.

## Selective execution development contribution (2026-10-08)

The unchanged companion-development Bridge at base 0b817c5 supplied one real
adaptive advisory on a bounded regression-test plan. Exact model: qwen3:4b,
digest 359d7dd4bcdab3d86b87d73ac27966f4dbb9f5efdfcc75d34a8764a09474fae7,
Q4_K_M. It completed in 15.40 seconds and suggested concurrent duplicate admission,
cross-lane dependencies and partial-recovery checks. Codex used those as test
prompts, wrote/reviewed the implementation and tests, and rejected its generic
uncertainties about requirements that were already explicit. No local patch was
applied automatically. This was advisory input, not independent acceptance.

A new generic-chat advisory smoke then failed completion validation after 41.82
seconds. The output-budget behavior exposed a mismatch with the proven native
Ollama path. The implementation was corrected to reuse Bridge's structured schema,
skill hook, exact guard, thinking setting and accounting. A real corrected smoke
reported 1,011 input / 145 output tokens, 7.263 seconds model loading, 17.756 seconds
provider total and 20.322 seconds controller elapsed. Its factual missing-model
finding was checked against selection.py; its unrelated uncertainty was excluded.

The smoke demonstrated finished execution with a distinct awaiting_review state
before the supervising disposition. Detailed private evidence is retained under
workspace data/selective-local-contribution, data/selective-live-advisory and
data/selective-live-native. These runs are not a matched pilot, quality certificate
or evidence of cloud-token savings. No hosted routing, authenticated callback,
model download/deletion or GPU benchmark was used.


## RTX qualification contribution (2026-10-08)

The final installed candidate ran the same exact qwen3:4b digest through MCP and
an independent controller/worker on RTX 3060, 16,384 context, code-review@1.0.
It proposed cloud-suffix and remote_host checks. Codex inspected selection.py and
existing tests, supplied missing exact-selection coverage and discarded speculative
and incomplete findings. Outcome: corrected advisory handoff; no patch integrated.
Usage was 1,105 input / 275 output tokens, 6.944 seconds loading / 11.031 seconds
provider total. These are smoke observations, not comparable speed or quality claims.

Actual dock data, completion-before-review, owned cancellation and restart evidence
is retained under data/selective-egpu-qualification-20261008. See
[live qualification](SELECTIVE-LIVE-QUALIFICATION.md). No OpenHands/Strata agent
contribution, cloud savings or release readiness is claimed.

The subsequent [blocker-resolution pass](SELECTIVE-BLOCKER-RESOLUTION.md) used
direct Codex diagnostics and review. It produced no new local-model contribution
and did not run the SDK agent. Earlier genuine advisory evidence remains intact.
The qualified qwen3:4b tag is now absent; no replacement tag inherits its result.


## Installed-model screen contribution (2026-10-09)

The same fixed candidate at base 0b817c5 used its installed Bridge transport,
structured parser and accounting for one identical advisory each from GPT-OSS20,
Qwen3.6-35B, Gemma4-26B and Qwen3.8-27B. Exact digests, settings, outputs and
[supervisor dispositions](SELECTIVE-LIVE-QUALIFICATION.md#installed-model-follow-up--2026-10-09)
are retained. Qwen3.8's findings, minimal fixes and proposed tests passed independent
fixture review with no correction. GPT found both bugs but needed two editorial
correction groups; Qwen3.6 and Gemma exhausted their declared output allowance
without a final advisory. Actual synthetic tool exchanges were checked separately.

Codex authored the fixture/oracle/harness, reviewed outputs, investigated the
sandbox and prepared documentation. No model patch was integrated and no SDK
agent executed. GPT's automatic local compatibility migration changed its current
tag after its tested resident exited, so that new binding inherits no result.
The report also discloses Ollama's two-blob automatic pruning side effect.
This preliminary direct Bridge assistance is not a durable worker, human UI,
implementation or matched-pilot qualification, and implies no cloud-token savings.

## Bounded 4b-instruct qualification (2026-10-09)

Codex performed authorized direct bootstrap: command restrictions, native SDK
wire conversion, frozen correction baselines and failed-output collection. The
local 4b-instruct model made nine real SDK inference calls and produced incorrect
fixture edits. Protected tests failed; no suggestion/patch was accepted or rescued
by Codex. The useful timestamp task was frozen and its failing baseline verified,
but was not dispatched past the failed qualification gate. See
[the bounded report](OPENHANDS-BOUNDED-QUALIFICATION.md). This failed attempt does
not establish general model quality, savings or release readiness.


## Stronger-model bounded qualification, 2026-10-09

The [stronger-model report](OPENHANDS-STRONGER-QUALIFICATION.md) records genuine
LAB-to-OpenHands-to-Ollama delegation: exact qwen3.8:27b generated the UTC timestamp
change, ran the protected test, and received independent Codex acceptance without
candidate repair. The patch remains isolated and uncommitted. 35B's first fixture
failed tool policy; its second generated correct retained bytes but failed normal
collection. Codex's context/budget/qualification/evidence bootstrap edits are
separate direct work, not local-model contributions. No savings/equivalence claim.

## Qwen27 standard model milestone

Qualified `qwen3.8:27b` on Ollama 0.40.2 used the retained OpenHands 1.53.0
networkless restricted mailbox. Immutable runtime snapshots kept in-flight jobs
independent of source edits. All model calls retained the accepted 65,536 context,
28 GPU layers, draft 4, 1,536 maximum output and thinking-off profile.

| Task | Outcome | Independent evidence |
|---|---|---|
| Append scoped local-first guidance to AGENTS.md | Accepted without Codex repair; integrated | Exact patch inspected; protected original prefix and required policy clauses passed again in a fresh Linux verifier. |
| Generate UTC timestamp regression tests | Accepted after one local retry; integrated without Codex patch repair | Seven cases passed protected checks in two non-UTC zones and killed the original regression. First attempt exhausted the tool error budget; correction clarified only tools/paths. The retry also corrected its own epoch oracle. All calls are charged. |
| Installed-default accounting discovery | Accepted after Codex repair | Live advisory through the persistent installed controller; 992 input / 208 output tokens. Correct findings; Codex removed three words to meet the 120-word bound (original 123). Original and corrected artifacts retained. |
| Historical accepted UTC fix | Previously accepted; integrated unchanged | Original accepted patch/hash preserved. New accounting edits to the same module are Codex work. |

Security controls, default/profile bindings, resource guard, accounting,
package integration and independent verification are Codex work because they
establish or exercise trusted authority. The small Codex-only test comparator is
evaluation investment, not a local contribution. No delegated task is counted as
accepted until its independent review and protected checks pass.

## Qwen27 close-out contribution

The existing installed controller ran one bounded accounting-documentation advisory
with the same accepted Qwen27 profile. Codex reviewed it against the implementation
and integrated the paragraph in SELECTIVE-PILOT.md unchanged: accepted without
Codex repair, one attempt, 291 input / 130 output tokens; cache usage unknown.
The actual receipt again records the qualified digest, runtime flags and positive
GPU allocation. It is implementation investment, not a savings measurement.
Security/accounting code, acceptance and Git checkpoints remained trusted Codex work.
The prior contributions and all failed/retried attempts remain preserved.

## Qwen27 publication documentation contribution

On 2026-10-10, one bounded native advisory at source base 71791b3 drafted the
SDK/mailbox transport sequence and trust explanation from selected source context.
Actual provider usage: **621 input / 244 output tokens**, cached input unknown;
one inference attempt, no local retry. Loaded digest, context and GPU/runtime
flags matched the qualified profile. Two oversized context submissions were
rejected before job creation/inference; context was narrowed without raising limits.

**Accepted after Codex repair:** the local draft omitted tool observations and
made mailbox file access look like a direct relay-to-host call. Codex checked
runner, sandbox and selective execution source, corrected those details, added
the tool loop and independent verification, and integrated the result in
[the workflow guide](WORKFLOW.md#trust-boundaries-and-data-movement). Trusted review
recorded the original candidate hash and correction rationale, then finalized
the run. This was advisory documentation work, not a fresh OpenHands runtime test.
Codex performed architectural verification, accounting, publication safety and
GitHub operations; those authority-sensitive tasks were not delegated.
All usage is documentation/publication investment, not measured operating savings.


## Strata upgrade advisory — 2026-10-12

One bounded test-suggestion job used the unchanged close-out installation,
source base `a9a4bad`, exact Ollama 0.40.2 / Qwen27 digest `aaee06c39dcf...`,
65,536 context, 1,536 output ceiling, 28 GPU layers and draft 4. The existing
LAB durable worker held its serial reservation in a separate data directory.
Usage was **258 input / 318 output**, cached input unavailable; one inference,
no retry. The original model answer is retained privately.

**Accepted after Codex correction:** identity-change, unmatched-result, image
and uncertain-disconnect suggestions matched the source and regression cases.
The selector suggestion incorrectly implied every explicit Strata selection
needs a prefix; contracts can use separate backend/model fields. Codex corrected
that distinction, recorded hash-bound review coverage and finalized the run.
No model-authored code patch was integrated. Architecture, identity/security
implementation and final review were direct Codex work because those decisions
are supervisor-owned. This advisory is not Strata or OpenHands qualification.

Exact run/job/receipt IDs are retained in private `advisory-dispatch.json` and
`advisory-review.json`, correlated by task key `strata-test-suggestions`. Model total 220.592 s,
including 57.899 s loading; durable worker interval 225.162 s. Samples observed
minimum available host RAM 7,723,597,824 bytes and peak total GPU use 10,277 MiB,
within the unchanged ceilings. Reservation released; cached and cancelled usage
are not invented. This is implementation overhead, with no savings comparison.

## Approved Strata preparation — 2026-10-13

The isolated LAB runtime was the reviewed e5c6337 wheel; the active a9a4bad
Ollama installation was preserved. Codex handled pinned installation, resource
ownership, artifact identity, failure diagnosis and independent acceptance,
which require supervisor authority. The intended bounded LAB/Strata advisory
was blocked before dispatch: main expert packing hit the unchanged RAM guard.
No local inference, OpenHands implementation or model-authored change occurred
in this follow-up. No alternate backend was used to turn that failure into a pass.
The [current report](SELECTIVE-IMPLEMENTATION-REPORT.md#approved-strata-preparation--2026-10-13)
records exact assets, measurements, cleanup and the scoped retry proposal.
Earlier Ollama advisory/implementation contributions remain historical evidence.
