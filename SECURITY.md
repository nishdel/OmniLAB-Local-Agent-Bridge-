# Security

LocalAgentBridge is intended for local execution. MCP uses stdio; the optional
telemetry receiver binds only to 127.0.0.1. Role-based Ollama endpoints must be
loopback. Do not expose the receiver or Ollama publicly. This is not a hardened
multi-user service or a security boundary for untrusted repositories.

Local model responses are untrusted suggestions. They can invent facts, miss
requirements or follow malicious text inside source/logs. Codex must verify
evidence and decide whether a change is appropriate. Models receive content and
return bounded JSON; they never get shell access, command execution or file writes.
The discovery scanner has explicit path, size, time, secret-file and reparse-point
limits. Do not use those limits as a reason to supply secrets.

Normal storage contains usage metadata and local correlation identifiers, not
prompts/source contents. Explicit benchmark runs retain supplied exercises and
model responses in ignored local directories for review. Protect those directories
and any database backups. The collector does not scrape Codex's graphical UI.

## Reporting a vulnerability

Use [GitHub private vulnerability reporting](https://github.com/nishdel/LocalAgentBridge/security/advisories/new)
(repository Security tab â†’ Report a vulnerability). Reports are visible privately
to the maintainers and invited collaborators. Do not disclose vulnerabilities in
public issues or pull requests before coordinated disclosure.

Include the affected version, impact, minimal synthetic reproduction, expected
behavior and any suggested fix. Remove credentials, personal paths, identifiers,
private source, prompts and telemetry databases. Never upload a secret to prove
it can be exposed. Revoke exposed credentials through their provider.

If GitHub's private form is temporarily unavailable, open an issue asking only
for a private contact channel; wait for that channel before sharing details.
Ordinary bugs and feature requests belong in
[GitHub Issues](https://github.com/nishdel/LocalAgentBridge/issues).

## Supported versions and response

Security fixes target the latest released version (currently v0.4.1). Older
versions may require an upgrade. This is a volunteer-maintained project with no
guaranteed response time; follow up within the private advisory if needed.
Maintainers will coordinate validation, remediation and disclosure with the
reporter. Keep details private until a fix or disclosure plan is agreed.

## Companion candidate data and permissions

The companion database and its workflow recovery journal store user-supplied
task excerpts and local results; they are not metadata-only. The journal lives
in the companion's usage database. Keep the entire data_dir private to your
Windows user account. See [recovery](docs/RECOVERY.md) for durable evidence scope.
There is no network control listener. The filesystem/OS account is the access
boundary; the bridge does not sandbox another process running as that same user.
Do not put state on a shared/network directory or in a repository publication.

The selected source_root must match the exact Git worktree root and recorded HEAD.
Jobs carry bounded supplied excerpts rather than unrestricted file-read commands.
Treat repository content, local results and callback reports as untrusted evidence.
The supervisor retains shell execution, source modification and final validation.

Local-only inference rejects remote Ollama metadata in both tags and show. The
configured server remains trusted to report truthfully. Callback review explicitly
sends the bounded task objective and generated result to the authenticated Codex
service; this is cloud data flow, not an entirely offline workflow. Dedicated
read-only sessions disable shell and plugins, do not use --last, and retain the
normal CLI authentication. No credential copying, reset redemption or paid fallback.

Process actions use kernel locks and owned handles/creation identities. Shared
Ollama is never killed/unloaded. The protected benchmark Job Object logic remains
for its separately owned server tree. Never infer ownership from a process name.

Raw callback files may include excerpts, model results and local paths. Share only
manually redacted diagnostics. Authentication secrets are not intentionally stored,
but logs must still be reviewed before sharing; automatic comprehensive redaction
is not implemented. Report uncertain delivery honestly and inspect before retry.

## Optional implementation lane

The [selective executor boundary](docs/SELECTIVE-SETUP.md) confines OpenHands to
an owned Linux container with no host mounts/network/credentials and only selected
files. A worktree alone is never accepted as isolation. Missing Docker, immutable
image, storage quota, memory budget or tool compatibility blocks implementation.
The model cannot reach the LAB database, Docker socket, supervisor review API or
acceptance authority. LAB independently collects candidate bytes and runs approved
checks in a separate sandbox. Supervisor acceptance binds the exact candidate.
Local inference does not change the configured cloud data path of Codex supervision.

## Qualified local profile boundary

A personal profile is trusted supervisor configuration scoped to one checkout.
Identity, backend version, template, loaded context, runner offload/draft flags
and native request options must match its qualification. No model/quantization,
CPU or cloud substitution is permitted. Model outputs cannot edit the config,
grant permissions, change limits, choose acceptance outcomes or start services.

Whole-host RAM/VRAM checks cover loading and execution; a missing GPU diagnostic
is a stop, not permission to use CPU. Resource pressure cancels owned work and
retains unconfirmed inference reservations. Another provider's existing residency
blocks admission even when that alternate provider is disabled for new jobs.
Shared Ollama processes are never terminated by name.

The optional Strata adapter requires trusted config/artifact/process binding and
loopback-only listening sockets. Request model strings and aliases are not weight
identity. Strata lifecycle/MCP operations remain outside model-controlled tools.
Private machine paths and usage evidence are excluded from public packaging.
