# Hosted Beta H2 — Deployment Preflight and Security Decision

## Current activation — 2026-09-09

`IN PROGRESS — synthetic-only.` This section supersedes the original preflight
blocker record below. The product owner has supplied the existing Google Cloud
project `workbookcare-beta`, Cloud Run URL and runtime account; created the private
R2 bucket `workbookcare-beta-uploads` with a one-day lifecycle deletion rule; and
created the Access-protected `workbookcare-beta` Worker with `UPLOADS` bound to that
bucket. API Gateway is enabled and
`workbookcare-gateway-invoker@workbookcare-beta.iam.gserviceaccount.com` has only
the Cloud Run Invoker role on the existing service.

API Gateway has no Seoul location. The owner explicitly approved Tokyo
`asia-northeast1` for the bridge to the existing Seoul `asia-northeast3` Cloud Run
service. Request bodies therefore cross that regional boundary. H2 remains
synthetic-only and must not claim Korean-only residency. Remaining gates are the
provider-only HMAC secret, the revision of the same existing Cloud Run service,
Gateway configuration, Worker deployment, and positive/negative cleanup proof.

## Local implementation evidence — 2026-09-09

- `scripts/verify.ps1` passed: web 25 tests plus production build, Worker 3
  security/cleanup tests, API 68 tests, Ruff, and the supplied M4-C 36-candidate
  sample-pack check all passed. The only warning is the existing Starlette
  TestClient deprecation.
- `scripts/verify-m4-release.ps1 -AcceptProductOwnerFixtureWaiver` passed: the
  immutable M4-C final evaluator returned 72/72 location and top-level-rule
  matches under the accepted narrow fixture waiver; M4-A.5 remains
  `CONDITIONAL_GO` rather than a production quality claim.
- A newly built local `workbookcare-api:hosted-beta-h2` container passed its
  synthetic HMAC upload, failure, health, non-root, and temporary-file cleanup
  rehearsals on ports 8080 and 9091. This is not a Cloud Run deployment.

## Current status

`IN PROGRESS — the original blocker entry below is historical only.`

`HISTORICAL PRE-APPROVAL BLOCKER — resolved.` The target project, existing Cloud
Run service, private R2 bucket, Access-protected Worker, Gateway API, and
dedicated Gateway invoker account are now known and approved. This PC still has
no authenticated `gcloud` or `wrangler`; the approved operator now has both
authenticated locally. Use `infra/gateway/deploy.ps1` from Windows PowerShell or
`infra/gateway/deploy.sh.example` from Google Cloud Shell. Neither route stores
deployment credentials in the repository.

## Required H2 control path

```text
Access-protected browser
  -> same-origin Cloudflare Worker
  -> private R2 object with opaque key
  -> Google API Gateway
       validates the exact Cloudflare Access JWT issuer + application audience
  -> non-anonymous Cloud Run
       accepts calls only from the API Gateway backend-auth service account
  -> static scan result
  -> Worker deletion attempt + R2 lifecycle backstop
```

The Worker must also attach a short-lived, body-bound HMAC signature that FastAPI verifies. This prevents an authenticated user from bypassing the Worker by calling the API Gateway directly. The HMAC exists only in the Cloudflare Worker secret store and Google Secret Manager.

## Why the additional API Gateway is required

Cloud Run IAM accepts a Google-signed ID token from an authorized principal. A Cloudflare Worker is external to Google Cloud and cannot safely obtain that token without either workload-identity federation or a Google service-account private key. H1 prohibits storing such a long-lived key in Cloudflare.

API Gateway resolves this boundary without changing Cloud Run to anonymous: it validates the Worker-forwarded Cloudflare Access JWT, and its dedicated backend-auth service account is the only Cloud Run Invoker. The public gateway is not a browser API: requests require both the exact Access JWT and the Worker-generated HMAC. Direct Cloud Run requests remain rejected by IAM.

## Inputs and permissions required from the operator

1. Install/authorize Google Cloud CLI and Wrangler with internet access.
2. Google Cloud project ID, billing-enabled confirmation, and a region approval (the H1 default is `asia-northeast3`).
3. Google roles for the operator: Artifact Registry, Cloud Run, API Gateway/API Config, IAM service-account administration, Secret Manager, logging/budget configuration, and permission to enable required APIs.
4. Cloudflare account ID, a hosted-beta zone/hostname, R2 enablement, Workers deployment permission, Zero Trust/Access administration, and an Access policy containing only the operator for synthetic testing.
5. Confirmation that a dedicated hosted-beta R2 bucket, Cloud Run service, API Gateway, service accounts, secret namespaces, and logs may be created and billed.
6. Explicit approval of the API Gateway bridge and its small additional cost/operational footprint.

## Required secrets (provider stores only)

| Secret | Store | Purpose |
| --- | --- | --- |
| `WORKBOOKCARE_CONTROL_PLANE_HMAC_SECRET` | Cloudflare Worker + Google Secret Manager | short-lived, body-bound Worker-to-FastAPI request proof |
| R2 S3 access credentials, if presigned retrieval is selected | Cloudflare Worker only | create single-object, short-lived analysis retrieval authorization |
| Google service account key | nowhere | prohibited; API Gateway uses its own Google-managed identity |

No secret is committed, printed, added to a browser build, or accepted through chat.

## H2 verification after prerequisites

- Deploy an Access-protected Worker/static frontend, private R2 bucket/lifecycle policy, authenticated API Gateway, and Cloud Run with no anonymous invoker.
- Use only the repository synthetic workbook for upload, scan, optional separate Formula Audit, re-validation, and CSV path checks.
- Demonstrate denial for unauthenticated Worker, direct Gateway without the HMAC, direct Cloud Run, direct R2, expired upload authorization, malformed input, limit excess, timeout, and cleanup failure.
- Verify immediate deletion attempts and the R2 lifecycle backstop with content-free events only.
- Run standard and M4 regression verification before recording H2 completion.
