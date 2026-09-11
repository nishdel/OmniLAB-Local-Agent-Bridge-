# Starter and optional stronger profiles

Model registration remains generic: exact Ollama tags, supported roles, dense/MoE
metadata, capabilities, thinking mode, strength and resource limits are configurable.
No model is downloaded or deleted by the server. Model licenses are separate from
this project's MIT license; LocalAgentBridge does not redistribute weights.

| Profile | Files to copy to root `config.toml` | Models | Approximate weight storage |
|---|---|---|---:|
| Starter | `config.example.toml` | Qwen3 4B | 2.33 GiB |
| Balanced | `profiles/balanced.toml` | Qwen3 4B + Qwen3 14B Q4_K_M | 10.97 GiB |
| Quality | `profiles/quality.toml` | Qwen3 4B + Qwen3 14B + GPT-OSS 20B MXFP4 | 23.81 GiB |

Copy an optional profile to the checkout root before use; relative paths are
resolved from the config file. Keep your existing private config as a backup.
After switching profiles, use the dashboard to set the intended cap: a previously
persisted cap takes precedence over `adaptive.default_cap`.

Starter needs only `ollama pull qwen3:4b`. Balanced additionally needs
`ollama pull qwen3:14b-q4_K_M`; Quality additionally needs `ollama pull gpt-oss:20b`.
Run `doctor`, `verify-models`, then `smoke --all`. Quality also supports
`smoke --all --consensus`. Balanced can use general/coding consensus. Starter has
only one distinct model and reports that consensus needs multiple models.

## Quality selection rules

The Quality example reflects one small reviewed reference workload, not a universal
ranking. GPT-OSS low thinking achieved 7 accepted / 4 corrected / 0 rejected over
11 cases, averaging 54.2 seconds. Qwen3 14B achieved 6 / 5 / 0, averaging 77.1 seconds.
It remains useful for different discovery/review strengths and lower memory use:
sampled host allocation about 6.19 GiB versus GPT-OSS's 9.26 GiB. See the
[paired results and limitations](benchmarks/v0.4-results.md). Neither fully fits
6 GiB VRAM. The Quality example's 16 GiB combined budget is tight on a 16 GiB PC;
other applications and current free memory can still cause load failures/timeouts.

| Compute | Eligible production models | Selection |
|---|---|---|
| Light | Qwen3 4B | Simple discovery/extraction/summary within input limit; substantive work hands back to Codex |
| Medium | Qwen3 4B, Qwen3 14B | Simple discovery/summary at most 1,200 input characters uses 4B; substantive work uses 14B |
| Large (Quality default) | 4B, 14B, GPT-OSS | Same cheap-work threshold; substantive work prefers GPT-OSS; 14B is the lower-memory/capability fallback |
| Maximum | 4B, 14B, GPT-OSS | Cheap-work threshold falls to 256 characters; GPT-OSS is preferred for everything else that passes local delegation/gates |

Input characters include content plus objective. Only `find_relevant_context` and
`summarize_context` qualify for the simple cheap path. Analysis, diagnosis, review,
reasoning and nontrivial triage are substantive even with short input. A moderate
complexity or stronger hint bypasses the cheap path; complex work hands off directly.
Lexical discovery (`use_model=false`) and small deterministic triage use no model.

Configure `adaptive.preferred_model` and `lightweight_model` together. They must
name distinct enabled registry entries with greater preferred strength. The two
character thresholds are configurable; they are transparent workload heuristics,
not benchmark-proven quality boundaries. No keyword-based risk detection is implied.
Without these fields, legacy smallest-first selection remains unchanged.

Role defaults in Quality are general=4B, coding=GPT-OSS, reasoning=14B, allowing exact
individual verification and GPT-OSS/14B fixed consensus. Adaptive substantive
reasoning still prefers GPT-OSS. The dashboard derives actual eligible names from
installed weights, supported roles, enabled flags and the same cap/resource/quality
gates used by the router. An explicit role can narrow available candidates.

## Thinking and bounded JSON

The GPT-OSS registry entry specifies `thinking = "low"`. The bridge sends
`think: "low"` with schema-constrained `/api/chat`, validates only final
`message.content`, and discards thinking text. Callers cannot override this through
MCP. The internal frozen benchmark override can deliberately reproduce the historical
`think=false` protocol; it is never exposed as a tool argument. That protocol failed
JSON validation on all 11 reference cases; the low-thinking run passed all 11.
This is consistent with [Ollama's documented GPT-OSS thinking levels](https://docs.ollama.com/capabilities/thinking).

No regex recovery, raw reasoning dump or silent JSON repair is used. Invalid JSON,
truncated output or insufficient confidence escalates only to a stronger eligible
model within the attempt limit. If the preferred strongest model fails, Codex
receives a handoff; the bridge does not repeatedly retry or downgrade it. A missing
model reports the exact pull command, without a substitute. Cap/resource/quality
exclusion can choose the configured lower-memory fallback before inference and logs
the reason. Current free RAM is not an admission guarantee; measured allocation
and a configured reserve are conservative estimates, not a GPU scheduler.

Codex retains final verification, architecture, security/privacy judgments,
implementation decisions, complex multi-file reasoning and resolving disagreement.
Structured JSON and unanimous consensus do not establish correctness. Preserve
review history; the dashboard includes older protocols and labels its scope.
