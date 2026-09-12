# Existing protected beta release workflow

The owner's 2026-09-12 standing authorization applies until project completion or
revocation. After each separately approved development unit passes its required
checks, deploy its validated changes to:

https://workbookcare-beta.wonderlogic-studio.workers.dev/

Do not ask for the same beta deployment permission again. This is a deployment
authorization, not approval to start the next development bundle. Remote Git push,
new paid resources, production/public exposure, real customer data, live payments,
refunds, prices and invitations still need their own authorization. Preserve prior
progress/reviews; do not declare H2/H3 ready from a product release.

## Scope and preparation

1. Read the current milestone, delta and actual local evidence. Preserve owner
   changes. Select the validated components needed for this release.
2. Reuse still-current passing checks; rerun checks affected by code, build or
   environment changes. Record command, exit code and meaningful limitations.
3. Preserve Access, authenticated Gateway/Cloud Run, private R2/KV and existing
   capability gates. A frontend-only release does not imply the API was upgraded.
   If the approved unit needs an API revision, validate that revision and its
   rollback before updating the existing service with the same boundaries.
4. Inspect the currently active Worker version and compare configuration without
   printing/storing credentials, secret values, customer content or account emails.
   Keep the prior version ID for rollback. Abort when unrelated remote drift exists.

## Current web build

Use explicit non-secret process environment overrides rather than replacing user
environment files. From the repository root:

```powershell
$env:VITE_PRODUCT_ENV='hosted_beta'
$env:VITE_API_BASE_URL='/api'
$env:VITE_FEEDBACK_CAPTURE_ENABLED='false'
$env:VITE_FORMULA_AUDIT_INTERNAL_BETA_ENABLED='false'
$env:VITE_FORMULA_AUDIT_HOSTED_BETA_ENABLED='true'
$env:VITE_HOSTED_BETA_FEEDBACK_ENABLED='false'
npm.cmd run build --workspace @workbookcare/web -- --mode hosted_beta
```

The owner approved automatic separate M4 on this protected beta on 2026-09-12.
Production M4 and feedback remain off. The API requires both
`FORMULA_PATTERN_AUDIT_ENABLED=true` and `HOSTED_BETA_FORMULA_AUDIT_ENABLED=true`
in hosted_beta with HMAC required. Preserve every other environment/secret/IAM setting.
Use the installed Wrangler version. D01 used 4.130.0 via
`npx.cmd --offline --no-install wrangler` with config
`infra/cloudflare/wrangler.jsonc`. Do not save credentials to repository files.

Use `versions upload --dry-run --keep-vars --strict --var FORMULA_AUDIT_ENABLED:true`, then upload the verified
version with the same explicit `--var FORMULA_AUDIT_ENABLED:true` override and a release-specific tag/message.
The checked-in Worker default stays false. Compare the new version's binding
metadata with the previously active version before `versions deploy <id>@100`.
The versions workflow preserves existing triggers/routes; do not replace the
Access policy or create a preview route to bypass login. Secret values must not
be read for these comparisons. These commands are described in the official
[Wrangler documentation](https://developers.cloudflare.com/workers/wrangler/commands/workers/).

## Verify and record

- Re-query active version/percentage and compare the intended release ID.
- Confirm anonymous requests still redirect to the expected Access application;
  record only status/path and a destination-match boolean, never redirect tokens.
- When a connected authenticated browser is available, verify the actual page and
  approved synthetic flow. Do not extract login cookies or bypass Access when it
  is unavailable. Clearly separate local UI evidence, deployed-version evidence
  and authenticated hosted interaction evidence.
- Record build asset hashes, previous/current versions, commands/exits, changed
  components, unrun checks and owner actions in the bundle review/progress delta.
  Commit only verified release records locally. A beta deployment does not push Git.
- On a release regression, use the recorded previous Worker version if still
  deployable and compatible; verify the resulting active version. Do not disable
  Access or alter storage/security policies as a rollback shortcut.

Initial D01 beta evidence: [release record](delivery-v3_2/reviews/evidence/D01-beta-release.json).

## Approved M4 API/Gateway release

Use the existing Artifact Registry repository and pin the tested image digest.
Update only the existing Cloud Run image and the two approved M4 flags, initially
with `--no-traffic`. Check the created revision Ready/ContainerReady conditions,
not only the service latestReady field: a no-traffic revision can be RETIRED.
Preserve service spec/secret references and IAM, then explicitly shift traffic.
Clone the current existing Gateway OpenAPI config, add only `/v1/formula-audits`,
and retain the backend service identity/security/JWT audience/path translation.
Create a config version on the same API and update the same Gateway; no new gateway.
Keep the prior revision/config/Worker IDs for rollback. See the official
[Cloud Run revision guide](https://docs.cloud.google.com/run/docs/managing/revisions) and
[Gateway config guide](https://docs.cloud.google.com/api-gateway/docs/creating-api-config).
Latest release/rollback/actual hosted evidence: [M4 follow-up](delivery-v3_2/reviews/evidence/D01-m4-hosted.json).
