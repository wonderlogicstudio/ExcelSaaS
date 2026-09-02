# M4-D Formula Audit Release Candidate

## Status

`m4-formula-audit-rc1 — local Release Candidate / hosted-beta readiness only`

This is not a public release, hosted service, production accuracy claim, or permission to process customer workbooks. The default site and API keep the formula audit disabled.

## Fixed baseline

| Item | Value |
| --- | --- |
| Scanner version | `0.1.3` |
| Base rule-set version | `2026.09.4` |
| Formula-audit rule-set version | `2026.09.5` |
| RC version | `m4-formula-audit-rc1` |
| M4-C evaluation | 72/72 locations, Rules, and subtypes; no unexpected candidates |
| Approved source-label waiver | `M4C-2026-09-02-source-label-conflict` |

The waiver accepts only two contradictory labels in the immutable synthetic additional pack: `배부계산!E13` within `D6:I13` and `배부계산!F22` within `D22:I29`. It does not alter the source files, checksums, normal-negative results outside those cells, or any other evaluator failure. A corrected upstream pack should replace this waiver later.

## Supported audit surface

| Item | RC support |
| --- | --- |
| Top-level Rule | `FORMULA_PATTERN_OUTLIER`, `FORMULA_PATTERN_GAP` only |
| Evidence subtype | Function, reference-sheet, fixed/relative/absolute reference, range-boundary drift; constant-override and blank-gap candidates when the existing normalizer supports them |
| Comparison | Repeated, supported A1-reference formula regions with sufficient neighbouring evidence |
| Output | Sheet/cell location, value-free pattern summaries and IDs, neighbouring coordinates, limitations, and Excel confirmation guidance |
| Finding key | Stable normalized `rule_code|sheet|cell` identifier; it contains no formula text or cell value |
| Normal exception handling | Summary/manual-labelled rows, boundary rows, merged cells, Tables, dividers, unsupported syntax, and insufficient evidence abstain or skip rather than create a candidate |

Unsupported: formula correctness, calculated values, business logic, SUM/SUMIF/SUMIFS intent, VBA, Power Query, external-link execution, dynamic arrays/unsupported syntax, arbitrary Tables, financial/statistical models, automatic repair, and repaired XLSX output.

## Separation contract

The M4 audit is a second, user-selected request. It must not change base `ScanResult` findings, summary, risk score, complexity, price preview, repairability counts, CSV input, or M2.5 re-validation. It cannot run unless the base scan is complete, untruncated, and the same browser re-sends its selected file.

The server gate remains fail-closed: `FORMULA_PATTERN_AUDIT_ENABLED=true` and `APP_ENV=development|internal_beta` are both required. A browser visibility flag is not access control. `hosted_beta` is intentionally not accepted by the current server gate.

## Controlled local limits

These are `Settings` values, not UI guesses. They apply to the isolated audit only; the base diagnosis remains available when an audit is skipped.

| Setting | Default | RC behaviour |
| --- | ---: | --- |
| `max_upload_mb` | 10 MB | Request rejected before opening workbook |
| `max_uncompressed_mb` | 120 MB | OOXML envelope rejected |
| `max_zip_entries` | 5,000 | OOXML envelope rejected |
| `max_compression_ratio` | 250 | Suspicious ZIP rejected |
| `scan_cell_limit` | 250,000 | `SKIPPED_TRUNCATED` |
| `formula_audit_max_sheet_count` | 200 | `SKIPPED_WORKBOOK_LIMIT` |
| `formula_audit_max_formula_cells` | 30,000 | `SKIPPED_FORMULA_LIMIT` |
| `formula_audit_max_candidate_count` | 120 | `SKIPPED_CANDIDATE_LIMIT`; no partial list is shown |

There is no genuine server-side timeout or memory kill switch in the current synchronous local API. A browser timer must never be presented as a timeout. Process isolation, CPU/memory limits, and a cancellable job model are hosted-beta prerequisites, not implemented RC features.

## User-safe execution states

- `COMPLETED`: candidates may be present or absent; absence is not a correctness guarantee.
- `ABSTAINED_INSUFFICIENT_EVIDENCE`: comparison evidence is insufficient.
- `SKIPPED_TRUNCATED`, `SKIPPED_FORMULA_LIMIT`, `SKIPPED_WORKBOOK_LIMIT`, `SKIPPED_CANDIDATE_LIMIT`, `SKIPPED_UNSUPPORTED_STRUCTURE`: audit was deliberately not completed; no candidate is emitted.
- `FAILED`: safe audit failure; retain base result and never expose stack traces, formula text, or cell values.

The synchronous UI may say only “analyzing”; it must not invent a percentage, remaining time, or cancellation result.
