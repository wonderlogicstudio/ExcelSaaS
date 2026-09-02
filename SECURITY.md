# Security policy for the prototype

## Current scope

WorkbookCare is a local product-validation prototype. Do not expose it to untrusted public uploads or use real confidential workbooks until the production upload, retention, abuse-control, and legal milestones are approved and implemented.

## Never commit

- real customer or company workbooks;
- `.env` files or API keys;
- presigned URLs;
- payment secrets;
- logs containing filenames, formulas, cell values, emails, or company identities.

## Workbook execution boundary

The scanner must never execute:

- VBA or embedded binaries;
- formulas or Excel calculation;
- Power Query or external connections;
- user-supplied scripts;
- linked workbook content.

## Reporting a problem

For a private deployment, use the repository owner's private security channel. Do not place sensitive workbook samples in a public issue. Reproduce with a synthetic file whenever possible.

See `docs/05_SECURITY_PRIVACY.md` for the production threat model and controls.
