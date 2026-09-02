# Deployment placeholders

These files prepare for hosting but are deliberately not connected to live accounts.

## Intended beta topology

1. React/Vite static assets on Cloudflare Workers static assets.
2. Cloudflare R2 private bucket for short-lived direct uploads.
3. Cloud Run for isolated Python workbook scans, with min instances set to zero.
4. A small control API and database only when M5 is approved.
5. Payments only after M8, once quote records, idempotency, refunds, and legal pages exist.

## Why deployment is deferred

The starter is for value-proposition and usability testing. Connecting storage, analytics, or payment before users understand and trust the quote would create cost and compliance work without proving demand.

See `docs/14_HOSTING_DEPLOYMENT.md` and `docs/05_SECURITY_PRIVACY.md` before using these examples.
