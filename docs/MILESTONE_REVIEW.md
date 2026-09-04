# Hosted Beta H1 — Final Milestone Review

## Status

`COMPLETED AS LOCAL DEPLOYMENT FOUNDATION — H2 AWAITS PRODUCT OWNER APPROVAL`

H1 closes the deployment foundation and security boundary only. It does not close hosted beta, user validation, commercial validation, repair, or public release.

## Evidence

| Gate | Result |
| --- | --- |
| API Docker image build | Passed |
| Non-root container runtime | Passed (`app` user) |
| Liveness/readiness contracts | Passed; content-free safe fields only |
| Hosted config/CORS tests | Passed; unsafe hosted configuration fails closed |
| Standard verification | Passed: web 23 tests/build, API 50 tests/Ruff, supplied M4-C pack 36 exact candidates/no extras |
| M4 RC verification | Passed with existing product-owner fixture waiver; 72/72 locations and rules |

## What is now ready

- A non-root Cloud Run-compatible API image and safe health endpoints.
- Same-origin `/api` frontend contract; browser-to-Cloud-Run direct access is prohibited by design.
- Environment and secret ownership rules, safe logging/error contract, file-lifecycle requirements, and H2 deployment/rollback runbook.
- Preserved M4 RC boundaries: default-off/internal-only Formula Audit, isolated findings, no risk/quote/CSV change, no repair.

## Not completed or claimed

- No Cloudflare Access/Worker/R2/Cloud Run/Google Cloud deployment or credential.
- No real file flow, temporary object deletion proof, access-control proof, direct-origin-bypass test, rate limit, or budget alert.
- No user invitation, M3/M3.5 external test, M5, automatic repair, payment, account, database, analytics, AI, VBA, or Power Query.

## Before H2

The product owner must separately approve the beta audience and file policy. A human operator must then create isolated cloud resources, prove the authenticated Worker-to-Cloud-Run path and private R2 lifecycle using synthetic files, complete desktop/mobile checks, and approve any invitation. Do not begin H2 automatically.
