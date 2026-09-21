# MONTHLY-01 implementation report

Scope implemented: conservative candidate-only monthly sheet reference drift detection for same-row binary subtraction formulas under explicit M01..M12-style headers. The detector requires a unique header within four rows, existing month sheet correspondence, contiguous support, a unique dominant pattern with at least three neighbors, exactly one interior deviation, and matching immediate left/right dominant cells. It does not add repair eligibility or global sheet-name normalization.

Acceptance mapping:
- Positive oracle: Budget!N18 `=N15-N14` under M10 header is detected as `FORMULA_PATTERN_OUTLIER` / `REFERENCE_SHEET_DRIFT`; comparison locations prioritize `M18`, `O18`.
- Equivalent local normal: `=N16-N15` resolves one hop through local month-link cells and produces no candidate.
- Frozen historical normal/mutant truth remains unchanged in old artifacts; root reports native new2 plus reused controls verified separately.
- Negatives covered by tests: missing/duplicate/reversed headers, missing sheet, three-formula run, multiple deviations, edge deviation, left/right mismatch, hidden group/header, Table, merged cell, summary/manual row, function/range/anchor/external/name/mixed-month operands, blank and constant target.
- Existing vertical and HORIZONTAL-01 paths are reused and dedup remains by rule/cell key.

Changed files:
- apps/api/app/formula_patterns.py
- apps/api/tests/test_formula_patterns.py
- apps/web/src/components/FormulaAuditPanel.tsx
- apps/web/src/components/FormulaAuditPanel.test.tsx
- apps/web/src/components/UnifiedDiagnosis.test.tsx

Executed checks are recorded in `command-log.json`. Final passing checks: monthly pytest 4 passed; targeted API pytest 23 passed; Ruff passed; changed web tests 8 passed; web build/typecheck passed.

Not run here: full regression, native Excel/browser beta verification, deployment, commit, push. Root owns those integration gates after review.


## Focused review correction

Correction applied after CHANGES_REQUIRED:
- Restored Korean UI/API copy in `FormulaAuditPanel.tsx` and monthly candidate title/description.
- Added independent UI test literals for the limited M01~M12 simple subtraction scope, zero-result phrase, unsupported monthly-scope copy, and the wording that function/range/anchored/external/name references are unsupported only for this horizontal-arithmetic/monthly comparison path.
- Restricted monthly detection so the dominant pattern must be a fully resolved `MONTHLY_SUB(...)` signature. Unresolved-local-majority and fixed-other-month-majority cases now yield zero candidates.
- Excluded cases where the outlier is also a fully resolved `MONTHLY_SUB(...)` with different A1 addresses, keeping correct-month address drift out of scope.
- Reworked MissingSheet to use a separate workbook with a valid M10 header and no real M10 sheet, and changed the 3-formula fixture to an actual interior F18 drift in E:G.

Final correction checks: monthly pytest 5 passed; targeted API pytest 24 passed; Ruff passed; changed UI tests 8 passed; web build/typecheck passed. Full regression, beta deployment/screen verification, Git commit and push remain with root.


## Copy semantics wording correction

A wording-only correction scoped the unsupported grammar copy to this horizontal-arithmetic/monthly comparison path, so it no longer reads as a global exclusion of vertical formula patterns that already support functions/ranges/anchors/sheet references. No API logic or checks were rerun in this step; root owns the next full verify/web validation.
