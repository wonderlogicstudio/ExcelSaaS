# HORIZONTAL-01 grouped hidden correction

Implemented only the approved grouped-hidden column interval correction.

Change summary:
- `formula_patterns.py` now treats hidden `ColumnDimension` entries with serialized `min`/`max` intervals as hidden for every column in the interval.
- The horizontal detector still excludes only runs whose min/max span overlaps hidden columns.
- `test_formula_patterns.py` adds a save/reload `BytesIO` fixture for grouped hidden `C:F` overlapping the `D8:H8` formula run with `F8` drift.
- Visible and outside-group controls remain detected, so the correction is not blanket suppression.

Verification:
- Pre-fix targeted regression failed as expected: `GroupedHidden!F8` was emitted.
- Post-fix targeted pytest passed: 19 passed, 1 existing Starlette deprecation warning.
- Ruff passed after one style-only SIM102 simplification.

Not run: web retest, full regression, native Excel, hosted beta, commit, push.
