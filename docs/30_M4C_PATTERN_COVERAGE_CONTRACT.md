# M4-C Formula Pattern Coverage Contract

## Status

`IMPLEMENTED — EXECUTION-PATH RECOVERY VERIFIED — READY FOR HUMAN REVIEW — STOP`

M4-C extends the existing internal-only formula-pattern audit against the supplied synthetic practical corpus. It does not add a rule code, calculation engine, automatic repair, workbook write path, or public product feature.

The base scan remains scanner/rule-set `0.1.3` / `2026.09.4`. The isolated audit returns its own rule-set `2026.09.5` so a base-only M2.5 re-validation is not invalidated by an M4-only parser expansion.

## Acceptance corpus

- Source: supplied `WorkbookCare_M4C_Sample_Pack_2026-09-01` synthetic pack.
- Repository copy: `samples/m4c-evaluation/`.
- Labels: `manifest.json` contains 36 target candidates and 36 normal exceptions across nine mixed business-style workbooks and one clean-control workbook.
- Pass condition: candidate `(sheet, cell, rule_code, evidence subtype)` set exactly matches the 36 target labels; no candidate may fall outside that set or in a labelled normal-exception range.

The target is **not** “36 or more.” Extra findings are potential false positives and fail the gate until manually reviewed.

## Supplemental synthetic-pack validation

The separately supplied `WorkbookCare_M4C_Additional_Pack_2026-09-01` is a checksum-verified, synthetic-only validation input, not a production fixture or a reason to add a rule code. It contains 36 additional target labels, 36 normal-exception labels, and a 4-target Holdout workbook.

The M4-C remediation corrected a defect where summary markers inside a formula's referenced sheet name caused the formula's entire data row to be excluded. With the fix, the additional pack returns its exact 36 target keys, including 4/4 Holdout targets, with no extra candidate. Combined with the original supplied pack, this is 72/72 exact target keys and no unexpected candidate.

Two additional-pack normal ranges conflict with its own expected targets: `배부계산!E13` lies within `D6:I13`, and `배부계산!F22` lies within `D22:I29`. Candidates at those two cells are expected targets, not product false positives. The source fixture must be corrected before it can be added as a strict normal-exception regression gate; all non-conflicting normal labels produced no candidate.

## Permitted implementation

The existing rule codes remain the only possible output:

- `FORMULA_PATTERN_OUTLIER`
- `FORMULA_PATTERN_GAP`

The formula normalizer may accept numeric, text, logical, and error operands as value-free token categories in supported expression contexts. It must not retain, log, return, or display the literal values. Direct static operands to `SUM` or `AVERAGE`, external workbooks, names, structured/Table references, arrays, unsupported syntax, summary rows, merged cells, and Excel Table cells remain outside the comparison surface.

`RANGE_BOUNDARY_DRIFT` may be emitted only when a changed reference is itself a range. A changed single-cell reference in a formula that also contains an unchanged range remains `RELATIVE_REFERENCE_DRIFT`.

## Non-negotiable boundaries

- Formula candidates remain separate from the basic `ScanResult`; base findings, summary, risk, quote, repair counts, CSV, and default Results must remain unchanged.
- The server feature flag remains default-off and must still require a development/internal-beta environment.
- This is static inspection only: no formula/VBA/external-link execution, no cached-value interpretation, and no workbook save or modification.
- Candidate copy remains indeterminate: a pattern difference is not a confirmed error, business verdict, replacement formula, or repair instruction.
- All validation assets remain synthetic.

## Internal-beta execution procedure

The normal free scan and the M4 audit are intentionally different requests. In the supplied pack, scenario 03 has 49 free-scan findings from earlier M0–M2 static rules, while its separate M4 audit has four formula-pattern candidates. A free-scan count is never an M4-C result.

1. Start the local stack with `./scripts/dev.ps1 -InternalFormulaAudit`. It selects an available isolated API/web pair from `8010–8090` / `5174–5190` and does not depend on an older default stack at `8000` / `5173` being stopped.
2. Open the `Web:` address printed by that command (not the default `5173` address).
3. Upload one supplied synthetic workbook, wait for the free scan, then use the **separate** formula-pattern audit panel now shown before the free Finding list.
4. Use `./scripts/verify-m4c-sample-pack.ps1` for a non-UI exact-pack check. It must report M4 counts `4, 4, 4, 4, 4, 4, 4, 4, 4, 0` and 36 exact candidates in total.

The launcher is intentionally isolated: an earlier default-mode API/browser can remain on standard ports without being mistaken for the internal beta. It tests actual socket binding and chooses a free beta pair; if its configured ranges are exhausted, it exits before starting another beta stack.

## Required verification

1. Exact M4-C target/normal corpus regression.
2. Existing M4-A.5 target, normal-exception, unsupported, truncated, evidence, privacy, stability, and performance evaluation.
3. Basic-scan invariance before/after optional audit and no M4 candidate in base findings.
4. API endpoint integration against the supplied pack, backend unit tests/Ruff, and complete `scripts/verify.ps1` web/API check.
5. Record timing and limitations without claiming production accuracy.
