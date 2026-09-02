# Test plan

## Test layers

### Frontend unit/component

- Primary copy and CTA render.
- Demo flow reaches diagnosis.
- API success maps to result UI.
- API failure shows a safe error and sample fallback.
- Unsupported extension is rejected before upload.
- Keyboard activation of upload controls.
- Quote button is visibly disabled in prototype.

### Backend unit

- ZIP path traversal rejection.
- Decompressed size limit.
- Entry-count limit.
- Missing OOXML core parts rejection.
- Sheet/hidden/merged/formula counts.
- Formula error-token detection.
- Volatile-function detection.
- Macro and external-link flags.
- Stable risk and quote outputs.

### Contract

- Frontend response types match API schema.
- Error payloads have stable codes.
- Scanner version and rule-set version are present.

### Integration

- Synthetic workbook upload from browser to API.
- Progress, result, findings, and quote display.
- API unavailable path.
- Large-but-allowed workbook.

### Visual/manual

- 1440 px desktop.
- 1024 px laptop.
- 768 px tablet.
- 390 px mobile.
- Light mode.
- Keyboard-only navigation.
- Reduced-motion preference.

### Security

- Renamed non-ZIP file with `.xlsx` extension.
- ZIP bomb fixture using safe synthetic metadata.
- Excessive ZIP entries.
- `../` and absolute ZIP paths.
- `.xls` rejection.
- Password/encrypted package rejection or safe failure.
- Macro-containing workbook detected but not executed.
- External links detected without network access.
- No workbook content in logs.

## Synthetic workbook corpus

Build fixtures for:

1. Clean basic workbook.
2. `#REF!` formula.
3. External workbook formula.
4. Hidden and very-hidden sheets.
5. Macro-enabled workbook metadata.
6. Many merged ranges.
7. Volatile formulas.
8. Deep nested `IF`.
9. Whole-column formulas.
10. Numbers stored as text.
11. Workbook with charts/drawings.
12. Large sheet near configured scan-cell limit.
13. Broken defined name.
14. Unsupported/corrupted OOXML.

Never commit real customer files.

## Release checklist

- All automated tests pass.
- Dependency vulnerability review performed.
- No secrets in repository/history.
- CORS/rate limits verified.
- File-retention job verified in non-production.
- Privacy and limitation copy matches implementation.
- Unsupported files route safely.
- Output opens in supported Excel versions when repair is enabled.
- Re-scan verifies every repaired output.
