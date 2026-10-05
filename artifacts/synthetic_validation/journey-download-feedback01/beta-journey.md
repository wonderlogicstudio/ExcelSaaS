# Beta journey evidence — 2026-09-27

Baseline product ffd6647. Chrome2 authenticated protected beta, new test tab209534438; existing user tab preserved. No deployment during this unit.
Input: monthly-repair-flow06/stage3/monthly-rp03-supported-6sheet.xlsx. Oracle: stage1/expected-control.json.

Observed actual UI: structure0/formula1; Budget N18 =N15-N14 -> ='M10'!B16-'M10'!B15; #VALUE! -> -5. Exact-change checkbox and explicit approve separate from test entitlement. Execute reached READY with three download controls. No mandatory cell/formula typing.
Actions: file select1; proposals2; server preview3; storage consent4; preflight5; beta-only checkbox6 and example7; step3=8; exact acknowledgement9; approve10; execute11; bulkdownload12. Core10 + beta2, BUT this is request count, NOT successful all3 receipt. Recovery changes13 and HTML14.

File chooser PASS. waitForEvent(download) timed out20s. Internal chrome downloads page denied by browser URL policy; no bypass attempted. Used read-only filesystem inspection of expected product output names, not browser history. Actual Downloads directory has only workbookcare_repaired_b14aa3f6-e157-43b5-a4e4-6ccb28f062d1.xlsx after both individual recovery buttons. No visible app error. Cause of missing files not established; possible browser download permission, not claimed proven. Do not mark complete E2E or all3 downloads PASS.

Read-only zip/XML verification: original SHA256 unchanged, exact target formula and numeric cache-5.0 PASS, only business formula N18 changed; other14 formula caches refreshed. Output SHA25696ffbca2612f4ab0611f5b01bce606008ed603dfed835684eb435f2f873d41cd matches prior native Excel evidence compatibility-final/excel-reopen.json. This is reused native proof, not a new Excel execution. Initial checker exit1 assumed literal-5 instead of numeric-5.0; corrected. Next checker exit1 compared cache XML as business edits; corrected to separate unchanged-formula cache updates, final exit0. Product/expected oracle not changed to fit outputs.

Largest bounded usability defect: bulk/individual requests leave no persistent per-file feedback and no clear save-verification distinction. RepairDelivery feedback only authorized. Missing-files root cause and two artifact content checks remain pending; no ZIP or browser settings changes in this unit. Targeted frontend tests and independent review; no engine/Excel/PG/full-regression reruns.

Evidence: beta-ready.png, inspect_download.py, download-inspection.json. Shell startup git/read commands0 (one filename-glob search emitted error then corrected source path; no product impact); focused native-hash search returned1 due private-state permission, matching evidence file itself found. Product source owned by builder; unrelated dirty checkout preserved.