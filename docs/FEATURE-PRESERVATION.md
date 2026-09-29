# Pre-companion v0.5 feature preservation

This audit compares the candidate with the actual pre-companion v0.5 source,
preserved in the development baseline commit `cc88d4d` and the separately hashed
coordinating snapshot. The public v0.4.1 tag is an additional compatibility
baseline, not a replacement for implemented v0.5 behavior. Unreleased status
does not authorize removing a capability.

`retained` means the supported path still works; `refactored` means behavior is
preserved through an integrated path; `intentionally gated` means an existing
explicit opt-in, resource, evidence or supervisor control remains. The audit
found a companion integration gap: it discarded the full configuration and
called a single-model Bridge directly. Existing MCP/workflow paths were retained,
but companion jobs bypassed them. The adapter now repairs that gap. No duplicate
workflow engine, legacy registry UI or process implementation was restored.

## Preservation matrix

Paths below are relative to this source tree. Tests use deterministic provider
responses unless explicitly identified as live observations below. A test of
transport or routing is not a model-quality evaluation.

| Capability | Current code path | Supported interface / configuration | Regression and reachability evidence | Documentation | Classification |
|---|---|---|---|---|---|
| 15 declarative skills, including implementation proposals, documentation, performance, release and UI reviews | `catalog.py:Skill`, `workflow.py:step`, `definitions/skills/*.toml`, existing schemas/Bridge adapters | `workflow catalog`; `workflow_catalog` MCP; custom TOML stage `skills` composition under `agentic.catalog_root` | `test_v05_catalog.py`; every declared compatible role/skill pair executed through a real custom project catalog in `test_companion_workflows.py::test_every_declared_role_skill_is_executable_through_project_catalog` | [Workflow definitions](WORKFLOWS.md) | retained |
| 12 advisory roles and minimum requirements | `catalog.py:Role`, `Catalog.role`, `workflow.py:Execution`, `AdaptiveRouter.candidates` | Stage `role`; category, strength, context, capabilities, timeout, attempts, auto-escalation; no local tool/patch authority | Same exhaustive role/skill execution test; `test_role_requirements_and_compute_caps_remain_authoritative`, `test_capability_and_context_requirements_are_hard_gates` | [Workflows](WORKFLOWS.md) | retained |
| Built-in generic and LocalAgentBridge project profiles, custom profiles | `catalog.py:ProjectProfile`, `Catalog.resolve/role`; `definitions/project-profiles` | `agentic.project_profile`, task `project_profile`; enabled/disabled roles, instructions, model allowlists, stage replacement/removal, stricter limits, required reviews | `test_profile_overrides_compose_and_narrow`, `test_profile_file_controls_and_validation`, `test_explicit_workflow_and_stage_overrides_are_preserved`; custom catalog executed through durable adapter | [Workflows](WORKFLOWS.md), [adaptive controls](ADAPTIVE-DELEGATION.md) | retained |
| Explicit `review_change` / `implement_issue` workflows and decomposition | `workflow.py:WorkflowTask/WorkflowEngine`, `definitions/workflows`; `service.py:Service.workflows` | Existing CLI `workflow plan/start/step/checkpoint/status`; six additional MCP workflow tools when enabled | `test_review_workflow_composition_order_and_final_checkpoint`, `test_implementation_checkpoint_requires_actual_diff_and_new_evidence`; real MCP stdio tests in `test_v05_mcp.py` | [Workflows](WORKFLOWS.md) | retained; opt-in intentionally gated by `agentic.enabled` and adaptive registry |
| Workflows inside durable companion jobs | `companion_workflows.py:submit_workflow/follow_workflow/perform`, `companion.py:execute` | `companion workflow-submit`, `workflow-next`, `workflow-checkpoint`, `workflow-status`; same task schema, profiles and engine | `test_durable_workflow_handoffs_restart_and_explicit_checkpoints`; live independent worker exercised workflow direct path; CLI end-to-end validation | [Durable workflow guide](COMPANION-WORKFLOWS.md) | refactored; missing integration repaired |
| Shared attempt, correction, token reservation, input, output, elapsed-time and stage limits | `catalog.py:Limits.intersect`, `workflow_store.py:claim/reserve/attempted/finish`; `workflow.py:Execution` | Workflow/profile/agentic limit intersection; role limits; live compute cap between attempts | `test_shared_budgets_apply_across_stages`, `test_stronger_retry_counts_against_shared_correction_limit`, `test_correction_rewinds_without_refunding_stage_or_workflow_attempts`; durable budget handoff test | [Workflows](WORKFLOWS.md), [durable guide](COMPANION-WORKFLOWS.md) | retained; exhaustion intentionally hands off |
| Bounded evidence, source freshness, dependent handoffs | `workflow.py:_evidence/_handoffs/_check_sources`, `files.py`, `context.py`; companion stores returned packets | Task context/diff/test output/exact file ranges; `inputs_from`; original callers re-supply handoffs, durable next jobs do so from stored results | Existing stale/discovered-source/restart/privacy tests; durable restart and tampered-handoff tests; serialization preserves original digest ordering | [Workflows](WORKFLOWS.md), [security](../SECURITY.md) | refactored for durable transport; existing evidence contract retained |
| Implementation and final Codex/supervisor checkpoints | `workflow.py:checkpoint`, `workflow_store.py:checkpoint`; companion explicit checkpoint job | Accept/reject/revise/abort; actual diff for implementation; validation status or explicit unverified-check acknowledgment; current version required | `test_unrun_checks_are_not_silently_certified`, `test_checkpoint_cannot_skip_actual_implementation_evidence`, `test_workflow_finalization_requires_checkpoint_even_after_result_reviews` | [Durable guide](COMPANION-WORKFLOWS.md) | retained; deliberately supervisor-gated |
| Adaptive direct / auto / workflow selection | `delegation.py:DelegationHints/plan`, `workflow.py:_task/start`; persisted plan in WorkflowStore | Task `delegation.mode`, risk/breadth/complexity/specialization hints; omit delegation for original explicit behavior | `test_small_tasks_default_direct_without_a_classifier`, `test_positive_reasons_select_only_relevant_roles`, three durable mode regressions; real MCP gate tests | [Adaptive delegation](ADAPTIVE-DELEGATION.md) | retained |
| Adaptive project controls and mandatory reviews | `ProjectProfile.workflow_mode/decomposition_threshold/required_reviews`; `delegation.py:compose/estimate` | Explicit project controls apply even if caller omits hints; required security/resource reviews survive direct mode; optional decomposition may fall back within budget | `test_explicit_profile_policy_cannot_be_bypassed_by_omitting_task_hints`, `test_direct_still_requires_project_security_review`, `test_optional_budget_falls_back_but_mandatory_budget_does_not` | [Adaptive delegation](ADAPTIVE-DELEGATION.md) | retained; missing mandatory capability intentionally hands off |
| Existing role routing and quality preferences | `service.py:analyze`, `config.py:resolve_model`, `adaptive.py:AdaptiveRouter`, `models.py:eligibility/task_eligibility` | Seven legacy MCP tools; `[roles]`, `[routes]`, registry, preference, cap, memory/quality/attempt controls; companion submit defaults to routed when roles exist | `test_v2_routing.py`, `test_v3_adaptive.py`, `test_v041_preferences.py`; durable Qwen Medium fallback/think test | [Profiles](PROFILES.md), [durable guide](COMPANION-WORKFLOWS.md) | refactored for companion; legacy paths retained |
| Exact model selection and overrides | `selection.py:discover/select_model`, `companion.py:submit/job_config` | `companion select TAG`; `submit --model TAG` or `--execution exact`; custom completion tags; recorded digest and thinking | Existing exact-selection tests; digest-change guard; exact Qwen inventory selection verified locally | [User guide](USER-GUIDE.md) | retained; unavailable/remote/incompatible selection rejected, no substitution |
| Independent second opinions and sequential consensus | `service.py:second_opinion`; existing Bridge lock and fixed model choices | MCP `second_opinion`; routed companion submit with `tool=second_opinion`, `consensus=true`, distinct `roles` | `test_consensus_is_sequential_independent_and_bounded`; durable fixed-order/no-substitution tests; live GPT-OSS then exact Qwen3 14B calls | [Profiles](PROFILES.md), [durable guide](COMPANION-WORKFLOWS.md) | retained and reachable through durable jobs |
| Review events, finalization and dock visibility | `companion_store.py:complete/decide/finalize`; `dock.py:presentation`; callbacks remain optional | Every step gets a review event; local supervisor `decide --local`; checkpoint is separate; dock details show ID/profile/path/stage/budget; successful finalize requires resolved workflow | Companion outbox tests, local-review and finalization regressions, native Tk verification | [User guide](USER-GUIDE.md), [durable guide](COMPANION-WORKFLOWS.md) | refactored; authenticated callback remains unverified and separately approval-gated |

No requested capability remains classified as missing or broken after these
repairs. This does not imply every model performs every advisory role well.
Some role/skill pairs need an explicit custom stage; being a reusable catalog
definition does not mean every built-in workflow invokes it automatically.

## Exact Qwen3 14B preservation

The installed loopback inventory observed during this audit contained
`qwen3:14b-q4_K_M`, digest
`bdbd181c33f2ed1b31c972991882db3cf4d192569092138a7d29e973cd9debe8`,
9,276,198,565 bytes, advertised 14.8B / Q4_K_M, completion/tools/thinking.
The exact name was selected through the candidate inventory parser; no alias or
different model was substituted. Advertised capabilities are not quality scores.

The actual pre-companion configuration enables Qwen for general/coding/reasoning,
strength 4, minimum tier Medium, weight estimate 8.67 GiB, thinking false.
Reasoning and `second_opinion` bind to that exact name; consensus roles are
coding=GPT-OSS and reasoning=Qwen. GPT-OSS remains the substantive preference
(strength 5, Large, thinking low), with Qwen3 4B for bounded lightweight work.
The [quality companion example](../examples/companion-quality.toml) preserves
these enabled routes without copying private paths or changing the user's config.

The Medium-cap fallback test actually reaches the Qwen transport with its exact
name and think=false. Fixed consensus separately pins both role models; it never
lets a preference replace the independent Qwen opinion. A live bounded consensus
probe verifies transport usability only; it is not a new broad model benchmark.
No model was downloaded or deleted.

## Limits and evidence interpretation

The original seven MCP tools remain independently usable and, as before, do not
enforce project workflow policy. Use the workflow task interface when that policy
is required. Exact mode intentionally selects one model; it does not masquerade
as adaptive workflow execution. The dock is a queue/status client, not a visual
workflow editor. It links decisions to explicit CLI actions.

Completed-step restart is supported. A process dying between the workflow ledger
commit and companion result commit can leave missing handoff content. Spent
reservations and result digests remain; automatic generation replay is forbidden.
Inspect `workflow-status`, retain the interrupted evidence, and explicitly scope
new work if content cannot be recovered. This is not token-position resumption.

The [contribution ledger](LOCAL-CONTRIBUTIONS.md) identifies direct Bridge calls,
actual multi-stage workflow contributions, durable workflow execution, and fixed
sequential consensus separately. Authenticated callbacks remain unsent. Windows
tests, mocked providers, live local calls and untested release gates are reported
separately in [readiness](RELEASE-READINESS.md).
