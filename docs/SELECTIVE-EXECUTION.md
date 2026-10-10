# Selective local execution (development)

For the current complete workflow, see [WORKFLOW.md](WORKFLOW.md). Historical
hardware/preparation observations below retain their original scope; current
project activation and the dated profile are in [operations](SELECTIVE-SETUP.md).

Codex owns contracts, risk classification, final review and integration. LAB owns
durable admission, deterministic routing and evidence. Ollama and Strata are
alternative inference providers. OpenHands is an optional sandboxed executor.
Existing v0.4.1 and v0.5 callers keep their defaults and interfaces.

## Baseline

The authoritative source is companion development commit `0b817c5`, not the
non-Git workspace root or a v0.4.1 export. Its working tree was clean. This work
uses a separate `codex/selective-local-execution` worktree. Existing checkouts,
coordinating environments, databases and historical evidence are retained.

Current observation 2026-10-08T17:14:47.8599842Z: Dell G5 5587;
34,139,435,008 bytes RAM; RTX 3060, 12,288 MiB, driver 560.94, PCIe Gen3 x4;
Windows 10 Home 19045. Internal GTX 1060 Max-Q reports Code 31 and is absent
from nvidia-smi. This supersedes the earlier eGPU-absent observation. Ollama
0.32.5 completed short RTX-only advisories. Docker runs but storage enforcement
failed. See [live qualification](SELECTIVE-LIVE-QUALIFICATION.md). No pilot ran.

## Decisions

Extend the companion store and independent serial worker. Execution lane is
separate from legacy exact/routed and auto/direct/workflow orchestration.
Old role IDs remain compatible personas. Contracts select a reusable local-worker
or a read-only local-reviewer and only relevant canonical skills, with versions
and content hashes. A label change is not independent review or isolation.

The optional executor runs the OpenHands SDK in a pinned, preinstalled Linux
container. It has no network, host mounts, Docker socket, credentials or host
home. LAB forwards bounded inference messages through a mailbox to one loopback
provider; the SDK owns the edit/test loop. Acceptance runs independently in a
separate sandbox against controller-collected file bytes. Missing isolation blocks
execution. No image, dependency or model is downloaded automatically.

One inference reservation spans both providers and lanes in this controller's
data directory. Use one controller/data directory for the machine; independent
legacy processes and externally started models are not governed by this lock.
Cancellation without confirmed provider termination holds the reservation until
explicit supervisor reconciliation.

Execution, verification, acceptance and integration are separate facts.
Acceptance names the exact controller candidate hash; a changed candidate
invalidates it. Uncertain dispatch reconciles its owned container identity and
does not start another agent loop. All transitions remain in the audit table.

Local inference does not make Codex supervision offline. Context and evidence
given to Codex follow its configured data path. Efficiency and quality remain
hypotheses until the comparable pilot is run.
