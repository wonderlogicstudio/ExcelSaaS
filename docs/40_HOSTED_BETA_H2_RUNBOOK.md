# Hosted Beta H2 — Deployment and Rollback Runbook Draft

## Scope

This is a reproducible procedure draft, not authorization to deploy. Complete it only after H1 is accepted and the product owner separately approves H2.

## Required human-owned prerequisites

1. Create distinct Cloudflare hosted-beta resources: zone/hostname, Access application/policy, Worker route, private R2 bucket, lifecycle rule, and Worker secret store.
2. Create distinct Google Cloud resources: project or isolation boundary, Artifact Registry, Cloud Run service account with least privilege, Secret Manager entries, billing budget/alerts, and Cloud Run IAM policy.
3. Establish and test a Worker-to-Cloud-Run authenticated invocation. Do not grant `allUsers` an invoker role and do not use `--allow-unauthenticated` as a shortcut.
4. Approve a written beta file policy, support escalation path, data location, retention language, and allowed test participants.

## Local container rehearsal

Run only with synthetic files and a running Docker engine:

```powershell
docker build -t workbookcare-api:h1 -f apps/api/Dockerfile apps/api
docker run --rm -p 8080:8080 -e APP_ENV=development -e CORS_ORIGINS=http://localhost:5173 workbookcare-api:h1
Invoke-WebRequest http://127.0.0.1:8080/health/live
Invoke-WebRequest http://127.0.0.1:8080/health/ready
```

Expected: both endpoints return only safe service/version fields. Do not mount a folder containing real workbooks, `.env`, keys, or cloud credentials into the container.

## Deployment order after H2 approval

1. Run `scripts/verify-m4-release.ps1 -AcceptProductOwnerFixtureWaiver` and the standard verification suite.
2. Build the frontend with the untracked hosted-beta environment file so its API base is `/api`.
3. Build/publish the API image and deploy it with `infra/cloudrun/deploy.ps1.example`; preserve no-anonymous-invoker policy.
4. Configure Worker/API service authentication, private R2 permissions, exact CORS, rate limit, lifecycle deletion, budgets, and alerts.
5. Run a synthetic end-to-end upload, analysis, error, deletion, and direct-origin-bypass rehearsal.
6. Capture desktop/mobile states; complete `docs/35_M4D_MANUAL_RC_CHECKLIST.md` where applicable.
7. Obtain explicit product-owner approval before inviting any participant.

## Rollback

- Stop invitations and disable Access policy/Worker route before changing runtime code.
- Disable Worker-to-Cloud-Run analysis traffic while preserving the static information page if needed.
- Roll back Cloud Run traffic to the previous revision; never change a prior scanner/rule version's recorded result.
- Revoke temporary upload capability and verify lifecycle/deletion reconciliation using content-free events.
- Record only opaque identifiers, safe status codes, and version information in the incident record.
