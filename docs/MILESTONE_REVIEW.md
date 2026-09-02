# M4 Formula Audit — Final Milestone Review

## Status

`COMPLETED AS LOCAL RELEASE CANDIDATE — HOSTED BETA AND M5 AWAIT APPROVAL`

M4 closes as `m4-formula-audit-rc1`. This is an internal-only, default-off formula-pattern audit, not a hosted or public release and not evidence of real-user or commercial validation.

## What is delivered

- A separate, opt-in `FormulaAuditResult` with only `FORMULA_PATTERN_OUTLIER` and `FORMULA_PATTERN_GAP`.
- A fail-closed server gate for development/internal-beta plus an isolated local launcher.
- Value-free structural evidence, Excel confirmation guidance, explicit limitations, local handling state, and category-only local feedback.
- Settings-based sheet, formula-cell, and candidate limits. A limit returns a named safe skip state, never a partial audit list.
- Regression coverage that preserves the M0–M2.5 Finding list, summary, risk, quote, repairability totals, re-validation, and CSV.
- A reproducible 20-file synthetic M4-C evaluator and an RC verification command.
- Release, failure, hosted-beta-readiness, and manual synthetic-review contracts.

## Final evidence

| Check | Result |
| --- | --- |
| Expected M4-C locations | 72 / 72 |
| Top-level Rule and subtype | 72 / 72 each |
| Unexpected candidates / non-target normal-range candidates | 0 / 0 |
| Normal controls | 0 candidates |
| Scanner failures / file damage / key instability | 0 / 0 / 0 |
| Base-result or privacy-field regressions | 0 / 0 |
| M4-A.5 synthetic quality | 24 TP, 0 FP, 0 FN; precision/recall/F1 1.00 |
| General suite | web 23 tests + production build; API 35 tests + Ruff passed |

The synthetic performance result remains `CONDITIONAL_GO`: at 1k/10k/30k formula cells, the audit/base time ratios were 1.918x / 2.126x / 2.074x. This is an internal-beta operating constraint, not a public performance claim.

## Controlled answer-sheet exception

The immutable additional sample pack labels `배부계산!E13` and `배부계산!F22` as both expected targets and members of normal ranges. The product owner explicitly accepted only this documented source-label conflict through `M4C-2026-09-02-source-label-conflict`. The evaluator accepts it only with `-AcceptProductOwnerFixtureWaiver`; labels and checksums were not edited, and any other failure still blocks. A corrected upstream answer sheet remains desirable.

## Not completed or claimed

- No hosted deployment, public beta, customer workbook processing, user database, analytics, payment, or repair.
- No formula calculation/business-correctness decision, replacement formula, automatic repair, or repaired XLSX.
- No external M3/M3.5 user-validation, payment intent, or market claim.
- No manual desktop/mobile capture: the configured browser runtime was unavailable. The synthetic checklist defines the required capture before hosted beta.

## Before the next approval

1. Complete the hosted-beta deployment, access-control, isolation, retention, logging, and manual visual gates in `docs/33_HOSTED_BETA_READINESS_CHECKLIST.md`.
2. Obtain a corrected checksum-verified source answer sheet when available; retain the current waiver record until then.
3. Resume M3 external testing only after hosted-beta approval. Do not start M5, repair, or payment without separate approval.
