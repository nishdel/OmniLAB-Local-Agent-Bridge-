---
name: Release manual testing
about: Record human observations for one exact release candidate
title: "[Manual release testing] VERSION — CANDIDATE"
labels: ""
assignees: ""
---

Release/version: OWNER TO FILL

Candidate/package filename and SHA-256: OWNER TO FILL

Product source commit (and staged/export snapshot if applicable): OWNER TO FILL

Test-definition commit: OWNER TO FILL; replace /blob/companion-release-candidate/ links below with that immutable documentation commit before opening.

Environment (OS/build/architecture, display/devices, disposable data/profile, dependencies): OWNER TO FILL

Checklist owner: OWNER TO FILL; actual testers/dates belong in rows.

Summary — Passed: 0 / Failed: 0 / Blocked: 0 / Not tested: 6 / N/A: 0

Use this issue's table as the sole execution status authority. New rows are No / Not tested. Tested: No / Partially / Yes / N/A. Result: Not tested / Pass / Fail / Blocked / N/A. Issue registered: — / Not needed / Pending / linked issue number. Pass requires all expected results actually observed and Tested=Yes. Record the actual tester/date. Blocked/N/A need reasons; failed rows need Pending or a linked existing/new defect. A closed defect never passes its retest. N/A is excluded from passes.

On a candidate change, first preserve the previous table/evidence in an issue comment labelled with its candidate/hash. Record affected IDs and reset them to No / Not tested; retain unaffected results only with owner rationale and original candidate/tester/date. Use separate rows for separate environments. Keep the summary synchronized with current rows. Do not copy results into repository documents, infer human acceptance from automation, or open a new release-testing issue for each development task.

Definitions and exact setup: [manual guide](https://github.com/nishdel/OmniLAB-Local-Agent-Bridge-/blob/companion-release-candidate/docs/MANUAL-RELEASE-TESTING.md). Select conditional cases before release sign-off; add each as its own row and adjust counts. This template's initial core rows are not an acceptance result.

| ID | Test | Expected result | Tested | Result | Issue registered | Tester / date | Evidence / notes |
|---|---|---|---|---|---|---|---|
| [LAB-M01](https://github.com/nishdel/OmniLAB-Local-Agent-Bridge-/blob/companion-release-candidate/docs/MANUAL-RELEASE-TESTING.md#lab-m01) | Packaged launch | Dock opens from the identified package. | No | Not tested | — | — | — |
| [LAB-M02](https://github.com/nishdel/OmniLAB-Local-Agent-Bridge-/blob/companion-release-candidate/docs/MANUAL-RELEASE-TESTING.md#lab-m02) | Exact model selector | Exact tags appear; selected default persists. | No | Not tested | — | — | — |
| [LAB-M03](https://github.com/nishdel/OmniLAB-Local-Agent-Bridge-/blob/companion-release-candidate/docs/MANUAL-RELEASE-TESTING.md#lab-m03) | One local task | Saved local result awaits explicit review. | No | Not tested | — | — | — |
| [LAB-M04](https://github.com/nishdel/OmniLAB-Local-Agent-Bridge-/blob/companion-release-candidate/docs/MANUAL-RELEASE-TESTING.md#lab-m04) | Keyboard and focus | Controls work without refresh stealing focus. | No | Not tested | — | — | — |
| [LAB-M05](https://github.com/nishdel/OmniLAB-Local-Agent-Bridge-/blob/companion-release-candidate/docs/MANUAL-RELEASE-TESTING.md#lab-m05) | DPI and readability | Text, controls and evidence remain readable. | No | Not tested | — | — | — |
| [LAB-M06](https://github.com/nishdel/OmniLAB-Local-Agent-Bridge-/blob/companion-release-candidate/docs/MANUAL-RELEASE-TESTING.md#lab-m06) | Hide and reopen | Same run returns; dock exit leaves work independent. | No | Not tested | — | — | — |

Automated evidence (separate): link exact source/artifact results and limits; do not transfer them to Pass above.

Release-owner decisions (separate): applicability and unresolved gates, authorizations, signing/publication and any performance criteria. This issue does not grant approval.

Candidate/retest history: record changes and affected IDs; keep prior table/evidence in labelled issue comments. Sanitized public evidence only; no private paths/files, credentials, raw databases or tokens.
