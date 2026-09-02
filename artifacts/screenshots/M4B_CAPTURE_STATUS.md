# M4-B capture status

Date: 2026-09-01

The configured in-app browser runtime was started for M4-B desktop/mobile capture, but its browser discovery returned an empty list. No screenshot was created and no alternate browser automation was used.

Manual capture prerequisites:

- API: `APP_ENV=internal_beta`, `FORMULA_PATTERN_AUDIT_ENABLED=true`
- Web: `VITE_FORMULA_AUDIT_INTERNAL_BETA_ENABLED=true`
- Use only a synthetic fixture such as `samples/m4-evaluation/detected-patterns.xlsx`
- Check the 1440 px desktop and 390 px mobile layouts after the base scan, then run the optional formula audit.

This is a verification limitation, not a successful capture artifact.
