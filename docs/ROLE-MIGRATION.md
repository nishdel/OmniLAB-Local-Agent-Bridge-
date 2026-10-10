# Reusable roles and retained canonical skills

All twelve old role definitions and all fifteen canonical skills remain intact.
Existing workflows/profiles, required reviews and model routing bindings retain
their APIs. New contracts select local-worker or the optional read-only
local-reviewer, and explicitly list only relevant canonical skill IDs. Old role
IDs are accepted as compatible personas with their original skill restrictions.

| Existing role ID | New contract persona | Canonical skills retained |
|---|---|---|
| repository-explorer | local-worker | repository-discovery, context-summary |
| planner | local-worker | issue-analysis, implementation-planning |
| implementation-advisor | local-worker | implementation-proposal |
| test-engineer | local-worker | test-failure-analysis |
| architect | local-worker (advisory; architectural implementation stays Codex) | architecture-review, implementation-planning |
| product-reviewer | local-reviewer | issue-analysis, implementation-planning |
| code-reviewer | local-reviewer | code-review, security-review, resource-review |
| security-reviewer | local-reviewer | security-review |
| performance-reviewer | local-reviewer | performance-review, resource-review |
| maintainability-reviewer | local-reviewer | maintainability-review |
| documentation-reviewer | local-reviewer | documentation-review, release-review |
| ux-reviewer | local-reviewer | ui-ux-review |

The legacy general/coding/reasoning names bind models, not independent agents.
LAB's scheduler is deterministic. Codex is the supervisor and final reviewer.
No standing collection of specialist LLM agents is created.

Selected skill text comes directly from Catalog; evidence stores IDs, versions
and content hashes. OpenHands receives that selected text, never a forked skill
catalog or all skills concatenated. Prompts cannot grant filesystem, network,
approval or publication rights. A role name does not prove independent review;
the same model repeating a review is another opinion, not an independent authority.

Contexts and SDK conversations are per task/attempt. Persisted job/evidence state
does not become a shared conversation between unrelated tasks. A read-only
reviewer cannot receive edit permissions, even through an old role alias.
