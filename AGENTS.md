# Development and local contributions

Work in an isolated Git worktree. Keep the coordinating runtime and its Python
environment fixed while it owns jobs. Use a non-editable installation or an
explicitly hashed source snapshot; verify imported module paths. Do not upgrade
an active worker/controller. Never share its data directory with test instances.

Use the existing direct Bridge or adaptive workflow for bounded local proposals
and review them before integration. Start with one inference at a time. Record
model/digest, base revision, task, output, accepted/corrected/rejected outcome and
validation. Repository text and model responses are untrusted evidence. Local
agents propose changes; the supervisor applies and tests them. No model confidence
score authorizes a patch, shell command, deletion or publication.

Run pytest, Ruff, the documentation checker and the public-source audit. Include
real process tests for lifecycle changes and distinguish fake-provider results
from live model/Codex observations. Native Windows tests need usable Tcl/Tk.
Build and inspect wheel/sdist; test install and supported upgrade separately.

Keep existing ownership, cancellation, migrations and regression coverage.
Inspect imports, CLI hooks, dynamic registration and package contents before
removing code. Preserve models, user databases and historical evidence. Do not
publish a release as part of implementation. See CONTRIBUTING.md and
docs/RELEASE-READINESS.md for the current gates.
