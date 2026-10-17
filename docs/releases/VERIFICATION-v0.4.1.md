# v0.4.1 release verification

The release uses an explicit source allowlist. Personal configuration, raw model
responses, usage databases, machine identifiers and cleanup records remain private.
The public reference benchmarks contain anonymized aggregates and synthetic cases.

## Earlier v0.4.1 validation

Before final publication, a fresh source copy and environment passed 145 tests
with one Windows symlink-privilege skip. Ruff and dependency consistency passed.
Starter and Quality MCP calls, isolated Codex registration, native tray startup,
layout/focus and SQLite startup were checked. These are setup and regression
checks on one Windows host, not a cross-platform or broad hardware certification.

The GPT-OSS profile sends `think: "low"`, validates final JSON independently of
thinking and prevents MCP callers from overriding that policy. Regression tests
cover this behavior and stronger-only bounded escalation. See
[profiles and routing](../PROFILES.md).

## Final public-state verification

- **145 passed, 1 skipped** in the release regression suite; the skip is the
  Windows symlink-privilege test. Ruff and `pip check` passed.
- Fresh constrained installation, isolated Codex MCP registration and starter
  `doctor` checks passed. Real user settings were not changed by registration tests.
- Post-cleanup MCP verification made three real, bounded calls: a lightweight
  Quality-profile summary, a substantive GPT-OSS test diagnosis under Large,
  and a Qwen3 4B starter summary. All used the expected model in one attempt,
  returned valid final JSON with Ollama counters, and were reviewed for the
  supplied synthetic exercises. Lexical discovery and the seven-tool catalog
  were also checked. This does not prove automatic delegation from a Codex turn.
- The exact Git export is rechecked against the **86-file** public allowlist
  before pushing. Pattern/privacy scans, ignore probes and relative documentation
  links passed. No personal configuration, runtime history or build output is tracked.
- The build contains 29 package/metadata/license files, with package bytes
  matching source and no private artifacts. Wheel SHA-256:
  `34b9be8bacaa9ca1d3425d13cc3690a1c50f031d272dd4170debab11c9a17159`.
  The wheel was a local build check; GitHub distributes the source release.
- GitHub Issues and private vulnerability reporting are enabled. No earlier
  private history is imported. Expensive reference benchmarks were not rerun.

## Privacy, history and licenses

The exact release export is checked against `PUBLIC-FILES.txt`, including SHA-256
source comparisons, ignored-file probes, secret/path/identifier patterns and
private audit terms. Four exact synthetic path-security matches are reviewed;
there is no file-wide exemption. Public images contain synthetic demonstration
content. No private Git history is imported into the initial public repository.

LocalAgentBridge retains MIT. Model licenses and installed dependency licenses
remain separate; no weights or dependency binaries are distributed. The existing
44-version constraint file is unchanged. See [dependency review](../DEPENDENCIES.md).

## Practical limits

Valid JSON, high confidence and model agreement do not prove correctness. Models
can invent filenames, miss explicit requirements and return incomplete snippets.
Codex retains implementation, architecture, security and final-verification
responsibility. Review delegated results before using them.

Byte compression compares input content and returned envelopes. It excludes tool
schema/orchestration overhead and does not measure cloud-token savings or avoided
cloud calls. No controlled with/without-delegation experiment was run. Historical
[reference results](../benchmarks/v0.4-results.md) are a small workload, not a
universal quality ranking. Final release checks do not rerun those benchmarks.

Optional large models can be slow or exhaust memory; configured budgets are not
admission guarantees. A missing or ineligible stronger model can return work to
Codex. The public starter requires Qwen3 4B only.
