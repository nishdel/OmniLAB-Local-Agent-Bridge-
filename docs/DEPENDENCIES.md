# Dependency and license review

Scope: source-only LocalAgentBridge release, unmodified dependencies installed
separately, no bundled dependency binaries or model weights. Package metadata and
installed LICENSE/COPYING files were inspected. Exact versions are constrained by
requirements.lock.txt. Every listed distribution contains license notices.

LocalAgentBridge is released under MIT with the LocalAgentBridge contributors
attribution. Dependency and model licenses remain separate.
See [MIT](https://opensource.org/license/mit) and
[Apache-2.0](https://www.apache.org/licenses/LICENSE-2.0).

Ollama models have separate licenses; check the exact tag and upstream model card.
The project MIT license grants no rights to downloaded weights. Python/Tcl/Tk,
Ollama and Codex are user-installed prerequisites, not redistributed here.

For v0.4.1, all 44 constrained versions and packaged license notices were checked
again; the dependency list is unchanged and `pip check` passes in the fresh
environment. The installed Qwen3 4B, Qwen3 14B Q4_K_M and GPT-OSS 20B artifacts
each expose Apache-2.0 notices through `ollama show --license <tag>`. Inspect the
exact artifact you install, including upstream model-card terms; these notices
are not replaced by LocalAgentBridge's MIT license. No models, Ollama caches or
third-party dependency code are distributed by this source-only project.

## Distribution findings

- pystray is LGPLv3 with accompanying GPL terms. It remains a separately installed,
  replaceable Python dependency. A future bundled executable must preserve its
  notices and meet corresponding-source/relinking obligations.
- certifi and pathspec are MPL-2.0. Preserve applicable file notices and source
  obligations if redistributing/modifying them. None are in this source release.
- pywin32 includes multiple component notices, including LGPL-2.1. Its top-level
  metadata alone is insufficient to audit a future frozen application.
- cryptography, packaging and other dependencies retain their license choices.
  Native libraries inside downloaded wheels retain their packaged notices.
- No copyleft library source was incorporated into bridge files. The source-only
  release retains MIT while users install unmodified dependencies separately.
- No wheels, interpreter, model weights or third-party source are allowlisted.
  A later binary bundle requires a new component/license audit before release.

This review covers license identity and the current distribution plan, not a
vulnerability audit or a guarantee about future versions. Repeat it when the
constraints or distribution format change.

The build backend is separately installed setuptools (MIT). Version 77 or later
is required for SPDX license metadata and license-files, per its
[license migration guide](https://setuptools.pypa.io/en/stable/userguide/license_migration.html).
Build tooling is not vendored in the source release.

## Installed distribution inventory

| Package | Version | License | License files present |
|---|---|---|---:|
| annotated-types | 0.8.0 | MIT | 1 |
| anyio | 4.15.1 | MIT | 1 |
| attrs | 26.1.0 | MIT | 1 |
| certifi | 2026.7.22 | MPL-2.0 | 1 |
| cffi | 2.1.1 | MIT-0 | 1 |
| click | 8.5.0 | BSD-3-Clause | 1 |
| colorama | 0.4.6 | BSD-3-Clause | 1 |
| cryptography | 50.0.1 | Apache-2.0 OR BSD-3-Clause | 3 |
| h11 | 0.16.0 | MIT | 1 |
| httpcore | 1.0.9 | BSD-3-Clause | 1 |
| httpx | 0.28.1 | BSD-3-Clause | 1 |
| httpx-sse | 0.4.3 | MIT | 1 |
| idna | 3.19 | BSD-3-Clause | 1 |
| iniconfig | 2.3.0 | MIT | 1 |
| jsonschema | 4.26.0 | MIT | 1 |
| jsonschema-specifications | 2025.9.1 | MIT | 1 |
| mcp | 1.30.0 | MIT | 1 |
| opentelemetry-proto | 1.44.0 | Apache-2.0 | 1 |
| packaging | 26.3 | Apache-2.0 OR BSD-2-Clause | 3 |
| pathspec | 1.1.1 | MPL-2.0 | 1 |
| pillow | 12.3.0 | MIT-CMU | 1 |
| pluggy | 1.6.0 | MIT | 1 |
| protobuf | 7.36.1 | BSD-3-Clause | 1 |
| psutil | 7.2.2 | BSD-3-Clause | 1 |
| pycparser | 3.0 | BSD-3-Clause | 1 |
| pydantic | 2.13.5 | MIT | 1 |
| pydantic-settings | 2.15.0 | MIT | 1 |
| pydantic_core | 2.46.5 | MIT | 1 |
| Pygments | 2.21.0 | BSD-2-Clause | 1 |
| PyJWT | 2.13.0 | MIT | 1 |
| pystray | 0.19.5 | LGPL-3.0-or-later | 2 |
| pytest | 9.1.1 | MIT | 1 |
| python-dotenv | 1.2.3 | BSD-3-Clause | 1 |
| python-multipart | 0.0.32 | Apache-2.0 | 1 |
| pywin32 | 312 | PSF-style / component licenses (includes LGPL-2.1) | 7 |
| referencing | 0.37.0 | MIT | 1 |
| rpds-py | 2026.6.3 | MIT | 1 |
| ruff | 0.16.7 | MIT | 1 |
| six | 1.17.0 | MIT | 1 |
| sse-starlette | 3.4.11 | BSD-3-Clause | 1 |
| starlette | 1.6.0 | BSD-3-Clause | 1 |
| typing-inspection | 0.4.4 | MIT | 1 |
| typing_extensions | 4.16.0 | PSF-2.0 | 1 |
| uvicorn | 0.52.4 | BSD-3-Clause | 1 |

## Companion candidate

psutil is now a core dependency for process identity. Windows explicitly requires
pywin32 for native process creation identity and the retained owned-runtime tests.
The redundant benchmark extra is removed. Installed versions remain constrained
by the existing requirements.lock.txt; no new bundled third-party binaries.
