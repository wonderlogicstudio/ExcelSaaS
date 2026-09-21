# MONTHLY-COPY-01 builder evidence

Scope:
- Changed `apps/web/src/components/OriginalFormulaComparison.tsx` only.
- Display-only exact mapping for the API evidence text:
  `The target formula uses a different monthly sheet-reference pattern from the surrounding M01~M12 subtraction formulas.`
- Korean display text:
  `이 셀은 주변의 M01~M12 월별 시트를 참조하는 뺄셈 수식과 참조 방식이 다릅니다. 의도한 계산인지 확인하세요.`

Behavior:
- Preserves `evidence_summary ?? description` fallback.
- Does not change source API data, detection, approval, formula context loading, or unsupported repair behavior.
- Uses exact-message mapping only; no subtype/category broad mapping.

Commands:
- `npm --prefix apps/web test -- OriginalFormulaComparison`
  - exit 1
  - PowerShell blocked `npm.ps1` by execution policy before tests started.
- `npm.cmd --prefix apps/web test -- OriginalFormulaComparison`
  - exit 1
  - Vite/esbuild startup failed with sandbox `spawn EPERM`; no assertions ran.
- `npm.cmd --prefix apps/web test -- OriginalFormulaComparison`
  - exit 0
  - escalated only after sandbox EPERM
  - result: 1 test file passed, 2 tests passed.

Not run by builder:
- Typecheck/build: intentionally skipped per PL update; root will run hosted-beta build once after review/freeze.
- Full regression, Excel checks, beta verification, deploy, git commit/push: outside this text-only builder scope.
