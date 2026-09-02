# M4-D Manual Release Candidate Checklist

Use synthetic fixtures only. Do not capture, upload, or record a real company workbook.

## Required local setup

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\scripts\dev.ps1 -InternalFormulaAudit
```

Use the isolated `Web:` URL printed by the launcher. Do not use a stale default `5173` browser tab.

## Viewports and captures

- Desktop: 1440 × 900, browser zoom 100%.
- Mobile: 390 × 844, browser zoom 100%.
- Save synthetic-only captures as `artifacts/screenshots/m4-rc-desktop.png` and `artifacts/screenshots/m4-rc-mobile.png` when a controllable browser is available.
- Record the browser/version, local URL, date, and fixture name beside the captures; do not include browser profile information.

## Checklist

- [ ] Default feature flags: public/default page has no formula-audit entry point or request.
- [ ] Internal flags: after a base upload, the separate formula-audit panel appears before the long base Finding list.
- [ ] Candidate case: use a synthetic M4-C workbook; verify location, rule, evidence summary, comparison coordinates, normal-case text, Excel confirmation method, limitation, local handling state, and category-only feedback buttons.
- [ ] No-candidate control: use `10_경영대시보드_정상패턴.xlsx` or `20_다중사업부_정상통제.xlsx`; confirm the no-candidate message does not guarantee correctness.
- [ ] Truncated, unsupported, workbook-limit, formula-limit, and candidate-limit cases: confirm the matching safe state, no candidate list, and unchanged base result.
- [ ] Feedback: no memo/free-text input appears; category selection remains local and clearable.
- [ ] Separation: M4 candidates do not appear in base Findings, risk score, quote, repairability totals, re-validation, or CSV.
- [ ] Error state: use a synthetic invalid input only; no stack trace, formula, cell value, or filename appears.
- [ ] Accessibility: keyboard reaches the audit action, details, handling selector, feedback buttons, and clear action with visible focus.

Browser capture is a manual release check. If this environment lacks a controllable browser, mark the capture as pending; do not invent a successful visual result.
