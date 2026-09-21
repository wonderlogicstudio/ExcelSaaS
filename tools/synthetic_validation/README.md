# Synthetic Validation Tooling

This is a separate diagnostic tool for WorkbookCare. It does not edit product code, product fixtures, product tests, configuration, lockfiles, customer data, payment state, deployment state, or AI services.

It generates deterministic synthetic `.xlsx` workbooks, freezes independent ground truth before engine execution, runs the real local `scan_workbook` and `run_formula_audit` entry points in a subprocess per workbook, and writes JSON, CSV, and HTML reports. These entry points are product internals, not HTTP/UI validation.

## Scope

Scored M4 rules are limited to `FORMULA_PATTERN_OUTLIER` and `FORMULA_PATTERN_GAP`. Base static findings are scored only when frozen truth predeclares `FORMULA_REF_ERROR` or `FORMULA_VISIBLE_ERROR_TOKEN`. M4 candidates are reported separately from confirmed errors. Normal exceptions, ambiguous business-policy cells, unsupported structures, summary/manual rows, duplicates, and unjudged findings are not silently counted as passes.

Excel recalculation is `NOT_RUN`. Formula cached values are excluded from claims. Generated-file validation checks formula placement, independent arithmetic invariants, subtotal/closing-balance references, formula reference existence, mutation before/after snapshots, and non-target preservation snapshots.

Current generated families cover ten business domains, but not every requested structure is complete. Missing or partial coverage includes absolute/mixed reference variants, lookup formulas, conditional SUM formulas, Korean sheet names, and monthly sheet-per-period workbooks. Treat those as coverage gaps, not passes.

## PowerShell Commands

Global options come before the subcommand. Use the existing API virtual environment; do not install dependencies:

```powershell
cd C:\Users\JinwonLee\project\ExcelSaaS
.\apps\api\.venv\Scripts\python.exe -m tools.synthetic_validation.cli --python-exe .\apps\api\.venv\Scripts\python.exe generate --mode smoke
```

Generate the full 150-pair/300-workbook dataset without running the engine:

```powershell
.\apps\api\.venv\Scripts\python.exe -m tools.synthetic_validation.cli --python-exe .\apps\api\.venv\Scripts\python.exe --pairs 150 generate --mode full
```

Create a new immutable evaluation run from an existing generated dataset:

```powershell
.\apps\api\.venv\Scripts\python.exe -m tools.synthetic_validation.cli --python-exe .\apps\api\.venv\Scripts\python.exe prepare-eval .\artifacts\synthetic_validation\<source_run_id>
```

Run or resume engine execution for a generated run after review approval:

```powershell
.\apps\api\.venv\Scripts\python.exe -m tools.synthetic_validation.cli --python-exe .\apps\api\.venv\Scripts\python.exe run-engine .\artifacts\synthetic_validation\<run_id>
.\apps\api\.venv\Scripts\python.exe -m tools.synthetic_validation.cli --python-exe .\apps\api\.venv\Scripts\python.exe score .\artifacts\synthetic_validation\<run_id>
```

## Outputs

By default, outputs are written under the current checkout:

`artifacts\synthetic_validation\<run_id>`

Use `--output-root <path>` to place generated workbooks and reports elsewhere.

Key files:

- `dataset/manifest.json`
- `dataset/truth.json`
- `frozen_contract.json`
- `generation_validation.json`
- `engine_status.json`
- `raw_engine/*.json`
- `reports/summary.json`
- `reports/case_results.csv`
- `reports/workbook_results.csv`
- `reports/scope_results.csv`
- `reports/summary.html`

Run IDs include a timestamp and UUID suffix. Previous outputs are not overwritten.
