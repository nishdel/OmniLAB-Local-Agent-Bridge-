# Companion quickstart (unreleased candidate)

Use Windows with Python 3.11+ including Tcl/Tk, Git, Ollama and an installed
completion model. Managed reviews require an authenticated Codex CLI. The
tested CLI version and acceptance status are in [release readiness](RELEASE-READINESS.md).
There is no bundled model, automatic download, or executable installer.

Already have a qualified LAB runtime? Keep its package/environment and data store
fixed; use its established configuration and skip the generic installation below.
An advisory is the first useful path and does not need OpenHands or Strata.
Strata's experimental status does not block this onboarding path. Before submitting,
check the [model/store and status meanings](USER-GUIDE.md#choose-the-model-and-store).
Use a separate store for acceptance tests. The [existing human ledger](release-testing/selective-execution-issue-draft.md)
records owner observations; an automated mock is not human acceptance.

From the candidate checkout:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install ".[tray]" -c requirements.lock.txt
Copy-Item examples/companion.toml config.local.toml
```

Edit `config.local.toml`: set `source_root` to the target Git worktree and
`data_dir` to private local storage. Paths are relative to the configuration
file, so the copied example's `..` must be changed to `.` when targeting this
checkout. Set `thinking = "low"` if selecting GPT-OSS; other models may require
`false`. No global Codex configuration is modified.

```powershell
ollama --version
ollama list
codex --version
.\.venv\Scripts\python.exe -m localagentbridge --help
.\.venv\Scripts\python.exe -m localagentbridge --config config.local.toml companion inventory
.\.venv\Scripts\python.exe -m localagentbridge --config config.local.toml companion select "EXACT_INSTALLED_TAG"
.\.venv\Scripts\python.exe -m localagentbridge --config config.local.toml companion create
```

Replace `EXACT_INSTALLED_TAG` with an exact inventory name. Custom tags are
accepted; remote/cloud weights are rejected. Capability metadata is not a quality
grade. Save the returned `run_id` as `$runId`. The run records its worktree and
Git HEAD. Commit or otherwise establish your intended base before creating it;
a changed HEAD blocks execution/review and requires a new run.

```powershell
$runId = "RETURNED_RUN_ID"
$codexExe = (Get-Command codex).Source
.\.venv\Scripts\python.exe -m localagentbridge --config config.local.toml companion init-review --run $runId --codex-exe $codexExe
.\.venv\Scripts\python.exe -m localagentbridge --config config.local.toml companion submit --run $runId --request examples/companion-task.json
.\.venv\Scripts\python.exe -m localagentbridge --config config.local.toml companion start --codex-exe $codexExe
.\.venv\Scripts\python.exe -m localagentbridge --config config.local.toml companion dock
```

Session initialization creates a dedicated report-only Codex session. Do not
resume that managed session concurrently in another client. Submission returns
a durable job ID; it does not wait for inference. The controller starts a
separate worker and later resumes the exact recorded session. Closing the dock
hides it; its tray menu can quit the dock without stopping jobs.

Review the bounded local result, callback report and your own tests. Record the
decision using the actual event ID; never copy an acceptance without verifying it:

```powershell
.\.venv\Scripts\python.exe -m localagentbridge --config config.local.toml companion status --run $runId
.\.venv\Scripts\python.exe -m localagentbridge --config config.local.toml companion decide --event RETURNED_EVENT_ID --outcome corrected --validation "Inspected the patch and ran the boundary regression"
.\.venv\Scripts\python.exe -m localagentbridge --config config.local.toml companion finalize --run $runId --summary "Reviewed and validated the bounded contribution" --validation-passed
```

The provided task is a deliberately incorrect synthetic boundary check. Its
result is advisory; it never edits your source. See the recorded genuine local
contributions in [the ledger](LOCAL-CONTRIBUTIONS.md), and follow
[troubleshooting](TROUBLESHOOTING.md) if the review is blocked. Finalization refuses
unresolved reviews. Callback completion is not automatic acceptance.

For the preserved v0.5 skills, roles, profiles and budgets, follow the
[durable workflow guide](COMPANION-WORKFLOWS.md). It also shows local supervising
review with `decide --local`, requiring no authenticated callback. Its quality
example retains GPT-OSS preference and exact Qwen3 14B independent consensus.
