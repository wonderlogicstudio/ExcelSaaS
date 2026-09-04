# Hosted Beta H1 Final Report

## Decision

`COMPLETED — Deployment Foundation & Security Boundary`

H1 is complete as a local, deployable foundation. It is not a hosted beta, public launch, cloud deployment, or authorization to accept user workbooks. H2 is `Awaiting Product Owner Approval`.

## Delivered boundary

- The future browser path is fixed as Cloudflare Access-protected hostname -> same-origin Worker `/api` control plane -> private R2 -> authenticated Cloud Run -> value-free response -> deletion attempt plus lifecycle backstop.
- Cloud Run must not be made anonymous. The frontend never receives a Cloud Run origin URL.
- `hosted_beta` and `production` fail closed unless they use declared environment names and exact HTTPS CORS origins. Formula Audit remains unavailable outside development/internal beta.
- The API container is non-root, uses a private container temporary directory, and has content-free liveness/readiness endpoints.
- Structured logs use a code-enforced allowlist; generic failures expose only `INTERNAL_ERROR`.
- Separate environment/secret, lifecycle/observability, and H2 deployment/rollback contracts are recorded in docs 38–40.

## Local verification

| Check | Result |
| --- | --- |
| Docker image build | Passed (`workbookcare-api:h1`) |
| Container runtime | Passed as `uid=100(app)` |
| `/health/live` | Passed; safe service state only |
| `/health/ready` | Passed; safe scanner/rule/RC version fields only |
| Standard regression | Passed: web 23 tests + production build; API 50 tests + Ruff; supplied M4-C pack 36 exact candidates/no extras |
| M4 release regression | Passed with existing narrow fixture waiver: 72/72 locations and top-level rules; M4-A.5 `CONDITIONAL_GO`, precision/recall 1.0 |

## Important non-claims

- No Cloudflare, R2, Google Cloud, Cloud Run, Artifact Registry, DNS, domain, secret, IAM identity, or hosted endpoint was created.
- No user, company, or real workbook was uploaded, retained, deleted, or logged.
- Access policy, Worker-to-Cloud-Run authentication, R2 private-object lifecycle, rate limiting, cost alerts, and hosted end-to-end cleanup are H2 gates, not verified H1 behavior.
- No M5, repair, repaired XLSX, payment, account, AI, VBA, Power Query, analytics, or external M3/M3.5 test began.

## H2 human approval gates

1. Approve the beta audience, permitted synthetic/real-file policy, retention wording, and support owner.
2. Create separate hosted-beta Cloudflare and Google Cloud resources with least privilege.
3. Prove Access protection, non-anonymous authenticated Worker-to-Cloud-Run calls, private opaque R2 objects, deletion plus lifecycle backstop, and direct-origin bypass rejection.
4. Run synthetic hosted end-to-end, failure, deletion, desktop, and mobile checks before inviting anyone.
