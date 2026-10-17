# Migrating from v0.3 to v0.4

Back up the local config and data directory before upgrading. Existing schemas,
seven tool names, output limits, role defaults and single-model configs remain
supported. SQLite migrations are additive, including query indexes. Old benchmark
files are preserved locally rather than rewritten.

The CLI now discovers config.toml in the current directory. Use an explicit
--config path or LAB_CONFIG to remove ambiguity, including in automated tests.
The dashboard command aliases widget; doctor checks setup and codex-config prints
registration advice without editing user settings.

Optional registry fields: display_name, min_tier, experimental, disabled_reason,
capabilities, reliability and thinking. An explicit min_tier replaces the legacy
active-parameter cutoff for that model; memory and measured latency gates still
apply. Experimental models require Maximum. Registered capability-only models may
have no analysis roles and are never selected for MCP inference.

Per-tool reliability may be supplied as reviewed_cases, accepted_rate and
rejected_rate under a tool-name key. Local reviewed benchmark data takes precedence.
These are human-reviewed configuration inputs, not model confidence values. Public
examples do not import one machine's benchmark grades into a new user's database.

Thinking defaults to false. Models that require reasoning levels can explicitly
configure low/medium/high after protocol verification. Traces are not shown or
stored; their characters contribute only to approximate live output-token counts.
Final provider token counters remain authoritative. The preserved benchmark protocol
still overrides profile settings; a --think compatibility run is labelled separately.

The registry dashboard now uses native tabs and wrapping model cards. Installed but
unregistered models are visible, with routing disabled until configured. Compute
permission, current eligible models and per-tool exclusions are separate facts.
Large/Maximum are ceilings, not requests to run a larger model every time.

New routing metadata records the selected role, cap, tool and concise selection
facts. Historical records without those fields remain readable and say unavailable.
Local compression uses bytes and separates final logical envelopes from older/fixed
individual outputs. It does not establish cloud-token savings or avoided cloud calls.

Personal configs, old reports and raw benchmark histories are ignored for release.
Use the explicit public allowlist and release audit when preparing a source copy;
do not publish the working directory or force-add ignored files. Reference fixtures
contain only historical bridge source and synthetic exercises.
