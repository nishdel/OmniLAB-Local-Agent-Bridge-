# Contributing

Keep the bridge small: bounded analysis tools, explicit model choices, local
metadata, and no autonomous actions. A new dependency needs a concrete benefit.
Discuss substantial routing or telemetry changes in an issue before implementing.

Use Python 3.11+ and install `.[tray,dev,benchmark]` in a virtual environment.
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
