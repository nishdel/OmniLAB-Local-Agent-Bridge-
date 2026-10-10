# LocalAgentBridge — coding companion candidate

Local Ollama models propose bounded code, tests and documentation; Codex reviews,
integrates and validates. The bridge keeps local work and results alive between
Codex turns. A compact Windows Tk dock shows local jobs, review state and usage.

**0.5.0.dev0 is a development snapshot, not release-qualified.** The public
v0.4.1 release is unchanged. See [source and package provenance](docs/DEVELOPMENT-SNAPSHOT.md),
[release readiness](docs/RELEASE-READINESS.md) and the latest
[Windows qualification addendum](docs/WINDOWS-QUALIFICATION.md) for evidence
and open gates. [Manual test definitions](docs/MANUAL-RELEASE-TESTING.md) and the
[unpublished issue draft](docs/release-testing/0.5.0.dev0-issue-draft.md) prepare
owner testing; they do not record completed acceptance or authorize publication.

## Scoped Qwen27 workflow

The personal LocalAgentBridge worktree uses a qualified Qwen27 profile through
the durable companion. Public defaults and explicit model selection remain
available. [Setup and operations](docs/SELECTIVE-SETUP.md#qwen27-project-workflow)
describe the pinned runtime, start/stop/status, rollback and optional Strata.
[Current evidence](docs/OPENHANDS-STRONGER-QUALIFICATION.md#standard-model-milestone)
separates installed, tested and active components.
[Accounting](docs/SELECTIVE-PILOT.md#milestone-accounting) separates setup investment
from measured operating savings. Human dock/focus/DPI acceptance remains open.

## Start here

Use Windows, Python 3.11+ with Tcl/Tk, Git, an Ollama server with an installed
completion model, and authenticated Codex CLI for managed reviews. Model size and
hardware fit are your choice. The package never installs or deletes models.

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install ".[tray]" -c requirements.lock.txt
.\.venv\Scripts\python.exe -m localagentbridge --config examples/companion.toml companion inventory
```

Follow the [quickstart](docs/QUICKSTART.md) to select an exact model and worktree,
submit a task, start the controller and review its result. See the
[user guide](docs/USER-GUIDE.md), [configuration/CLI reference](docs/CONFIGURATION.md),
[troubleshooting](docs/TROUBLESHOOTING.md) and [upgrade/uninstall](MIGRATION-v0.5.md).
Install from this candidate checkout or its locally built wheel, not an assumed
published package version. Use a non-editable installation for a coordinating runtime.

## What runs

```text
Supervisor → durable submission → SQLite jobs → independent serial worker → Ollama
                                      ↑                    │
Tk dock / local CLI ← states/results ← transactional completion + review outbox
                                      │
                 controller → exact managed Codex session → report → supervisor validation
```

Each job records model/digest/options, worktree, base revision, attempt and result.
Callbacks queue per managed session; unavailable or uncertain delivery stays
visible. A finished local inference is not a successful run. The supervisor
records decisions and validates before finalization. Closing the dock hides it
without stopping the controller. Local and reported Codex usage stay separate;
missing counters are unavailable, and compression is not measured cloud savings.

## Demonstration and limits

The [contribution ledger](docs/LOCAL-CONTRIBUTIONS.md) records genuine GPT-OSS
code/test/doc proposals used for this candidate, including rejected and corrected
work. The [example task](examples/companion-task.json) is a synthetic boundary bug
for a small first run. It does not edit source. Deterministic fake-provider and
simulated clock tests are distinct from live integration evidence in the report.

This is not a general autonomous agent, a Codex replacement, a benchmark suite,
or a bypass for usage limits. Local models never execute shell commands.
Callbacks are read-only reports; automatic patch integration is not implemented.
HTTP cancellation does not guarantee a shared Ollama server stops generation.
No-deadline generation cannot run through computer shutdown. There is no bundled
EXE installer or automatic startup service. Windows is the tested desktop target;
other operating systems are not certified.

## Existing interfaces and contributors

The stdio MCP tools, direct/adaptive routing, bounded advisory workflows and usage
monitor remain supported: [workflow guide](docs/WORKFLOWS.md),
[adaptive delegation](docs/ADAPTIVE-DELEGATION.md), [profiles](docs/PROFILES.md),
[usage dashboard](docs/DASHBOARD.md), [delegation policy](CODEX_POLICY.md).

The [feature-preservation matrix](docs/FEATURE-PRESERVATION.md) audits the actual
pre-companion v0.5 implementation. Use the [durable workflow guide](docs/COMPANION-WORKFLOWS.md)
to carry those skills, roles, profiles, budgets and checkpoints through jobs and
the dock. The [quality configuration](examples/companion-quality.toml) keeps
GPT-OSS preferred, exact Qwen3 14B fallback/consensus and Qwen3 4B lightweight work.

See [architecture](docs/ARCHITECTURE.md), [decisions](docs/DECISIONS.md),
[contributing](CONTRIBUTING.md), [agent guidance](AGENTS.md),
[security/privacy](SECURITY.md), [dependencies/notices](docs/DEPENDENCIES.md),
[changelog](CHANGELOG.md), and [historical benchmark aggregates](docs/benchmarks/README.md).

## Optional selective execution

The [selective execution guide](docs/SELECTIVE-EXECUTION.md) adds opt-in supervisor
contracts, a Strata inference adapter and an isolated OpenHands implementation
executor to the existing companion. Defaults and the retained v0.5 workflows stay
unchanged. See [setup and boundaries](docs/SELECTIVE-SETUP.md),
[role/skill mapping](docs/ROLE-MIGRATION.md) and the [prepared pilot](docs/SELECTIVE-PILOT.md).
Strata/OpenHands and the new GPU are not live-qualified by mocked tests.

The [selective execution implementation report](docs/SELECTIVE-IMPLEMENTATION-REPORT.md) records verified stages, live limits and deferred qualification.
