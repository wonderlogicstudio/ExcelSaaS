# Hosting and deployment plan

> **Current H2 update — 2026-09-09:** H2 is approved and synthetic-only. The
> existing IAM-required Cloud Run service remains in Seoul (`asia-northeast3`).
> The owner approved a private API Gateway bridge in Tokyo (`asia-northeast1`),
> because API Gateway has no Seoul location. Do not claim Korea-only data
> residency, invite users, or upload real workbooks until H2's complete
> positive/negative/deletion checks pass.

> **2026-09-09: API Cloud Run preparation completed locally; deployment stopped.**
> The current approved step does not execute the broader deployment sequence below.
> Exact verified build/run commands, the future private image-digest deployment,
> required environment, and residual risks: [`43_CLOUD_RUN_PREPARATION.md`](43_CLOUD_RUN_PREPARATION.md).


## Local phase

- React dev server on port 5173.
- FastAPI on port 8000.
- Direct multipart upload only for local/testing.
- No cloud account required.

## Public prototype phase

Use only synthetic/sample data until privacy and retention controls are implemented.

- Frontend: Cloudflare Workers Assets or Pages.
- API: Cloud Run service.
- Real customer upload disabled or clearly restricted.

## Production beta target

### Cloudflare

- Domain and DNS.
- Workers Assets for frontend.
- Small Worker control API.
- Private R2 bucket.
- Short-lived presigned upload/download URLs.
- Lifecycle/deletion process.
- WAF/rate limiting when needed.

### Google Cloud

- Cloud Run service for short analysis requests.
- Cloud Run Jobs for repair or long analysis.
- Artifact Registry for containers.
- Secret Manager for production secrets.
- Budget alerts and maximum-instance caps.
- Region selected based on Korean-user latency and data-policy review.

### H1 security boundary

H1 completion update (2026-09-04): the API image was built locally and executed as an unprivileged container user. Its liveness and readiness endpoints returned only safe service/version data. This verifies a local container foundation, not Cloud Run deployment, Cloudflare Access, R2 retention/deletion, authenticated invocation, or hosted beta access.

Hosted beta is not an anonymous public API. The frontend calls a same-origin Worker control plane under Cloudflare Access; it does not call Cloud Run directly. The R2 bucket is private, and Cloud Run must require an authenticated control-plane invoker. H1 prepares these contracts and a conservative deployment example only. H2 must create and prove the actual Access, Worker-to-Cloud-Run authentication, R2 lifecycle/deletion, and synthetic end-to-end path.

### H2 identity bridge

H2 must not put a Google service-account private key in Cloudflare merely to satisfy Cloud Run IAM. The selected route is Access-protected Worker -> Google API Gateway, where the gateway validates the exact Cloudflare Access JWT issuer/audience and invokes Cloud Run with its own least-privilege service account. FastAPI additionally checks a short-lived Worker HMAC. This preserves non-anonymous Cloud Run and rejects direct Gateway calls that bypass the Worker. The preflight requirements are in `docs/42_HOSTED_BETA_H2_PREFLIGHT.md`.

## Cost controls

- Minimum instances: zero during early beta unless cold start materially hurts conversion.
- Maximum instances set to a conservative cap.
- File-size and scan-cell limits.
- Job concurrency tuned to memory profile.
- No LLM call in free static scan by default.
- R2 deletion enforced.
- Per-IP/session rate limits.
- Daily spending and error alerts.

## Deployment sequence

1. Build and test locally.
2. Build frontend production bundle.
3. Build API container.
4. Deploy API with no public customer files.
5. Deploy frontend against API.
6. Run synthetic end-to-end tests.
7. Configure custom domain.
8. Add R2/control-plane upload.
9. Verify automatic deletion.
10. Perform security review.
11. Invite a small beta group.

## Environment separation

Use separate projects/buckets/databases for:

- local.
- development.
- staging.
- production.

Production secrets and files must never be accessible from development.

## Rollback

- Frontend: retain previous deployment.
- API: Cloud Run revisions with traffic rollback.
- Scanner/rule changes: versioned results and feature flags.
- Quote changes: do not alter already issued quotes.
- Repair engine: disable new jobs while preserving valid completed downloads.

## Domain mapping

Use one canonical host. Redirect alternate `.kr`/`.com` domains to the canonical locale path. Avoid operating duplicate SEO content on multiple domains.
