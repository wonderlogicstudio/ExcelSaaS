# Hosting and deployment plan

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
