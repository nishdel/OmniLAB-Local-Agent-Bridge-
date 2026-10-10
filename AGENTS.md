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

## Supervised local-first workflow

The project model is qwen3.8:27b served by Ollama (output capped at 1536
tokens, 65536 context, 28 GPU layers, draft 4, thinking off). Advisory work
flows LAB -> Ollama; implementation flows LAB -> OpenHands -> Ollama. Codex
owns planning, security, independent patch/test review, acceptance and
integration; LAB owns durable jobs, evidence, budgets and review state.
OpenHands tools only see task-declared paths, protected acceptance and exact
approved test commands; the container is networkless and host inference uses
a trusted mailbox. This is project/personal configuration, not a requirement
for public users; exact per-job choices and the public model selector remain.

Never silently replace a missing or different model, ignore runtime settings,
grow output allowances or relax safety limits. Run one inference at a time;
split work, bound retries and explain escalation or direct Codex work. Local
output never authorizes its own permissions or acceptance. Record independent
acceptance outcomes: accepted without Codex repair, accepted after local
retry, accepted after Codex repair, or failed/blocked. Report usage from
actual provider or cumulative cloud evidence; local tokens are not cloud
tokens saved, missing counters are unknown, and any savings claim needs an
equivalent accepted baseline including overhead.

For measured task costs, bind the entire dedicated cloud supervisor session and
LAB run to one accounting run/task before importing usage. Include planning,
dispatch, retries, repair and review; mark shared controller overhead separately.
Never allocate a fraction of a shared turn or infer savings from local tokens.
Keep complete isolated baseline/hybrid inputs and acceptance equivalent. Stop a
comparison if either arm lacks attributable counters; record the precise gap.
