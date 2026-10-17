# 0.5.0.dev0 development source and retained packages

The current source is **0.5.0.dev0 development work**. The supervised Qwen27 work
and standalone documentation were published on `codex/selective-local-execution`;
the repository presentation cleanup prepares that work for integration into
`main`. Check the actual branch and commit before treating that integration as
complete. See the [publication qualification addendum](OPENHANDS-STRONGER-QUALIFICATION.md#workflow-documentation-publication--2026-10-10)
and [complete workflow](WORKFLOW.md).

Consolidating development source into `main` is distinct from publishing a
release or recording a passed human/live acceptance result. Keep the eleven-row human ledger, Strata
standalone blockers and separate OpenHands/Strata qualification visible. The
released v0.4.1 tag/package and installed controller remain separate from `main`.
The earlier companion-release-candidate provenance below is historical evidence,
not the current activation scope.

The companion-release-candidate branch is **development work, not a qualified
Windows release candidate**. Its historical branch name grants no acceptance.
Source publication does not merge into main, create a release/tag, distribute a
binary, send a callback or pass a human test.

## Source provenance

The historical publication base is `f6df420181f21856cb421619e2c1310f6cf46685`
(then `main` and the existing v0.4.1 tag target). The canonical repository is
[nishdel/OmniLAB-Local-Agent-Bridge-](https://github.com/nishdel/OmniLAB-Local-Agent-Bridge-);
the former LocalAgentBridge URL redirects there.

The existing unpublished history was reviewed before source publication and
retained without rewriting:

| Commit | Included work |
|---|---|
| `cc88d4d86d5d038513d694c542a00339093495b4` | Preserved v0.5 workflow and protected worker baseline |
| `53a2c59a1a1a95d29de0ed4f528c9da02c7c7e9b` | Durable companion jobs, exact models and managed reviews |
| `8b02eba3deb02cc24393421b317644b183114a09` | UI cleanup and portable lifecycle fixtures |
| `91ee3a20bb869c36e23bb1c7813827de053637b3` | Integrated workflows, recovery repair, tests and qualification records |

The integration commit has tree `43266f6c38b3cfa4edf99a7953d5d0b2c71db33e`.
Its runtime, tests, examples and profiles equal qualified source tree
`3a7d24cbf8c8d41c14d88fa6a6df326a6fa37ebb`; only the Windows qualification
addendum was added after that qualified tree. Subsequent manual-testing,
navigation, public-manifest and provenance changes are documentation-only and
belong to a separate commit. Use Git history to identify that documentation
commit; it is not the retained package's source snapshot.

## Unchanged retained artifacts

| Artifact | SHA-256 |
|---|---|
| localagentbridge-0.5.0.dev0-py3-none-any.whl | `3fde801aa34b5769ed68185ed7dfd857825d819f3af807f49bcc798ce37bbb2c` |
| localagentbridge-0.5.0.dev0.tar.gz | `7afe70772012d09328d4cb38617a06a982fb10173cc2def9f2bab3efd7208f10` |

These artifacts predate the documentation commit. They were neither rebuilt
from this newer documentation snapshot nor uploaded with the source branch.
The public manifest now includes the later qualification/manual documentation;
that does not retroactively change either archive or its earlier export.

## Validation and outstanding acceptance

Retained results describe the qualified runtime: Windows 411 passed/1 skipped,
installed recovery 50 passed, and actual Python 3.11.9 installed-package checks
361 passed/1 deselected (the accepted recovery suite was excluded). See
[recovery](RECOVERY.md) and [qualification](WINDOWS-QUALIFICATION.md) for scope.
Recovery covers the tested process-crash model, not host power loss. Unsaved
output and ambiguous incidents still require explicit intervention. Local
completion never implies supervisor approval or Codex verification.

Source-push checks are separate: Ruff, documentation links/generated reference,
the public-source/ignore audit and four release-audit unit tests. No runtime
change or new package qualification is claimed by these checks. Pattern scans
and manual review reduce disclosure risk but cannot prove absence of every
possible secret. Private evidence, personal configuration, transcripts, runtime
databases, models, virtual environments and build artifacts remain local.

Remaining release gates are human DPI/readability/keyboard/focus/hide/reopen
and status observations, fresh Windows installation, the privilege-dependent
symlink check, owner-defined performance criteria and scored observations, and
separately authorized live callback testing. Authentication/quota fixtures do
not prove live behavior. The existing private callback approval request must be
reviewed before any authenticated invocation; source-push authorization does
not authorize it. No existing model preference or inventory changes are needed.

Use the [manual definitions](MANUAL-RELEASE-TESTING.md) and
[issue-body draft](release-testing/0.5.0.dev0-issue-draft.md). Their new rows are
No / Not tested. Execution results belong in one future issue, not this source
report. Opening that issue requires separate authorization.
