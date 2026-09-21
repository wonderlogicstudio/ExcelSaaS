# HORIZONTAL-01 builder evidence

Status: implementation complete for the approved bounded detector unit.

Focused review correction:
- Hidden columns now exclude the whole horizontal run span between the run's min/max columns, so a hidden cell cannot shrink a wider `D:H` run into a detectable smaller visible run.
- New horizontal candidate title, description and detection-basis copy were restored to valid UTF-8 Korean.
- Negative fixtures now include an actual dominant tie and place unsupported target formulas at the interior `F8` position with normal left/right neighbors.
- Web scope copy now states limited same-row relative-A1 arithmetic support while preserving monthly-sheet/Table/horizontal blank-or-constant exclusions.

Scope implemented:
- Same-row, same-sheet, unanchored A1 arithmetic formula runs only.
- Contiguous formula run length >= 4.
- Interior outlier target only.
- Unique dominant pattern with at least 3 supporting neighbors.
- Immediate left and right formulas must both match the dominant pattern.
- Candidate emitted as `FORMULA_PATTERN_OUTLIER` with subtype `RELATIVE_REFERENCE_DRIFT`.

Scope preserved:
- Vertical outlier and formula-gap paths are unchanged.
- No repair eligibility, public M4 exposure, beta deployment, Excel replay, commit, or push.
- Sheet-qualified/monthly sheet-name patterns, functions, ranges, anchors, names, structured references, external refs, blanks, constants, Table, merged, hidden row/column, summary/manual rows remain excluded for this horizontal unit.

Frozen oracle mapping:
- `acceptance-oracle.json` case `normal` -> `test_detects_same_row_unanchored_arithmetic_reference_drift_from_run_formula_audit`, expected 0 horizontal outliers.
- `acceptance-oracle.json` case `column_drift` (`F8 =E6-F7`) -> same test, expected exactly `Horizontal!F8`, rule `FORMULA_PATTERN_OUTLIER`, subtype `RELATIVE_REFERENCE_DRIFT`, region `D8:H8`, evidence cells `D8,E8,G8,H8`.
- `acceptance-oracle.json` case `row_drift` (`F8 =F5-F7`) -> same test, expected exactly `Horizontal!F8`, rule `FORMULA_PATTERN_OUTLIER`, subtype `RELATIVE_REFERENCE_DRIFT`, region `D8:H8`, evidence cells `D8,E8,G8,H8`.
- Negative acceptance list -> `test_horizontal_reference_drift_excludes_unsupported_and_structural_cases`.
- Duplicate same rule/cell preservation -> `test_same_rule_cell_is_not_duplicated_between_vertical_and_horizontal_detection`.
- Existing vertical formula audit preservation -> existing `test_detects_supported_normalized_formula_pattern_outliers`.
- Default-off/free-scan/API isolation preservation -> existing `test_pattern_audit_is_default_off_and_emits_value_free_stable_evidence` and `test_formula_audit_is_separate_from_free_scan_contract`.

Final checks:
- Ruff targeted source/tests: PASS, exit 0.
- Targeted formula/API/quality pytest: PASS, exit 0, 18 passed, 1 pre-existing Starlette `TestClient` deprecation warning.
- Targeted web Vitest for `FormulaAuditPanel.test.tsx` and `UnifiedDiagnosis.test.tsx`: PASS, exit 0, 8 passed.
- Web type/build through `npm.cmd run build --workspace @workbookcare/web`: PASS, exit 0.

Not run by design:
- Full Excel/native replay.
- Full product regression.
- Hosted beta/browser verification.
- Commit, push, or deployment.

## PL final checkpoint: CHANGES_REQUIRED

Independent rereview found the grouped-hidden-column blocker remains after one correction: group C:F hidden, formula run D8:H8, mutant F8 can still be reported because individual keys do not cover ColumnDimension.min/max. Current HiddenSpan test hides H individually, not a real group. Other three findings resolved. Passing targeted tests are NOT complete acceptance. Stop under EFFICIENCY-02; no further automatic correction or deployment. Full regression/Excel/beta remain NOT_RUN. See review-result.json.

## Owner-approved grouped-hidden correction: PASS

Previous CHANGES_REQUIRED is superseded for the grouped-hidden defect by grouped-hidden-review.json and grouped-hidden-correction.json. Prior failures remain recorded. Final integration and beta acceptance are still pending. Exact ebcacc1 push confirmed; new implementation not pushed.
