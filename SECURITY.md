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
(repository Security tab → Report a vulnerability). Reports are visible privately
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
