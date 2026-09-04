# Hosted Beta H1 — Deployment Foundation & Security Boundary

## Status and boundary

`COMPLETED — local deployment foundation only; no cloud resource or user upload was created`

H1 prepares a restricted hosted-beta deployment. It is not a public launch, an invitation to upload company files, an M3 session, or a production release. M4 scanner rules, M4 exposure, base Results, risk score, quote, CSV, and repair boundaries remain unchanged.

## H1 architecture decision

```text
Browser
  -> Cloudflare Access-protected beta hostname
  -> Cloudflare Worker control plane (/api)
  -> private R2 temporary object
  -> authenticated Cloud Run API
  -> value-free result
  -> deletion attempt + lifecycle backstop
```

The browser must use the same-origin `/api` control-plane route. It must not receive or call a Cloud Run origin URL. Cloud Run is deployed without an anonymous invoker; H2 must prove a Worker-to-Cloud-Run authenticated invoker path before any beta traffic is enabled. A hidden browser button, an origin URL, a Worker route by itself, or a Cloudflare Access policy applied only to the frontend is not an access-control boundary.

## Environment isolation

| Environment | Purpose | Files, secrets, logs, and credentials |
| --- | --- | --- |
| `local` / `development` | local coding and synthetic checks | local only; never accesses beta storage |
| `internal_beta` | local M4 review | synthetic files only; M4 gate may be enabled |
| `hosted_beta` | future invite-only deployment | separate Cloudflare zone/access app, R2 bucket, Cloud Run service account, secrets, and logs |
| `production` | future public product | separate from all above; not created by H1 |

`hosted_beta` and `production` require exact HTTPS CORS origins. Wildcards, localhost, and `hosted_beta_live`-style undeclared environments fail configuration validation. Formula audit remains unavailable in `hosted_beta` until the complete access chain is independently verified.

## H1 implementation delivered

- Non-root API container with an owned, private container temporary directory and Docker liveness check.
- Content-free `/health/live` and versioned `/health/ready` endpoints. They expose no paths, secrets, workbook details, or credentials.
- Strict application-environment and CORS contract.
- A code-level structured-observability allowlist. It rejects filenames, sheet names, cells, formulas, values, object URLs, identities, and free text.
- Safe generic API error response without exception details.
- Same-origin hosted-beta frontend example and a non-public Cloud Run deployment example.

## H1 intentionally does not implement

- Cloudflare Worker, Cloudflare Access application, R2 bucket, Google Cloud project, Artifact Registry, Cloud Run service, Secret Manager secret, domain, or DNS record.
- Upload sessions, presigned URLs, R2 object transfer, deletion worker, result database, rate limiter, account, analytics, feedback API, or persistent scan ID.
- `hosted_beta` formula-audit exposure, automatic repair, repaired XLSX, payment, M3/M3.5 testing, M5, AI, VBA, Power Query, or public release.

## H2 prerequisite gates

1. Product owner approves the beta audience and file policy.
2. Cloudflare Access protects the beta hostname and Worker routes.
3. Cloud Run receives only an authenticated control-plane invocation; direct browser/API-origin bypass is rejected.
4. R2 is private, uses opaque keys, has narrow upload permissions and CORS, and has a tested deletion/lifecycle path.
5. The Cloud Run container has an enforced request timeout, CPU/memory/instance/concurrency limits, and a verified failure-cleanup path.
6. Synthetic end-to-end deployment rehearsal, desktop/mobile visual review, and explicit approval pass before any invitation.

## Completion update — 2026-09-04

`COMPLETED — local deployment foundation only; H2 awaits separate product-owner approval.`

- Local container build completed: `docker build -t workbookcare-api:h1 -f apps/api/Dockerfile apps/api`.
- The container ran as the non-root `app` account and returned safe fields only from `/health/live` and `/health/ready` on `127.0.0.1:8080`.
- `scripts/verify.ps1` passed: web 23 tests plus production build; API 50 tests plus Ruff; supplied M4-C pack 36 exact candidates with no extras.
- `scripts/verify-m4-release.ps1 -AcceptProductOwnerFixtureWaiver` exited successfully: M4-C 72/72 locations and top-level rules under the documented narrow waiver; M4-A.5 remained `CONDITIONAL_GO` with synthetic precision/recall 1.0.

No Cloudflare, R2, Google Cloud, Cloud Run, Artifact Registry, domain, DNS, credential, user invitation, or real workbook was created or used in H1. H2 remains awaiting separate product-owner approval.
