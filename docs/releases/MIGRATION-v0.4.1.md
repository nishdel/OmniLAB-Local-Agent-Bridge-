# v0.4.1 migration

- Existing configs preserve smallest-first routing unless both quality preference
  fields are set. Seven MCP tool names and legacy behavior remain compatible.
- Public starter now requires one Qwen3 4B model. Optional Balanced/Quality examples
  are separate; copying an example never installs weights or changes another project.
- Quality promotes the reviewed GPT-OSS low-thinking profile to Large. Qwen3 14B
  becomes the Medium substantive fallback; small context operations stay on 4B.
- Set the intended cap in the dashboard after replacing a config; stored settings
  override the default. Restart the MCP process and tray to reload profiles.
- Model registry support, user-defined roles, capabilities and dense/MoE metadata
  remain intact. Disabled historical entries and telemetry need not be removed.
- Source staging now offers `--check-ignore` and `--exact` validation. Run the latter
  only on a fresh source-only publication copy, before generating a venv/history.
- No model deletion, Git history rewrite, repository creation or publication is
  part of this migration. Review any local cleanup proposal separately.

See [profiles and exact selection rules](../PROFILES.md) and
[release verification](VERIFICATION-v0.4.1.md).
