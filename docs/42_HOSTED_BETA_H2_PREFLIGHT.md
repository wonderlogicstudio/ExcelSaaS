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
synthetic-only and must not claim Korean-only residency. The provider-only HMAC
secret, same-service H2 revision, Gateway and Worker are deployed. Positive browser
end-to-end and remaining security/deletion/lifecycle proof are still required.

## Upload 404 remediation — 2026-09-09

The authenticated browser reached the upload flow but received `Not Found`.
Content-restricted Cloud Run request logs confirmed repeated `POST /` responses
with status 404 at 11:28–11:29 UTC. The deployed Google service config confirmed
`pathTranslation: CONSTANT_ADDRESS` for the `/v1/scans` operation.

The template now explicitly sets `path_translation: APPEND_PATH_TO_ADDRESS`.
Google's operation-level default otherwise drops the request path when the
backend address contains only the origin. The Cloud Run origin and JWT audience
remain unchanged. See [Google's path translation documentation](https://cloud.google.com/api-gateway/docs/passing-data).

A template-driven test reproduced the exact `{"detail":"Not Found"}` before
the fix. With the fix it reaches the real FastAPI scan route through hosted HMAC
validation, returns 200 for a synthetic workbook, and denies an unsigned request
with 401. Worker tests also prove deletion attempts after a backend 404 and a
network failure. These are local regression tests, not live R2 deletion evidence.

Replacement config `workbookcare-beta-config-20260909203335` and existing Tokyo
gateway `workbookcare-beta-gateway` are ACTIVE; the gateway points to the new
config as of 2026-09-09 11:44:10 UTC. The deployment script exited successfully.
The compiled backend rule was rechecked: `APPEND_PATH_TO_ADDRESS` is active.
Prior config
`workbookcare-beta-config-20260909200234` is retained for rollback. No Cloud Run
revision, IAM policy, Access policy, HMAC secret, or Worker code changes are needed
for this routing correction.

Previously deployed H2 resources:

- Cloud Run `workbookcare-api-beta-00002-d5l`, Seoul, 100% traffic; still IAM-required.
- Worker `workbookcare-beta`, version `ef00a4c7-4406-4314-9666-d70edc74ad65`.
- Gateway `workbookcare-beta-gateway-3azf8h57.an.gateway.dev`, Tokyo.
- Provider-only HMAC secret, existing private R2 bucket and `UPLOADS` binding.

Read-only Wrangler inspection after the failed uploads reported `object_count: 0`
and `bucket_size: 0 B`. The enabled `delete-uploads-after-1-day` rule applies to
all prefixes. This inventory/lifecycle-configuration snapshot does not prove
per-request immediate deletion or an actual one-day lifecycle expiration event.
Wrangler also confirms public `r2.dev` access is disabled and no custom domains
are attached to this bucket.

Post-rollout anonymous probes: Worker GET redirects to Access (302), Gateway
`POST /v1/scans` rejects a tokenless request (401), and Cloud Run health access is
denied (403). These do not substitute for an authenticated browser scan or an
Access-authenticated Gateway request without the Worker HMAC.

## Positive browser scan — 2026-09-09

An Access-authenticated browser submitted the approved synthetic workbook after
the routing rollout and displayed the normal diagnosis result. Content-restricted
Cloud Run logs record `POST /v1/scans` with status 200 at 11:52:25 UTC. Immediately
afterward, a read-only R2 inspection returned `object_count: 0` and `bucket_size:
0 B`. This proves the successful browser → Worker → Gateway → Cloud Run flow and
that no object remained after this successful request; it does not prove a forced
failure cleanup branch or a one-day lifecycle expiration event.

The result screen distinguishes 10 findings needing possible review (1 safe repair
candidate, 7 user-confirmation items, 2 expert-review items) from 2 informational
items requiring no immediate modification. The counts are intentionally not a
contradiction.

H2 remains **IN PROGRESS** for the remaining live negative/deletion/lifecycle gates.

## Malformed browser failure and cleanup — 2026-09-09

The browser then submitted `samples/hosted-beta-invalid.xlsx`, a deliberately
invalid plain-text, synthetic file carrying an `.xlsx` extension. Content-restricted
Cloud Run logs record `POST /v1/scans` with status 415 at 12:09:52 UTC. A
read-only R2 inspection immediately afterward returned `object_count: 0` and
`bucket_size: 0 B`. This proves the malformed-input terminal path reaches the
deployed route and does not leave a temporary object behind. It does not test the
maximum-size, timeout, or forced-cleanup-failure paths, and it does not observe a
one-day lifecycle expiration.

Remaining H2 gates are therefore: an Access-authenticated direct Gateway call
without the Worker HMAC (must be denied) and time-based observation of the
configured one-day lifecycle backstop. The product owner reports CSV download
complete and completed synthetic browser re-validation; the comparison summary
changed from `3/3` to `2/1`. Automated coverage exercises the bounded size and cleanup
error paths. No new credential or Access policy may be created merely to perform
the direct-Gateway check without owner approval.

## Operating controls and post-deployment verification — 2026-09-09

The currently deployed Worker version `50128bfe-4942-48e1-9732-b1bd07205464`
adds an `UPLOAD_RATE_LIMITER`: five upload attempts per 60 seconds for each
authenticated Access assertion. Its counter key is an irreversible assertion hash;
no assertion or identity is stored, returned, or logged. The Worker returns a safe
429 before R2 when the limit is reached. Automated checks also prove a file over
10 MiB is rejected before R2. The post-deployment standard suite passed with web
26, Worker 7, and API 70 tests plus production build, Ruff, and the supplied
M4-C pack.

Read-only provider checks after this deployment confirm: Worker 302 without
Access, Gateway 401 without a bearer assertion, direct Cloud Run 403, private R2
with no `r2.dev` URL or custom domain, zero R2 objects/bytes, and the enabled
one-day expiration rule. The existing project budget is KRW 10,000 with alerts
at 50%, 90%, and 100%; the Budget API was enabled only to verify that rule.

The product owner reports that browser CSV download succeeded and synthetic browser
re-validation completed, with its comparison summary changing from `3/3` to `2/1`.
A live valid-Access/no-HMAC Gateway probe also remains open: creating a persistent test route or service credential
for this purpose was deliberately not performed because it would broaden the
security surface. At 2026-09-09 12:37 UTC, one content-free synthetic lifecycle
probe was written to the private remote bucket under an opaque test key and read
back without outputting its key or bytes. The bucket summary count did not update
immediately, so direct remote read is the creation evidence. An observed lifecycle
expiration must wait for the existing one-day rule to elapse; normal and malformed
terminal-path cleanup have already been verified immediately.

## Local implementation evidence — 2026-09-09

- `scripts/verify.ps1` passed: web 25 tests plus production build, Worker 5
  security/cleanup tests, API 70 tests, Ruff, and the supplied M4-C 36-candidate
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
dedicated Gateway invoker account are now known and approved. The approved
operator now has both `gcloud` and `wrangler` authenticated locally.
Use `infra/gateway/deploy.ps1` from Windows PowerShell or
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

### API Gateway multipart representation

Google API Gateway rejects OpenAPI 2.0 `type: file` parameters. The H2 gateway
therefore represents the single multipart form field as `type: string`; its
proxy does not enforce the form-data schema and forwards the original request.
The Worker and FastAPI remain the enforcement points for the `.xlsx`/`.xlsm`
allowlist, 10 MiB limit, multipart parsing, and body-bound HMAC. This is a
provider compatibility representation, not a relaxation of upload validation.

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
- Use only the repository synthetic workbook for upload, scan, re-validation, and CSV path checks. Formula Audit remains unhosted and default-off.
- Demonstrate denial for unauthenticated Worker, direct Gateway without the HMAC, direct Cloud Run, direct R2, expired upload authorization, malformed input, limit excess, timeout, and cleanup failure.
- Verify immediate deletion attempts and the R2 lifecycle backstop with content-free events only.
- Run standard and M4 regression verification before recording H2 completion.
