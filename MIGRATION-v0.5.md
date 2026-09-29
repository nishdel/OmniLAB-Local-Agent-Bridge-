# Upgrade to the unreleased companion candidate

Keep the public v0.4.1 installation until this candidate passes your gates.
Install the candidate wheel in a separate virtual environment; do not replace
an active coordinating runtime. Stop new work, resolve ownership/callbacks, then
switch at an explicit boundary. An editable environment must never import the
development tree while coordinating its edits.

Existing configurations, MCP commands, legacy usage views and workflow checkpoint
interfaces remain supported. `no_inference_deadline` and `thinking` are additive.
The existing per-workflow total time/cost limits still apply; disabling a direct
inference deadline does not disable workflow budgets.

The companion now preserves the implemented pre-companion v0.5 layer, as audited
in the [preservation matrix](docs/FEATURE-PRESERVATION.md). Configured roles use
existing routing by default; `--model`/`--execution exact` opt into a single model.
New workflow-submit/next/checkpoint/status actions reuse the existing engine and
ledger. Original workflows continue through their original interface; they are
not silently moved into the new companion database. See [integration](docs/COMPANION-WORKFLOWS.md).

Companion jobs use a new `companion/companion.sqlite3`; old `usage.sqlite3` is
left intact. Back up your data directory with all processes closed before an
upgrade. The candidate has schema version 1 and rejects newer unknown versions.
Do not downgrade an active companion database. Returning to v0.4.1 leaves that
new database unused; it does not delete it.

The `benchmark` install extra is removed because psutil is now a core dependency.
Use `.[tray,dev]` for contributors. The one-time `freeze_v02.py` source capture
is obsolete; historical fixtures/evidence remain preserved. Existing benchmark
tools remain research utilities and are not loaded by the product runtime.

Uninstall only the Python distribution:

```powershell
.\.venv\Scripts\python.exe -m pip uninstall localagentbridge
```

This leaves models, private databases, credentials, configuration and evidence in
place. Quit your dock/controller and let any active worker finish or explicitly
cancel it before removing its environment. No automatic service startup or
system-wide installation is created by this package.
