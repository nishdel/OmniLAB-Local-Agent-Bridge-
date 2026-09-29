# Contributing

Keep the bridge small: bounded analysis tools, explicit model choices, local
metadata, and no autonomous actions. A new dependency needs a concrete benefit.
Discuss substantial routing or telemetry changes in an issue before implementing.

Use Python 3.11+ and install `.[tray,dev]` in a virtual environment.
From the repository root:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check localagentbridge scripts tests
```

Tests mock Ollama unless explicitly named manual benchmark/smoke commands. Native
Tk/tray tests run on Windows; use a Python installation with Tcl/Tk. A symlink test
may skip when Windows Developer Mode is unavailable. Hardware sampling is opt-in.

Use descriptive names, small functions, explicit limits and no prompt logging.
The initial lint policy checks syntax and undefined names, without requiring a
wholesale reformat of historical code. Add regression tests for meaningful changes
to routing, file boundaries, response budgets, accounting or user-visible state.

Never commit local configs, databases, rollouts, logs or raw benchmark requests
from private repositories. Public paired fixtures contain this project's own
historical source and synthetic exercises. Keep those fixtures byte-identical.
Quality grades must come from independent review, never self-reported confidence.

Before preparing a release, run the release audit and clean-install checks in
`PUBLIC-RELEASE-CHECKLIST.md`. Do not attach telemetry databases to issues.

## Companion candidate workflow

Create a branch/worktree and preserve existing changes. Freeze the coordinating
source and environment before local dogfooding; record module paths and hashes.
Run tests against the development worktree using a different data directory.
Local agents propose bounded patches/tests/docs; the supervising Codex reviews,
integrates, validates and records outcomes in docs/LOCAL-CONTRIBUTIONS.md.

```powershell
.\.venv\Scripts\python.exe scripts/check_docs.py
.\.venv\Scripts\python.exe scripts/prepare_release.py --check-ignore
.\.venv\Scripts\python.exe -m pip wheel --no-deps --no-build-isolation . -w dist
.\.venv\Scripts\python.exe -c "from setuptools.build_meta import build_sdist; build_sdist('dist')"
```

Inspect distributable contents and install the wheel in a fresh environment;
exercise a copied old database during upgrade. Do not publish. Use the release
readiness report to distinguish deterministic tests, simulated elapsed time,
live calls, native UI checks and unresolved limitations. Research fixture tests
are synthetic and require no installed model or historical private evidence.
