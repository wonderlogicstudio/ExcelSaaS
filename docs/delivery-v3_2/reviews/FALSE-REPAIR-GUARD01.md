# FALSE-REPAIR-GUARD01 - bounded local verification PASS

Date: 2026-09-27. Owner approved necessary false-repair rules only. STOP after one defect under EFFICIENCY-02.

## Actual change and reuse

Six production lines in apps/api/app/delivery_inputs.py and app/repair_rules/numeric_text.py identify pure multi-digit all-zero number formats and refuse numeric-text conversion. Styled text 123 with format 00000 changed from PRELIMINARY_ONLY/eligible1 before the fix to UNSUPPORTED/eligible0. This is conservative ambiguity handling, not proof that every such cell is an identifier. General, 0 and #,##0 controls remain eligible. Existing planning, patching, POI calculation, preservation checks, approval and fingerprint gates were reused; no engine/UI expansion.

## Execution evidence

Exact commands, exit codes and hashes: [builder report](../../../artifacts/synthetic_validation/false-repair-guard01/builder-report.md). New guard tests3, rule tests2, monthly negative tests2 passed; Ruff, real artifact command and CRLF-aware diff check exit0. Three existing preflight controls also passed in the earlier mixed run; that invocation had separate temporary-directory setup failures, so it is not an all-pass command. The initial baseline run failed the E3 assertion and encountered a temporary-directory permission error, both retained in evidence.

[Actual result](../../../artifacts/synthetic_validation/false-repair-guard01/supported-control-result.json) proves separate XLSX output: B2 numeric1200, B3 numeric0, F3 formula =C3*D3 with calculated20. G2 retains =C2+D2, calculated5. Original hash unchanged; unselected F4 remains blank, E2:E5 preserved, non-target values/formulas/styles preserved. Formula cache and recalculation metadata updates are separately classified. Low-level plan/patch verification does not prove customer approval or full API delivery.

Frozen original oracle had invalid sheet-label encoding; v2 corrects only the label. V2 G2 =C2*D2+7 is unsupported by the existing calculation grammar and remains ENGINE_UNSUPPORTED, not repaired PASS. A separately frozen supported control changes only G2 input/expectation to =C2+D2/5. All oracle versions and errata are retained.

## Independent review

false_repair_guard_review: PASS, no blocking findings. Read-only ZIP/oracle verification exit0 independently bound source/output/oracle hashes, exact changed cells B2/B3/F3, all style references and four byte-identical non-target ZIP members. Reviewer did not duplicate tests/engine execution; test results are attributed builder evidence.

## Limits and next single unit

Automatic formula discovery abstained for insufficient evidence; detector comparison NOT_ESTABLISHED. No claim of automatic discovery-to-repair acceptance. Native compatibility is STALE because the existing patch fingerprint correctly changed. Existing plans retain their stale-plan guard. Do not refresh the reference without real compatibility evidence.

Full regression, native Excel compatibility refresh, exact-approved API delivery, beta deployment/browser receipt, commit and push were NOT RUN in this unit. Existing beta remains unchanged; historical missing two-download receipt issue remains open. No commercial/public readiness claim.

Next proposed unit: final regression and native compatibility refresh, then protected beta release and actual receipt verification if those gates pass. Requires separate owner confirmation under EFFICIENCY-02; not started.
