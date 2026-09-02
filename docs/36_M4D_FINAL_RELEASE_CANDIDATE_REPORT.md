# M4-D Formula Audit — Final Release Candidate Report

## Verdict

`COMPLETED — m4-formula-audit-rc1 (local only)`

M4-D closes the M4 release-candidate/readiness scope. It does not deploy the service or authorize public, hosted, commercial, or customer-file use.

## Fixed baseline

| Item | Value |
| --- | --- |
| Scanner version | `0.1.3` |
| Base rule set | `2026.09.4` |
| Formula-audit rule set | `2026.09.5` |
| Release candidate | `m4-formula-audit-rc1` |
| Source-control baseline | No Git repository is present; versions, synthetic assets, evaluator output, and the waiver ID are the reproducible local baseline |

## Final verification

- `scripts/evaluate_m4c_all.py --accept-product-owner-fixture-waiver`: `PASS_WITH_PRODUCT_OWNER_WAIVER`; 20 files; 72/72 expected locations, Rules, and subtypes; 0 unexpected candidates; 0 non-target normal-range candidates; 0 clean-control candidates; 0 scan failures; 0 key-instability, base-contract, formula, or raw-value exposure failures.
- `scripts/evaluate_formula_patterns.py --performance-runs 3`: 24 TP / 0 FP / 0 FN; precision, recall, and F1 are each 1.00 on the synthetic M4-A.5 corpus. Performance remains `CONDITIONAL_GO` because relative cost is about two times the base scan at the tested 1k/10k/30k formula workloads.
- `scripts/verify.ps1`: frontend Vitest 23 and production build passed; backend pytest 35 and Ruff passed. The non-failing Starlette `TestClient` deprecation warning remains a dependency follow-up.

Run the combined release check with:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\scripts\verify-m4-release.ps1 -AcceptProductOwnerFixtureWaiver
```

The waiver flag is deliberate. Without it, the evaluator fails closed on the two contradictory source labels.

## Answer-sheet exception

The additional synthetic pack calls `배부계산!E13` and `배부계산!F22` both targets and normal-range cells. The product owner accepted the engine result through `M4C-2026-09-02-source-label-conflict`. The evaluator recognizes only those two reviewed conflicts and only after all other gates pass. It never changes the supplied source files or checksums. This is a test-fixture acceptance record, not a claim that conflicting labels are good practice.

## Supported RC surface

- Internal-only, separately requested audit of `FORMULA_PATTERN_OUTLIER` and `FORMULA_PATTERN_GAP`.
- Value-free pattern/evidence differences, comparison positions, Excel verification guidance, limitations, local handling state, and category-only local feedback.
- Default limits: 200 sheets, 30,000 formula cells, and 120 candidates. Limit cases return named skip states with no partial candidate output.
- Default free diagnosis results remain unchanged before, during, and after the audit.

## Safety and release limits

- The server gate accepts only `development` or `internal_beta` with `FORMULA_PATTERN_AUDIT_ENABLED=true`; a browser flag alone is not security.
- M4 neither executes formulas, VBA, Power Query, macros, or external links nor overwrites the workbook.
- No free-text feedback, feedback API, database, telemetry, job cancellation, actual progress percentage, server timeout, memory kill switch, encryption/deletion/retention claim, or hosting implementation was added.
- Desktop/mobile visual capture remains pending because no controllable browser runtime was available. The exact synthetic-only checklist is `docs/35_M4D_MANUAL_RC_CHECKLIST.md`.

## Remaining human gates

Hosted beta requires the deployment controls and an independent synthetic end-to-end rehearsal in `docs/33_HOSTED_BETA_READINESS_CHECKLIST.md`, followed by explicit approval. M3 external validation can resume only then. M4-C's corrected upstream answer sheet should be adopted when available. M5, repair, payments, and public exposure remain out of scope.
