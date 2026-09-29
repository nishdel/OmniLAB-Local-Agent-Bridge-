# Changelog

## v0.5 preservation follow-up (unreleased)

- Audit against the implemented pre-companion v0.5 source; retain skills, advisory
  roles, profiles, explicit/adaptive workflows, budgets, handoffs and checkpoints.
- Route configured companion jobs through the existing Service. Add durable
  workflow submit/next/checkpoint/status actions through the existing engine,
  with exact stored handoffs and unchanged policy/budget enforcement.
- Retain exact Qwen3 14B fallback and independent consensus; preserve thinking
  profiles and reject changed model digests before generation.
- Show workflow state/budgets in dock details; support local supervising review
  without an authenticated callback and reject unresolved workflow finalization.
- Bound retries for transient Windows research-worker state-file replacement
  errors, preserving evidence and persistent-failure behavior.

## 0.5.0.dev0 — unreleased companion candidate

- Preserve existing local v0.5 direct/adaptive advisory workflows.
- Discover installed Ollama models, show capabilities/metadata, persist defaults
  and bind exact model/digest/options to each durable job.
- Add independent serial workers, a transactional completion outbox, dedicated
  Codex session callbacks, explicit review decisions and idempotent finalization.
- Add quota/auth/network/uncertain-delivery states, cancellation and queue pause.
- Add the compact Tk companion dock and explicit no-inference-deadline option.
- Reuse protected process/lock primitives; make lifecycle fixtures portable.
- Remove unreachable legacy registry UI paths and the redundant benchmark extra.
- Add verified command/interface docs, migration guidance and release gates.

No release has been published. See [readiness](docs/RELEASE-READINESS.md) for live,
simulated and blocked checks. Published v0.4.1 remains unchanged.
