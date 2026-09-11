# Public release checklist — v0.4.1

The public source is built from `PUBLIC-FILES.txt`; the private working directory
is never uploaded. Final validation is recorded in [VERIFICATION-v0.4.1.md](VERIFICATION-v0.4.1.md).

## Source and privacy

- [x] Explicit source allowlist; configs, credentials, databases, logs, rollouts,
  raw benchmarks, caches, weights, virtual environments and build output excluded.
- [x] Public examples use portable paths and a single-model starter.
- [x] Public benchmark aggregates are anonymized; exercises and screenshots are synthetic.
- [x] MIT attribution retained; dependency and model licenses documented separately.
- [x] No private Git history is imported; publication starts from the reviewed source.
- [x] Release audit checks secret/path/identifier patterns, private audit terms,
  representative ignore rules and unexpected files in the exact export.

## Behavior and documentation

- [x] Qwen3 4B is the only required starter model; stronger profiles are opt-in.
- [x] Light, Medium, Large and Maximum selection and resource limits documented.
- [x] Quality defaults to Large and prefers GPT-OSS for substantive work.
- [x] Codex retains implementation, architecture, security and final verification.
- [x] Model gates, bounded escalation and supervision requirements remain explicit.
- [x] Content compression is distinguished from unmeasured cloud-token savings.
- [x] Installation, configuration, MCP registration, doctor, smoke and troubleshooting documented.
- [x] Bug/feature templates and a private security-reporting link are configured.

## Publication gates

Before pushing each release, verify the exact allowlisted Git export, run the full
mocked regression suite and lint, install it in a clean environment, check doctor
and run bounded real MCP smoke calls. Do not repeat expensive benchmarks without
a reason. Confirm Issues and GitHub private vulnerability reporting are enabled.
Push the verified commit and an annotated version tag; create release notes that
state the remaining quality and measurement limitations.

Pattern scans and manual review are scoped evidence, not proof against every
possible secret. Never force-add ignored personal data. If history is imported
in a future release, audit every reachable ref/blob before publishing it.
