# M4-D Hosted Beta Readiness Checklist

## Scope

This is a deployment-readiness contract, not a deployment plan execution. No Cloudflare, R2, Cloud Run, database, feedback API, account, analytics service, or customer upload is created by M4-D.

## Required before any external beta invitation

- [ ] Product owner separately approves hosted beta, target users, and non-synthetic file policy.
- [ ] Use a distinct staging environment, origin, secrets, bucket, and logs. Development assets must not access beta files.
- [ ] Put access control in the deployment layer (for example, an invite-only identity-aware proxy). Do not add `hosted_beta` to the formula-audit server gate until this is tested.
- [ ] Keep the audit disabled by default and expose it only after server-side access control succeeds. A hidden button or client environment variable is insufficient.
- [ ] Set a private object-store design with random object keys, short-lived signed upload/download URLs, rate limiting, lifecycle deletion, and a verified immediate-delete path.
- [ ] Decide and test the exact temporary-file location, maximum retention, failed-upload cleanup, worker-crash cleanup, and operator access boundary. Do not claim automatic deletion or zero retention until tested.
- [ ] Use a separate worker/process with hard CPU, memory, request-size, decompression, and execution-time limits. The current synchronous process cannot honestly claim cancellation or enforced timeout.
- [ ] Define safe retry/idempotency behaviour before persistent upload sessions or analysis IDs are introduced.
- [ ] Add deployment health, dependency, rollback, and spend-alert checks without logging workbook content.
- [ ] Perform a privacy/security review of user-facing claims, retention wording, data location, and support escalation.

## Data and logging allowlist

Allowed operational events are opaque scan ID, scanner/rule-set/RC version, size/formula/sheet-count buckets, processing duration, rule code, subtype, and status/error code. They must not include filename, sheet name, cell location, finding key, formula, cell value, company/customer identifier, URL, or free-text feedback.

M4-D retains only category selections in local browser storage. It removes legacy local free-text memo fields when read and has no feedback API, database, telemetry, or staff dashboard. Do not add free text merely with a warning; it needs a later, separately approved retention/redaction/consent design.

## File-processing claims

The only current implementation-backed claims are that the scan does not execute VBA, macros, formulas, Power Query, or external links, and does not overwrite the original workbook. Claims of encryption, storage location, deletion, retention duration, production access control, or compliance certification are prohibited until they are implemented and verified.

## Hosted-beta go/no-go

All checkboxes above, an independent synthetic end-to-end deployment rehearsal, and explicit product-owner approval are required before external testing. M3 external user validation may resume only after this gate; it does not become completed merely because this document exists.
