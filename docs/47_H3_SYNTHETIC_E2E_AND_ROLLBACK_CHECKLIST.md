# Hosted Beta H3 — Synthetic E2E, deletion, and rollback checklist

> Use synthetic workbooks only. A checked item needs dated evidence; unchecked
> items are not inferred from source code or from a healthy landing page.

## Evidence already available

- [x] Authenticated synthetic normal upload reached `POST /v1/scans` and returned
  200; R2 was empty immediately afterward.
- [x] Authenticated malformed synthetic `.xlsx` reached the deployed route and
  returned 415; R2 was empty immediately afterward.
- [x] Browser CSV download reported successful by the product owner.
- [x] Browser re-validation was reported completed; its summary changed from
  `3/3` to `2/1`.
- [x] Tokenless Worker, Gateway, and Cloud Run negative probes are denied at
  their respective boundaries.
- [x] The private `FEEDBACK` KV binding is deployed; a tokenless feedback-route
  request is redirected to Cloudflare Access rather than reaching the Worker.
- [x] Read-only 2026-09-09 recheck: Cloud Run retains max 2, concurrency 1,
  CPU 1, 1 GiB, and 60 seconds; API Gateway is ACTIVE; Cloud Run has no public
  IAM member.
- [x] Source-level Worker/API tests cover bounded uploads, cleanup attempts,
  rate limits, safe errors, and content-free telemetry.

## Remaining synthetic verification

- [ ] Owner-session direct-Gateway no-HMAC probe returns the expected HMAC denial;
  immediately remove its temporary Worker route after evidence is recorded.
- [ ] Observe the remote content-free R2 lifecycle probe expired after
  2026-09-10 12:37:58 UTC (expiry may be delayed by the provider after eligibility).
- [ ] Browser repeats normal upload, finding-zero sample, multi-finding sample,
  limit error, malformed input, re-validation, and CSV flow on the deployed URL.
- [ ] Formula Audit remains inaccessible in the public hosted build. Test the
  deployed protected feedback binding only with an allowlisted synthetic payload,
  an invalid payload, rate limit, and the configured 30-day expiry setting.
- [ ] Inspect safe operational logs by field name and confirm no prohibited
  workbook or identity field appears.
- [ ] Verify the platform timeout/temporary-failure user experience without
  creating a persistent failure route or using a real workbook.

## Manual hosted UI walkthrough (human-owned)

- [ ] Desktop notebook/desktop viewport: landing, upload, processing, result,
  re-validation, CSV, errors, focus order, and refresh.
- [ ] Mobile-width viewport: the same sequence, including no horizontal overflow
  and reachable buttons/modals.
- [ ] Confirm the deployed UI exposes the beta notice and the privacy/terms links
  only after the corresponding build is deployed.

## Rollback rehearsal record

The previous API Gateway configuration is retained as
`workbookcare-beta-config-20260909200234`; the current configuration uses
`APPEND_PATH_TO_ADDRESS`. Cloud Run supports revision traffic rollback, and
Cloudflare supports Worker deployment rollback. H3 must not simulate a rollback
against the active synthetic beta until the product owner authorizes that
operational change.

Before invitation, record a synthetic rehearsal that verifies all of the
following: select previous Worker deployment; move Cloud Run traffic to the
previous revision; keep Formula Audit feature flags off; stop new uploads by
removing the Worker route/Access policy according to the approved runbook; and
inspect R2 for orphaned opaque objects. A healthy source build is not evidence of
this provider-side exercise.

## Current Go / No-Go result

`HOSTED BETA NOT READY`

Critical blockers: the H2 no-HMAC proof and lifecycle-expiry observation remain
open; protected feedback persistence still needs an authenticated synthetic
write/read proof; final legal/support/provider-retention decisions and hosted
desktop/mobile walkthrough remain human-owned; and the rollback rehearsal is not
yet authorized or evidenced. No invitation or M3 activity is authorized.
