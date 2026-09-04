# Hosted Beta H1 — Environment and Secret Contract

## Configuration ownership

Public browser configuration contains only product environment, same-origin API path, and non-security UI visibility. API configuration contains limits and exact CORS origins. Provider credentials are never committed: Cloudflare secrets belong in the Worker secret store; Google Cloud credentials belong in IAM and Secret Manager.

| Setting | Owner | H1 rule |
| --- | --- | --- |
| `VITE_PRODUCT_ENV` | frontend build | informational only; never authorization |
| `VITE_API_BASE_URL=/api` | frontend build | same-origin control plane, never Cloud Run origin |
| `APP_ENV=hosted_beta` | Cloud Run service | enables strict HTTPS CORS validation; does not enable M4 audit |
| `CORS_ORIGINS` | Cloud Run service | one or more exact HTTPS beta origins, no wildcard/local origin |
| scanner limits | Cloud Run service | retain RC defaults unless separately approved |
| Cloudflare API/R2 credentials | Worker secret store | no source, build log, browser, or Cloud Run injection unless a later design requires it |
| Google service identity | Cloud Run IAM | workload identity/service account, not a checked-in key file |
| optional HMAC secret | both secret stores | only if H2 approves a tested, timestamped, signed control-plane protocol |

## Required separation

- One bucket, secret namespace, service account, log sink, and Access application per hosted-beta environment.
- Development credentials cannot read hosted-beta objects. Hosted-beta credentials cannot deploy production.
- Worker configuration must never contain a Cloud Run IAM key, R2 listing privilege for browsers, or a database connection string.
- Formulas, cell values, filenames, sheet names, locations, object URLs, emails, company names, and free text are forbidden in logs and metrics.

## Build configuration

`apps/web/hosted-beta.env.example` is copied to an untracked `.env.hosted_beta` only for an approved build. `apps/api/.dockerignore` keeps local environments, tests, workbooks, logs, and generated packaging data out of the API image build context. `apps/api/Dockerfile` runs as an unprivileged user and uses only its container-local temporary directory.

## Explicit non-claims

H1 does not prove encryption, Korean data residency, deletion duration, access control, zero retention, or cloud-provider compliance. No hosted user file is accepted in H1, so these are deployment prerequisites rather than current product claims.
