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
