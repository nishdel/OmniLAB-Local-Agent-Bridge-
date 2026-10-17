# Windows qualification addendum

This addendum records the remaining-gates pass against the frozen recovery
candidate. It is a qualification record outside that candidate's public export;
no runtime, test, dependency, model selector or packaged file changed. The
[recovery verdict](RECOVERY.md) and its process-crash limitations remain accepted.
The earlier [readiness report](RELEASE-READINESS.md) is the historical baseline.

Qualified staged tree: `3a7d24cbf8c8d41c14d88fa6a6df326a6fa37ebb`.
Base commit: `8b02eba3deb02cc24393421b317644b183114a09`.
The existing staged-file inventory remains authoritative; this document is the
only subsequent staged-file delta. No release was committed or published.

| Artifact | SHA-256 |
|---|---|
| localagentbridge-0.5.0.dev0-py3-none-any.whl | `3fde801aa34b5769ed68185ed7dfd857825d819f3af807f49bcc798ce37bbb2c` |
| localagentbridge-0.5.0.dev0.tar.gz | `7afe70772012d09328d4cb38617a06a982fb10173cc2def9f2bab3efd7208f10` |

## Results and remaining decisions

| Gate | Evidence | Result | Next action / owner |
|---|---|---|---|
| Exact installed candidate | Unchanged wheel/sdist hashes; installed modules equal wheel bytes | Pass | Retain these artifacts / release owner |
| Python 3.11 | Actual CPython 3.11.9 AMD64, Tcl/Tk 8.6.12; 361 installed-package tests passed | Pass | None for this interpreter gate |
| Privileged symlink | Existing test deliberately excluded; no symlink privilege or Developer Mode available | Not tested | Run the existing isolated test with already available or explicitly approved privilege / owner |
| Bounded resource capture | One installed GPT-OSS task; raw process and hidden Tk samples retained | Pass, capture only | Select reference hardware/workload and acceptance limits / owner |
| Resource/perceptual acceptance | No existing numerical thresholds; no human observation | Not tested | Define criteria before scoring; perform interface checklist / owner |
| Fresh Windows install | No exposed clean Windows VM or Sandbox; isolated installs only | Not tested | Run the procedure below on a genuinely clean machine / owner |
| Authenticated callback | Exact prompts and command template prepared; zero authenticated invocations | Not tested | Approve the private bounded request before sending / owner |

The Python 3.11 run excludes the 50 already accepted recovery tests and the one
privilege-dependent symlink test: 361 passed, 1 deselected in 139.27 seconds.
The unchanged candidate's baseline full Windows suite remains 411 passed,
1 skipped; its installed recovery suite remains 50 passed. Those results are
historical evidence, not newly rerun tests. Existing fake-provider benchmark
unit tests do not constitute a live model benchmark.

CPython came from the official 3.11.9 NuGet package, with the matching signed
Python Software Foundation Tcl/Tk component extracted into private storage.
No system Python registration, PATH change or installer execution was needed.
This establishes an actual 3.11 interpreter test, not fresh-machine acceptance.

The predeclared measurement used 20 seconds idle, 100 settings transactions,
one exact `gpt-oss:20b` synthetic boundary review (423 input / 122 output tokens),
and five seconds after completion. The installed runtime was Python 3.13.14.
Controller startup was 0.875 seconds. Controller/worker CPU averaged 0.71% of
one core idle and 4.63% active; sampled RSS peaks were 56.6 and 124.8 MiB.
The separate hidden dock peaked at 57.3 MiB, with 18.1 ms p95 lateness for its
100 ms timer. Mean settings transaction time was 9.07 ms. Both owned processes
exited normally. Instrumentation contributes overhead; sampling can miss peaks.

The older observation used only two seconds idle (0.78% of one core, 43.2 MiB),
1.510 seconds startup and 9.76 ms settings writes. Different sampling windows,
model loading and one shared development host prevent a regression or speedup
claim. Ollama-name process samples omit differently named runner descendants
and GPU memory, and are not a complete inference footprint. No live callback
latency or human interaction latency was measured.

Owner decision: specify reference hardware, cold/warm workload, CPU/RSS scope
(companion, dock, or entire model runtime), startup/status latency and acceptable
idle/active resource limits. Set any new thresholds before a scored run. This
pass does not invent thresholds from the observed values.

The local review correctly identified the synthetic inclusive-boundary error.
Supervision graded it corrected because its downstream-impact claim was not
supported by the supplied snippet. No product patch followed. The isolated job
remains locally succeeded with a pending managed review and no Codex session;
telemetry feedback does not count as callback delivery, event approval or final
verification. Existing GPT-OSS preference and the exact installed
`qwen3:14b-q4_K_M` tag/digest remain unchanged.

## Human interface checklist

Record Windows version, display scale, screen resolution, keyboard, observations
and screenshots where useful. Automated native Tk checks do not pass these items.

| Check | Expected result |
|---|---|
| DPI | At supported owner-selected scales (include 100%, 150%, 200% where available), compact and expanded layouts remain readable; no clipped controls or inaccessible detail; moving between displays preserves usability |
| Readability | Run, model, queue, local execution and review labels are distinguishable; long exact model tags and evidence can be inspected without ambiguity |
| Keyboard | Tab/Shift+Tab follow a usable order with visible focus; keyboard operates model selection and buttons; Enter/Space act on the intended control |
| Focus | Refresh and new status do not steal focus from another app; explicit dock/tray activation gives usable focus; pin/unpin behaves as labelled |
| Hide/reopen | Close/Hide withdraws the dock; tray Show restores the same run/state; tray Quit closes only the dock and leaves an active owned worker independent |
| Status accuracy | Compare the dock with CLI status through queued, local generation and waiting-for-Codex states; local success remains distinct from review approval and completed verification; review/final states require explicit decisions |

The live callback's reviewing/completion sequence remains authorization-gated.
Do not create artificial approval just to obtain a green status screenshot.

## Short fresh-Windows procedure

Prerequisites: a genuinely clean supported Windows x64 machine/VM with approved
Python 3.11 including Tcl/Tk, Git, Ollama, and an already available completion
model. No model is bundled; stop if a model transfer/download needs permission.
Use an isolated Git fixture with an existing HEAD, never the stable checkout.
No paid machine provisioning or security setting changes are implied.

1. Copy the exact wheel, sdist, `requirements.lock.txt`,
   `examples/companion-task.json` and this checklist to a clean folder. Verify
   both SHA-256 values above with `Get-FileHash`. Retain a PowerShell transcript.
2. Confirm `py -3.11 --version`; create `.venv` with `py -3.11 -m venv .venv`.
   Install the wheel using `.\.venv\Scripts\python.exe -m pip install
   "./localagentbridge-0.5.0.dev0-py3-none-any.whl[tray,dev]" -c requirements.lock.txt`.
   Run `pip check`, package `--help`, and `python -m tkinter` using that venv.
   Record `sys.version`, `sys.executable` and `localagentbridge.__file__`.
3. Create only a private `config.local.toml`: `source_root` is the disposable
   Git fixture, `data_dir` is new private storage, `model` is an exact installed
   tag, and `thinking = "low"` for GPT-OSS. Use
   `python -m localagentbridge --config config.local.toml companion inventory`,
   then `select`, `create`, and `submit --run RUN_ID --request companion-task.json`.
   Run `companion controller --once` without a Codex executable. It starts the
   detached worker; poll `companion status --run RUN_ID` until terminal local
   state. Expect local success and pending review, never automatic verification.
4. Run `companion dock` and complete the checklist. Close the dock after review.
   If symlink creation is already allowed, extract the exact sdist to `source`
   and run the existing `tests/test_bridge.py::test_symlink_rejected` with the
   installed venv from outside the source directory:
   `python -I -m pytest source/tests/test_bridge.py::test_symlink_rejected -q -rs
   -p no:cacheprovider --basetemp symlink-fixture`. Adjust `source` to the actual
   extracted root. A skipped result remains not tested. If privileges are
   absent, stop that check and request explicit owner approval separately.
5. Retain hashes, interpreter/package paths, install/test logs, status and human
   observations. Stop before `init-review` or any `--codex-exe` option unless the
   separate bounded callback request has been approved.

The private evidence bundle contains exact application callback prompts,
payload hashes, CLI version/authentication method, anticipated context, retry
limitations and the bounded approval request. It contains no exported credential.
No production defect requiring a change was found during this pass. Release
qualification remains open for the environment, criteria, human and authorization
gates above; the accepted recovery verdict is unchanged.
