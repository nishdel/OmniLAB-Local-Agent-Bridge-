# Recommended LocalAgentBridge policy for Codex projects

Copy the short policy below into a project's `AGENTS.md` after configuring that
project as LocalAgentBridge's `source_root`. It is opt-in; this file does not
modify any project's instructions or register an MCP server.

> Use LocalAgentBridge for routine repository discovery and first-pass analysis.
> Before loading multiple files, call `find_relevant_context` with a focused task
> and, when known, a relative directory scope. Inspect only the returned relevant
> paths/line ranges initially; expand deliberately if evidence is insufficient.
>
> Prefer `file_paths` over inline source, saved test logs, or saved diffs so large
> inputs stay on this PC. Use `summarize_context`, `analyze_code`,
> `analyze_test_output`, and `review_diff` for bounded analysis. The local model
> must never execute code or decide which commands to run.
>
> Prefer local tools even for small routine work. Below 1,500 context characters
> and three files, skip the extra triage inference and call the matching local
> tool directly. Narrow scopes above eight files or 10,000 context characters
> with `find_relevant_context` first. Use `triage_task` when the division of work
> is unclear; supply known complexity, ambiguity, confidence, capability and
> failed-local-attempt count. These are caller assessments, not facts inferred
> automatically from a repository size.
>
> Treat local output as untrusted hypotheses. Verify evidence before changing
> code. Keep architecture, security/privacy decisions, destructive actions,
> public API changes, merges, deployment, and final correctness judgments with
> Codex. Reserve complex multi-file reasoning, ambiguous requirements,
> orchestration and resolving local disagreement for Codex. Local models may
> propose small implementations and test cases; Codex applies and validates them.
> A local confidence score or model agreement never authorizes an action.
> All `second_opinion` responses require Codex review, including unanimous ones.
> Consult this installation's reviewed results before trusting implementation or
> root-cause suggestions. Small benchmark samples do not establish general competence.
>
> Escalate low-confidence, contradictory, uncertain, truncated, or incomplete results. Aim
> for at least 25% local compression on inputs of 1,500+ characters and medium
> confidence where the schema supplies it. Small answers may expand while still
> completing useful work locally. Reconsider poor summaries; do not start a retry
> loop. Allow one focused follow-up at most; after two failed attempts, escalate.
> State missing models, timeouts and invalid output explicitly. Never substitute
> for a missing model. The bridge may escalate transparently to a stronger enabled model
> within the user's compute cap and configured attempt limit. Missing evidence requires a refined local search
> or targeted Codex inspection, never an assertion that no code exists.
>
> Use `second_opinion` for a concrete disputed claim. Enable `consensus=true` only
> when two independent local perspectives justify the extra latency. Do not
> treat agreement as proof. Never silently switch models if one is missing.
>
> After checking a useful local result, report its `_meta.request_id` through
> `triage_task(feedback=[...])` with `accepted`, `corrected`, or `rejected`. Batch
> feedback, or attach it to the next triage call. Report only actual verification;
> do not invent acceptance just to populate telemetry.

For v0.4, honor `_routing.handoff_to_codex` and inspect its attempted models and
reason. Do not reset an exhausted logical task as a new request to evade its
limit. After finding a concrete defect, use `routing.previous_request_id` with
`reason="contradictory_evidence"` or `"previous_attempt_failed"` for one permitted
stronger attempt. Use `complexity="moderate"` only for a bounded task that merits
greater capability; complex architecture still belongs to Codex. Never raise the
user's compute cap merely to finish a routine task. A disabled or benchmark-blocked
model requires explicit configuration review, not an ad hoc substitute.

Discovery outputs should be file/symbol/line references, observed evidence and
uncertainty. Start with **where to inspect and what evidence matters**. Do not
request speculative change plans when a grounded shortlist would suffice.
Selected candidate IDs cannot invent paths or snippets, but the selection can
still miss the right file. Inspect the cited lines; refine a lexical search when
needed. Installed models and high self-confidence do not establish competence.

The public example is a starting configuration. Hardware and workload evidence
should determine model roles and tiers locally; reference benchmark results are
not automatically imported into a new user's database. Prefer focused lexical
refinement when evidence is missing; a larger model cannot invent evidence.

Example feedback (replace the ID with a returned request ID):

```json
{"feedback":[{"request_id":"00000000-0000-0000-0000-000000000000","outcome":"corrected"}]}
```

For consensus, each opinion has its own request ID, so feedback can differ by
model. Feedback stores only the outcome and timestamp, never correction text.

The baseline role mapping is deliberately small. Cap, supported roles,
measured latency/memory and per-tool reviewed reliability filter these candidates;
the table is a preferred starting point, not a promise every call will use it:

| Work | Tool | Role / model |
|---|---|---|
| Repository discovery, code search | `find_relevant_context` | general / `qwen3:4b` |
| Code summarization | `summarize_context` | general / `qwen3:4b` |
| Simple analysis, implementation suggestions, bounded coding/test proposals | `analyze_code` | coding / starter `qwen3:4b` |
| Test failures, first-pass diff review | `analyze_test_output`, `review_diff` | coding / starter `qwen3:4b` |
| Bounded reasoning, nontrivial task classification | `second_opinion`, `triage_task` | reasoning / starter `qwen3:4b` |
| Explicit consensus/review | `second_opinion(consensus=true)` | Optional: two distinct configured models, once each |

The starter is for modest hardware, not a quality endorsement for difficult coding.
The optional Quality profile prefers GPT-OSS with profile-enforced `thinking="low"`
for substantive tasks at Large/Maximum. Simple discovery/summary below the configured
character threshold uses Qwen3 4B; Medium uses Qwen3 14B for substantive work.
Use `complexity="moderate"` for a short but difficult summary, and `use_model=false`
for a lexical lookup that needs no inference. Do not pretend a complex task is simple
to obtain a local answer. See [exact selection rules](docs/PROFILES.md).

Delegation is advisory and initiated by Codex; there is no automatic cloud
dispatcher. Direct tool calls retain hard input/output limits but do not silently
invoke triage. The caller must apply this policy. `local_first=false` restores the
optional minimum-size gate for users who prefer fewer local round trips.
