# M4-C Formula Audit — Final Validation Report

## Verdict

`COMPLETED WITH PRODUCT OWNER FIXTURE WAIVER — 2026-09-02`

The M4-C formula-audit engine satisfies the measured synthetic-engine and base-result regression checks below. The immutable additional-pack labels still contain two contradictions. The product owner explicitly accepted the narrow waiver `M4C-2026-09-02-source-label-conflict`: it applies only to those two source-label overlaps and only if every other gate passes. Source labels and checksums were not changed.

M4-D follows this release-candidate baseline; it does not turn the source defect into a general evaluator exception.

## Scope and baseline

- Evaluation date: 2026-09-01 (UTC timestamp is stored in the ignored evaluation artifact).
- Git: this workspace is not a Git repository; no commit hash, local commit, or tag can be created.
- Scanner version: `0.1.3`.
- Base rule-set version: `2026.09.4`.
- Isolated formula-audit rule-set version: `2026.09.5`.
- Default formula-audit flag: disabled and unavailable in the default environment.
- Internal-beta formula-audit flag: enabled and available only in the evaluator's internal setting.

The audit remains separate from the base free diagnosis. It is static only, default-off, internal-only, opt-in, absent from the public/default UI, excluded from base risk and beta-price calculations, and does not create a repair, replacement formula, or workbook output.

## Inputs

The evaluator read the two checksum-verified, synthetic-only source packs without modifying them:

1. `samples/WorkbookCare_M4C_Sample_Pack_2026-09-01/WorkbookCare_M4C_Sample_Pack`
2. `samples/WorkbookCare_M4C_Additional_Pack_2026-09-01/WorkbookCare_M4C_Additional_Pack`

Together they contain 20 workbooks, 72 expected candidate labels, 72 normal-exception labels, and two normal-control workbooks:

- `10_경영대시보드_정상패턴.xlsx`
- `20_다중사업부_정상통제.xlsx`

The evaluator verifies every supplied checksum before and after evaluation. Both checks passed, so it found no changed input or file-integrity failure.

## Final measured result

| Check | Result |
| --- | ---: |
| Expected locations detected | 72 / 72 |
| Top-level Rule match | 72 / 72 |
| Subtype match | 72 / 72 |
| Location false negatives | 0 |
| Top-level Rule false negatives | 0 |
| Unexpected candidates | 0 |
| Labelled normal-exception false positives, excluding contradictory target cells | 0 |
| Normal-control M4 candidates | 0 / 2 files |
| Audit scan failures | 0 |
| Finding-key instabilities across repeated audit | 0 |
| Base-result regressions | 0 |
| Formula-text exposure in audit artifact | 0 |
| Raw cell-value/formula fields in audit artifact | 0 |
| End-to-end evaluator time | 6.431 s |

Only the existing, internal-beta-approved top-level rules appeared:

- `FORMULA_PATTERN_OUTLIER`
- `FORMULA_PATTERN_GAP`

`GENERIC_PATTERN_DRIFT`, unsupported syntax, calculation/business verdicts, and new rule codes remain withheld.

## Blocking source-label conflict

The additional source pack contains the following two expected targets inside ranges which that same source labels as normal exceptions:

| Expected target | Conflicting normal range |
| --- | --- |
| `배부계산!E13` | `배부계산!D6:I13` |
| `배부계산!F22` | `배부계산!D22:I29` |

The engine correctly emits candidates at both expected target locations. Counting either candidate as a false positive would contradict the expected-target label; excluding it without recording the overlap would hide a defective test contract. The evaluator therefore fails closed with `source manifest has 2 target/normal label conflicts`.

Recommended follow-up: obtain a corrected, checksum-verified additional source pack (manifest and matching CSV labels) from the fixture owner. Do not edit the currently copied source labels or checksums in this repository. Until that occurs, the explicit waiver command below is required; any additional conflict or any other failed gate still exits non-zero.

## Regression and safety verification

`scripts/verify.ps1` completed its web verification:

- Frontend Vitest: 23 passed.
- TypeScript/Vite production build: passed.

The API and original supplied-pack checks were also rerun directly:

- Backend pytest: 34 passed.
- Ruff: passed.
- Original 10-file M4-C pack: 36 exact audit candidates, no extras.
- Existing warning: Starlette `TestClient` / `httpx` deprecation warning only; no test failure.

The integrated evaluator compares the base `ScanResult` before the audit, with the audit flag present, and after the audit. It verifies unchanged base workbook summary, findings, risk, quote, limitation, and CSV-input contracts. It also confirms M4 candidates never enter base findings. M2.5 re-validation and the existing category-only feedback tests are included in the 23 frontend tests.

## Reproducible commands

From the project root in PowerShell:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\scripts\verify.ps1
.\scripts\verify-m4c.ps1 -AcceptProductOwnerFixtureWaiver
```

Without its explicit waiver switch, `verify-m4c.ps1` still exits with an error by design. With the switch, it accepts only the documented two conflicts after writing:

- `artifacts/m4c-final/evaluation.json`
- `artifacts/m4c-final/evaluation.csv`

These ignored artifacts retain synthetic file/sheet/cell test locations only. They do not retain formula text or cell values.

## Files added or updated for final validation

- `.gitignore` — ignores `artifacts/m4c-final/`.
- `scripts/evaluate_m4c_all.py` — checksum-aware, two-pack final evaluator.
- `scripts/verify-m4c.ps1` — reproducible PowerShell entry point that fails closed when the final gate is blocked.
- `samples/WorkbookCare_M4C_Additional_Pack_2026-09-01/WorkbookCare_M4C_Additional_Pack/` — immutable repository copy of the supplied synthetic additional pack and its checksums.
- `docs/08_ROADMAP.md`, `docs/09_CURRENT_MILESTONE.md`, `docs/10_PROGRESS.md`, `docs/11_DECISIONS.md`, `docs/23_FORMULA_PATTERN_AUDIT.md`, and `docs/MILESTONE_REVIEW.md` — status and decision records.
- This report.

The formula-summary-marker remediation itself remains covered by `apps/api/app/formula_patterns.py` and `apps/api/tests/test_formula_patterns.py`; it was not expanded into a new detection rule in this final-validation step.

## Current support and limits

Supported output is limited to static pattern candidates with value-free evidence and Excel confirmation guidance. It does not prove a formula is wrong, calculate a workbook, check business rules, execute VBA or external links, compare real company files, recommend a correction, or modify/save a workbook.

Passing this synthetic corpus is a meaningful regression gate for the current two-rule engine, not an accuracy claim for production files. Further testing with approved non-identifying real-world cases remains necessary after the separately approved hosting/privacy work.

## Closure criteria

M4-C closure required 72/72 locations and top-level Rules, zero false negatives, zero non-target normal-exception false positives, zero normal-control candidates, and a passing `scripts/verify.ps1`. These conditions passed. The remaining source-label contradiction is recorded through the product-owner waiver, not erased.

M4-D, hosting, payments, automatic repair, and new detection rules remain separately controlled scopes.
