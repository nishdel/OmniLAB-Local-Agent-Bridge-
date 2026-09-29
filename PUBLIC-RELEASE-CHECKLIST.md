# Public release checklist — companion candidate

This is an unreleased development candidate. See
[release readiness](docs/RELEASE-READINESS.md) for exact observed results.
Historical v0.4.1 verification remains in VERIFICATION-v0.4.1.md; its checkmarks
do not certify this candidate. No publication is authorized by this checklist.

## Implemented and checked

- [x] Existing repository and stable release preserved; development uses a separate worktree.
- [x] Coordinating runtime frozen; original source hashes unchanged.
- [x] Exact installed-model selection, durable jobs/results, outbox and review gates.
- [x] Duplicate/restart/cancellation/ownership and unavailable-review regressions.
- [x] Real local GPT-OSS code, test and documentation contributions, including rejections.
- [x] Native Tk dock controls and independent controller/worker lifetime tests.
- [x] User, contributor, configuration, security, upgrade and architecture documentation.
- [x] Public allowlist audit; wheel/source content inspection; clean venv install.
- [x] Synthetic v0.4.1 database upgrade and uninstall preserving data.
- [x] Obsolete/unreachable code removed; meaningful safety tests and evidence retained.
- [x] MIT and separately installed dependency notices retained.
- [x] Actual pre-companion v0.5 feature-preservation matrix and reachable catalog/workflow regressions.
- [x] Durable workflow steps/checkpoints reuse the existing engine, budgets and evidence validation.
- [x] Exact installed Qwen3 14B retained and exercised in independent sequential consensus.
- [x] Direct Bridge versus workflow/consensus development contributions identified explicitly.

## Remaining gates

- [ ] Specifically approved live Codex callback and exact-session resumption.
- [x] Packaged local workflow with independently recorded Codex review and finalization (no authenticated callback claim).
- [ ] Fresh Windows-machine acceptance beyond this host's clean virtual environment.
- [ ] Python minimum-version and other supported-platform compatibility matrix.
- [ ] Active CPU/peak memory, true callback latency and perceptual UI measurements.
- [ ] Native symlink rejection under Windows Developer Mode or equivalent symlink privilege.

The [focused recovery repair](docs/RECOVERY.md) resolves the reproduced
cross-database process-crash blocker. Legacy missing output and ambiguous records
remain explicit intervention cases. Callback, fresh-machine and visual gates
are separate from that verdict; the original broad preservation audit is retained.

The candidate does not bundle a model, require one public model tag, automatically
buy credits, or publish releases. Pattern scans and tests are scoped evidence,
not proof against every possible security issue. Keep raw task/results and model
history private; publication needs a separate explicit decision after its gates.
