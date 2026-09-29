# Manual release testing

Test definitions live here; **execution results live only in the release-testing issue's single status table**. The checked-in issue-body draft is a starting document, not an execution ledger. Do not tick historical documentation checkboxes or add a second completion checklist.

Use disposable sample content and a test account/profile. Review screenshots and diagnostics before sharing; remove usernames, private filenames/paths, content, credentials, tokens and identifiers that grant access. Report public package names, hashes, OS/device details and synthetic labels only.

## Recording results

Use these columns exactly:

ID | Test | Expected result | Tested | Result | Issue registered | Tester / date | Evidence / notes

- Tested: **No / Partially / Yes / N/A**. Result: **Not tested / Pass / Fail / Blocked / N/A**.
- Issue registered: **— / Not needed / Pending / linked issue number**.
- New rows start **No / Not tested / — / — / —**. Only record Pass after every expected result for that row was observed; Pass requires Yes. Incomplete observation stays Partially with Not tested, or Fail/Blocked when supported by evidence.
- Record the person who performed the test and actual date, not the person transcribing it. Blocked and N/A require a reason; N/A is not a pass. Failed rows require Pending or a linked defect.
- Search/reuse a relevant existing defect before opening another. Closing a defect does not pass its test: explicitly retest the affected candidate.
- Above the table, record release/package, source and definition snapshot, SHA-256, environment, owner, and counts in this order: **Passed / Failed / Blocked / Not tested / N/A**. Counts refer to the Result column of current-candidate rows, including selected conditional rows.
- On a new candidate, preserve the old table/evidence verbatim in an issue comment labelled with its candidate/hash before updating the current table. Record changed behavior and affected IDs. Reset affected rows to No / Not tested; carry an unaffected result only with an explicit owner rationale and its original tester/date/candidate. If impact is uncertain, repeat it. A different artifact always repeats package identity/launch.
- Repeating on a different OS/device uses separate rows with a stable ID plus environment suffix, each linking the same definition. Keep detailed steps out of issue cells.
- Automated evidence belongs in a separate short evidence paragraph, with exact source/artifact and limitations. Release-owner scope, risk, signing, callback and publication approvals belong in a separate decision paragraph. Neither can set a human-test row to Pass.

## Conditional scope

Core tests are deliberately small. Conditional tests activate for the named changed feature, supported platform, installed hardware, or release risk. Missing a required environment means Blocked once assessed, not an automatic N/A. The owner records the applicability decision and reason. Unselected inherited requirements remain open; they are not waived by a core pass.

## Setup and launch (Windows owner handoff)

The owner supplies one **test kit** containing the exact wheel from the issue,
matching requirements.lock.txt, examples/companion-task.json renamed task.json,
and a disposable sample-repo with an existing Git HEAD. No public companion
installer is claimed. Stop if the kit or prerequisites are missing.

Prerequisites: normal Windows account, Python 3.11+ including Tcl/Tk, Git,
already installed Ollama and an existing completion model. Use the existing
GPT-OSS preference; no automatic model download/delete. A fresh-machine check
requires a genuinely clean host, not merely this venv.

Extract the kit, open that folder in File Explorer, type powershell in its
address bar, and run the following (the working directory must be the kit):

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install "./localagentbridge-0.5.0.dev0-py3-none-any.whl[tray]" -c requirements.lock.txt
notepad .\manual.toml
```

Save this exact TOML in manual.toml in the kit. These relative paths resolve
inside the kit; do not use an existing personal configuration or data directory:

```toml
model = "gpt-oss:20b"
endpoint = "http://127.0.0.1:11434"
source_root = "sample-repo"
data_dir = "manual-state"
thinking = "low"
num_ctx = 8192
max_input_chars = 10000
max_output_tokens = 600
max_output_bytes = 3000
```

Open the dock:

```powershell
.\.venv\Scripts\python.exe -I -B -m localagentbridge --config .\manual.toml companion dock
```

For LAB-M03, use a second PowerShell window in the same kit. Save the returned
run_id, substitute it for RUN_ID below, and submit exactly once:

```powershell
.\.venv\Scripts\python.exe -I -B -m localagentbridge --config .\manual.toml companion create
.\.venv\Scripts\python.exe -I -B -m localagentbridge --config .\manual.toml companion submit --run RUN_ID --request .\task.json --model "gpt-oss:20b"
.\.venv\Scripts\python.exe -I -B -m localagentbridge --config .\manual.toml companion controller --once
.\.venv\Scripts\python.exe -I -B -m localagentbridge --config .\manual.toml companion status --run RUN_ID
```

The once-controller starts a detached worker; status may still be running.
Repeat only status to observe completion. Do not add init-review or --codex-exe:
those enable the separately authorization-gated callback. Keep the test kit's
state private; publish sanitized observations only.

The source [quickstart](QUICKSTART.md), [troubleshooting](TROUBLESHOOTING.md),
[workflow/checkpoint guide](COMPANION-WORKFLOWS.md), and existing
[clean-Windows / privileged-symlink procedure](WINDOWS-QUALIFICATION.md#short-fresh-windows-procedure)
remain authoritative. The symlink test is **automated evidence**, run only with
already available or explicitly approved privileges; a skip is not a pass.
The existing callback approval packet stays private and is separately reviewed
by the owner; never paste its local paths or raw metadata into a public issue.

## Core scenarios

<a id="lab-m01"></a>
### LAB-M01: Packaged launch

**Prerequisite:** Approved wheel, Python 3.11+ with Tk and prepared test kit above.

1. Run the setup/launch commands above from the extracted kit.
2. Read the package identity supplied by the owner and open the dock.

**Expected:** Dock opens from the identified package.

<a id="lab-m02"></a>
### LAB-M02: Exact model selector

**Prerequisite:** Existing Ollama and model inventory; no download/delete permission implied.

1. Open the model list; confirm the existing GPT-OSS preference and exact qwen3:14b-q4_K_M entry where installed.
2. Select the existing GPT-OSS tag, choose Save default, and reopen the dock.
3. Check that the default persists only in this test data directory; record absent entries without substituting a similarly named model.

**Expected:** Exact tags appear; selected default persists.

<a id="lab-m03"></a>
### LAB-M03: One local task

**Prerequisite:** Prepared synthetic task, disposable Git fixture with an existing HEAD, available selected model.

1. Run the create/submit/controller commands above once; watch queued and local generation states.
2. When local work ends, inspect status and the saved result/evidence.
3. Confirm the review is pending/waiting_for_codex and the run is not automatically verified. Do not approve or finalize it just to obtain a green status.

**Expected:** Saved local result awaits explicit review.

<a id="lab-m04"></a>
### LAB-M04: Keyboard and focus

**Prerequisite:** Dock open; another harmless app available.

1. Use Tab/Shift+Tab through controls and operate the model selector with the keyboard.
2. Use Enter/Space on the intended control, then work in the other app during a refresh.
3. Activate the dock explicitly and check visible, usable focus.

**Expected:** Controls work without refresh stealing focus.

<a id="lab-m05"></a>
### LAB-M05: DPI and readability

**Prerequisite:** Owner-selected supported display scales; use 100%, 150%, 200% where available.

1. Inspect compact/expanded layouts and long model/status text at each available scale.
2. Move between displays if available; inspect details and critical controls for clipping.
3. Record each tested scale and any inaccessible text/action; do not infer a pass for unavailable displays.

**Expected:** Text, controls and evidence remain readable.

<a id="lab-m06"></a>
### LAB-M06: Hide and reopen

**Prerequisite:** LAB-M03 running, or a separately approved small test job.

1. Hide/close the dock and reopen it from tray Show companion.
2. Use tray Quit dock while the worker is active; inspect status from the separate console.
3. Launch the dock again and confirm the same job/result remains. If no active interval was observed, leave worker-independence untested.

**Expected:** Same run returns; dock exit leaves work independent.

## Conditional scenarios

<a id="lab-c01"></a>
### LAB-C01: Conditional: missing Ollama

**Prerequisite:** Owner-prepared second config using an unused loopback port and separate test data.

1. Open that config's dock and request model inventory.
2. Read the unavailable/stale guidance and compare with troubleshooting; do not stop the real service.
3. Close this test instance and return to the normal isolated config.

**Expected:** Unavailable inventory gives actionable guidance.

<a id="lab-c02"></a>
### LAB-C02: Conditional: absent model

**Prerequisite:** Owner-prepared synthetic task and a definitely absent tag; no model downloads.

1. Submit the synthetic task with the absent exact tag in an isolated run.
2. Read the missing-model message; verify no alternative model/job execution is substituted.
3. Use guidance only; do not download or delete a model to complete this check.

**Expected:** Exact missing tag is rejected without substitution.

<a id="lab-c03"></a>
### LAB-C03: Conditional: workflow checkpoint

**Prerequisite:** Owner-assisted existing workflow example and approved bounded local work.

1. Follow the durable workflow guide for one workflow-submit and workflow-next.
2. Inspect the saved handoff and checkpoint after local completion; verify no automatic approval.
3. Have the supervising owner record an actual reviewed checkpoint/decision, then compare workflow-status and dock state.

**Expected:** Saved handoff stops at an explicit decision.

<a id="lab-c04"></a>
### LAB-C04: Conditional: live callback

**Prerequisite:** Separate explicit approval of the exact bounded callback payload, context, quota/retry limits and destination.

1. Use the existing owner approval packet; stop if approval is absent or identities differ.
2. After authorization only, have the owner run its one initialization/one review sequence and observe the exact-session handoff.
3. Observe delivery followed by a separate supervising decision; retain only sanitized public evidence. Do not induce quota exhaustion or authentication failure.

**Expected:** One authorized review still needs a decision.

<a id="lab-c05"></a>
### LAB-C05: Conditional: clean Windows

**Prerequisite:** Approved clean Windows machine/VM and already available prerequisites/models.

1. Follow the clean-Windows procedure linked above with the exact wheel.
2. Record interpreter, package hash, installation and normal-user launch.
3. Do not describe another venv on a development machine as fresh-machine acceptance.

**Expected:** Package starts on a genuinely clean host.

<a id="lab-c06"></a>
### LAB-C06: Conditional: perceived response

**Prerequisite:** Owner has selected hardware, cold/warm workload, latency and resource scope/limits.

1. During one approved small task, observe model-list, detail and status responsiveness.
2. Compare observations with criteria chosen before the run and separately cite measured resource evidence.
3. Record visible stalls and environment; hidden Tk timing alone cannot pass this row.

**Expected:** Bounded interaction meets predeclared criteria.

## Retained requirements and conditional selection

The [Windows qualification addendum](WINDOWS-QUALIFICATION.md) supplies the
remaining owner gates; [recovery](RECOVERY.md) remains accepted for its tested
process-crash model. Do not repeat that audit as human testing or infer power-loss
safety. Unsaved/ambiguous output requires intervention, never invented recovery.

Keep fresh Windows (LAB-C05), callback authorization (LAB-C04), and performance
criteria (LAB-C06) distinct. The existing Python 3.11, package and process-crash
results remain automated evidence tied to their original artifacts. Callback
authentication/quota fixtures are not live proof. Retained v0.4.1/v0.5 workflow,
routing and checkpoints use LAB-C03 when affected; model selection remains public.
