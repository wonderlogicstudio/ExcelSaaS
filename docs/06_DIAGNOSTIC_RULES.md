# Diagnostic rules

## Rule-system requirements

Every rule must be deterministic, versioned, testable, and independently explainable. A finding is not merely text; it is a record with evidence and repair classification.

Required fields:

- `rule_code`
- `rule_version`
- `severity`
- `title_key`
- `description_key`
- `sheet`
- `cell_or_range`
- `confidence`
- `repair_class`
- `evidence_metadata`
- `false_positive_notes`

For the M2.5 Extension, scanner findings also receive a stable, value-free `finding_key`. It combines the rule code and normalized location only; it is used only for same-session re-validation comparison and is not a workbook version fingerprint.

## Repair classes

| Class | Meaning |
|---|---|
| `SAFE_CANDIDATE` | A deterministic replacement can be previewed and reversed, but still requires user approval |
| `CONFIRMATION_REQUIRED` | Technically automatable but business intent is ambiguous |
| `EXPERT_REVIEW` | Logic, fidelity, macros, external systems, or low confidence make automatic repair inappropriate |
| `INFORMATION_ONLY` | Useful risk or maintenance information with no automatic action |

## Current M2 static rules

### File and structure

| Code | Default severity | Detection | Repair class |
|---|---|---|---|
| `FILE_MACRO_ENABLED` | warning | `vbaProject.bin` or `.xlsm` | `EXPERT_REVIEW` |
| `FILE_DRAWING_PARTS` | info | drawings, charts, shapes, media parts detected | `EXPERT_REVIEW` for rewrite |
| `SHEET_HIDDEN` | info | hidden worksheet | `CONFIRMATION_REQUIRED` |
| `SHEET_VERY_HIDDEN` | warning | `veryHidden` worksheet | `CONFIRMATION_REQUIRED` |
| `MERGED_CELL_HEAVY` | info | merged-range count exceeds threshold | `INFORMATION_ONLY` |
| `DEFINED_NAME_BROKEN_REF` | critical | defined name contains `#REF!` | `EXPERT_REVIEW` |

### Formulas

| Code | Default severity | Detection | Repair class |
|---|---|---|---|
| `FORMULA_REF_ERROR` | critical | formula text contains `#REF!` | `EXPERT_REVIEW` unless deterministic neighbor pattern exists |
| `FORMULA_VISIBLE_ERROR_TOKEN` | critical | error token embedded in formula | `EXPERT_REVIEW` |
| `FORMULA_VOLATILE` | info | volatile function used | `INFORMATION_ONLY` |
| `FORMULA_DEEP_NESTING` | warning | nested `IF` count above threshold | `INFORMATION_ONLY` |
| `FORMULA_WHOLE_COLUMN_REFERENCE` | info | formula references entire column(s) | `INFORMATION_ONLY` |
| `FORMULA_EXTERNAL_REFERENCE` | warning | formula contains workbook-qualified reference | `CONFIRMATION_REQUIRED` |

### Data quality

| Code | Default severity | Detection | Repair class |
|---|---|---|---|
| `NUMBER_STORED_AS_TEXT` | warning | numeric-looking string in a numeric peer region | `SAFE_CANDIDATE` when locale is unambiguous |

### Performance and maintainability

| Code | Default severity | Detection | Repair class |
|---|---|---|---|
| `FORMULA_COUNT_HIGH` | info | count threshold exceeded | `INFORMATION_ONLY` |
| `SCAN_CELL_LIMIT_REACHED` | warning | configured safe cell limit reached | `INFORMATION_ONLY` |

## Future formula-pattern rules — not implemented

The following names describe possible M4 formula-pattern checks. They are not detected, counted, recommended as findings, or classified by the current M2 scanner.

| Future code | Intended future signal | Preconditions before implementation |
|---|---|---|
| `FORMULA_PATTERN_DRIFT` | formula differs from a stable surrounding row/column pattern | synthetic corpus, false-positive review, explicit evidence grade and repair-class approval |
| `FORMULA_HARDCODED_OVERRIDE` | a constant may replace translated peer formulas | same quality gates plus a clear business-intent confirmation path |

## Risk score

Risk score is a rules-based prioritization aid, not a probability of financial loss, an Excel calculation result, or a measure of business correctness. The user-facing labels are `낮음`, `보통`, and `높음`; a critical band is shown as `높음 · 우선 확인 필요`.

Suggested weights:

- Critical: 16 points each, capped at 48.
- Warning: 6 points each, capped at 36.
- Info: 1 point each, capped at 10.
- Macro flag: 6 additional points.
- External-reference count: 2 points each, capped at 6.
- `scan_truncated`: 4 additional points.
- Final score capped at 100.

Bands:

- `0–19`: Low.
- `20–44`: Moderate.
- `45–69`: High.
- `70–100`: Critical.

The UI must say `규칙 기반 우선순위 점수` next to a number and explain that the score measures detected structural risk, not business correctness. The calculation and its empirical limits are documented in `docs/20_SERVICE_SCOPE.md`.

## Complexity score

Complexity estimates delivery risk and price tier.

Inputs:

- File size bucket.
- Worksheet count.
- Formula count and diversity.
- External references.
- Macros.
- drawings/charts/shapes.
- named ranges.
- merged cells.
- detected critical/warning findings.
- candidate repairs.
- fidelity risk.

Bands:

- `0–3`: Basic.
- `4–7`: Standard.
- `8–11`: Advanced.
- `12+`: Expert review.

Complexity is not shown as an arbitrary secret number; the quote UI shows the actual factors.

## Current scanner limitations

- Static analysis does not execute Excel's calculation engine.
- Cached values can be stale.
- Business-logic mistakes can exist without formula syntax anomalies.
- Formula-pattern drift and hardcoded-override analysis are not implemented. They are planned for M4, not part of M2.5.
- Locale-specific number/date interpretation is intentionally conservative.
- Existing workbook objects are not rewritten.

## M2.5 Extension result guidance

`scanner.py` remains responsible only for objective facts, location, rule code, severity, existing confidence, repair class, and the value-free finding key. `recommendation_engine.py` maps every current rule code to deterministic result guidance:

- Action Category (`FIX_RECOMMENDED`, `USER_CONFIRMATION`, `DEEP_VALIDATION_REQUIRED`, `INFO_ONLY`)
- detection-basis grade
- Excel manual check steps
- normal-condition and action-recommended conditions
- recommended next action and static-check limitations

Action Category never changes a finding, severity, rule count, risk score, or price. `FIX_RECOMMENDED` is used only for the existing unambiguous numeric-text candidate class; uncertain rule results are not upgraded to a repair claim.

Result-level `scanner_version`, `rule_set_version`, and `scanned_at` make same-session comparison transparent. A version mismatch or a truncated scan must be surfaced as a comparison limitation.

## Rule quality gates

Before enabling a new rule in production:

1. Unit tests for positive and negative cases.
2. At least 20 synthetic workbooks.
3. False-positive review by an Excel expert.
4. Severity and repair-class approval.
5. Plain-language copy review.
6. Telemetry plan without workbook contents.
7. Rule-set version increment.
