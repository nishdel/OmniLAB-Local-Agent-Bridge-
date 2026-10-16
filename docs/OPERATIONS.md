# Standalone access and Docker operations

Opening a control application, running an inference server and dispatching an
OmniLAB job are distinct actions. An installed application can be opened while
its server is stopped; its browser URL becomes available only when that server
is serving. Loading a model still requires its existing preflight and authorization.

## Open the component you need

| Component | Standalone entry | Relationship to OmniLAB |
|---|---|---|
| OmniLAB | Companion CLI and native dock; [quickstart](QUICKSTART.md) | Durable policy, jobs, evidence and review; there is no general LAB browser app |
| Ollama | Installed Ollama app/CLI; optional separately installed Open WebUI | Inference for advisory and qualified implementation profiles |
| Open WebUI | Its configured browser port; the inspected personal installation maps port 3000 | Independent chat frontend with its own retained volume; not required by LAB |
| OpenHands | Its separately installed application, if present | LAB uses the pinned SDK in disposable restricted containers, not the standalone web app |
| Strata | Installed **Strata Control**; browser at `http://127.0.0.1:8080` during an authorized session | Standalone inference and experimental alternative backend; implementation still uses OpenHands |

An `agent-server` container is not evidence that a complete OpenHands browser UI
is installed. Consult that application's actual setup before advertising a URL.
Do not start an old agent-server container merely to obtain a browser interface.
Its network and permission settings differ from LAB's restricted executor.

The personal Strata Control currently refuses Start until separate live approval
and safety gates pass. Its frozen configuration is not lazy-loading; starting its
server may immediately load weights. A shortcut to port 8080 must not bypass that
control. The target Coder shards are already present; see the
[qualification roadmap](INFERENCE-ROADMAP.md). Browser availability and successful
model inference must be reported separately.

Independent experimental applications outside this deployment retain their own
entry points and models; see [research scope](research/JANAS.md).

## Understand LAB containers before cleanup

LAB creates short-lived containers for an agent attempt, protected baseline and
candidate verification. Names normally start with `lab-`; the authoritative
ownership label is `org.omnilab.owner`, and `org.omnilab.mode` identifies the role.
Old build/qualification containers can have other `org.omnilab.*` labels.
Names alone are insufficient evidence that deletion is safe.

Source: [`DockerSandbox.create/inspect/stop`](../localagentbridge/sandbox.py),
[`implementation/verify/collect_then_stop`](../localagentbridge/selective.py).
The qualified transport uses no external network, drops capabilities, runs as a
non-root user and enforces memory/CPU/process/storage constraints. Read-only tmpfs
artifacts must be collected before stop; an already stopped container cannot
recover lost tmpfs evidence by restarting it.

For each cleanup candidate, inspect exact ID, labels, state, mounts, image digest,
writable-layer changes and related job/reservation state. Archive inspect data,
logs and any persistent unique files before removing an owned stopped container.
Retain the image needed by qualified profiles and any image that preserves build
results. Keep models, named volumes, bind-mounted evidence and unrelated services.

Do not run blanket `docker system prune`, volume pruning, or force-remove running
containers. A stopped UI with a named volume is not disposable test debris.
Record what was removed and retained, then recheck inventory. Docker cleanup does
not change lane qualifications or authorize inference startup.

## Documentation maintenance and publication

The [documentation index](index.md) is the navigation entry. Keep implementation
claims in [Workflow](WORKFLOW.md), current provider plans in the
[roadmap](INFERENCE-ROADMAP.md), and dated findings in existing qualification
reports. Preserve historical URLs and evidence instead of deleting old reports.

The website is generated from allowlisted Markdown by
[`website/build.mjs`](../website/build.mjs). It includes source links, Mermaid
diagrams, search and a visible development status. A documentation publication
does not merge the development PR, release a package or install a new controller.
Run the documentation and public-source checks before publication. Public pages
must not include private configs, model artifacts, local paths, job databases or
unsanitized operational logs.
