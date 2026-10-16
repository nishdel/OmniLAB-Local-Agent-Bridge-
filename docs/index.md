# OmniLAB documentation

OmniLAB helps Codex delegate bounded work to local models while keeping planning,
review and final acceptance with Codex. Start with advisory work; add the restricted
OpenHands implementation lane only after its separate qualification gates pass.

**Development documentation — 0.5.0.dev0.** This website describes the development
branch. It does not turn that candidate into a qualified release or upgrade an
installed controller. The released v0.4.1, development source, installed package,
active configuration and dated live evidence are distinct states.

## Start here

| Your question | Canonical guide |
|---|---|
| What does OmniLAB do? | [Overview](../README.md) |
| How do I try a bounded advisory task? | [Quickstart](QUICKSTART.md) |
| What do the controls and job states mean? | [User guide](USER-GUIDE.md) |
| How do the three task lanes and two inference providers relate? | [Workflow and source-linked diagrams](WORKFLOW.md) |
| How do I open the independent applications or manage Docker safely? | [Standalone access and Docker](OPERATIONS.md) |
| What remains experimental for Strata? | [Inference qualification roadmap](INFERENCE-ROADMAP.md) |
| Why is Janas separate? | [Independent supervisory-agent research](research/JANAS.md) |

## Implementation and evidence

| Area | Read next |
|---|---|
| Python decisions, contracts and verification | [Workflow source map](WORKFLOW.md#source-map), [selective execution](SELECTIVE-EXECUTION.md) |
| Settings and installation | [Configuration reference](CONFIGURATION.md), [selective setup](SELECTIVE-SETUP.md) |
| Retained advisory and durable workflows | [Architecture](ARCHITECTURE.md), [workflows](WORKFLOWS.md), [companion workflows](COMPANION-WORKFLOWS.md) |
| Tested scope and unresolved gates | [Implementation report](SELECTIVE-IMPLEMENTATION-REPORT.md), [OpenHands qualification](OPENHANDS-STRONGER-QUALIFICATION.md), [human acceptance ledger](release-testing/selective-execution-issue-draft.md) |
| Recovery, security and operations | [Recovery](RECOVERY.md), [troubleshooting](TROUBLESHOOTING.md), [security](../SECURITY.md) |
| Measurement and release | [Comparison protocol](SELECTIVE-PILOT.md), [release readiness](RELEASE-READINESS.md), [development snapshot](DEVELOPMENT-SNAPSHOT.md) |

## Reading status correctly

**Tested** means a named test or dated live record supports that exact scope.
Synthetic tests do not establish live model quality. **Experimental** means code
exists but production admission is not established. **Planned** means a future
qualification target, with no automatic enabling, download or startup.

Historical reports stay at their existing links so their evidence remains
auditable. Use this index and the current workflow for navigation; do not treat
an older successful probe as current permission to run another model or lane.
