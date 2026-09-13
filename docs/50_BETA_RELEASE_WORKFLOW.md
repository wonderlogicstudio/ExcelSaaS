# Current D08 complex synthetic follow-up — 2026-09-13

Current private API: `workbookcare-api-beta-00014-nah`,100% in asia-northeast3. Immutable image `sha256:12edb4bea80533d20ddd59fe6cb71fb0749320422ee3f04b78de5ed182acecc2` in the same existing private repository. Worker `521ad0aa-55f9-4606-b481-fc4861d8a60f` and Gateway `workbookcare-beta-d08-e6132fcdf496` are unchanged. Only registered synthetic hashes changed:1repair input and2comparison pairs. Access/IAM/HMAC/R2/KV/flags/payment OFF are unchanged.

`build_complex_beta_oci.py` overlays exactly two allowlist files on the previously verified e6132f image; Java/wheels/application logic are hash-checked unchanged. No Docker, Cloud Build or new paid resource. `deploy_complex_beta.py` is a bounded recorded one-shot release helper, not a general automatic deployment command. Baseline11-bav → staging13-zum (20refs/2actual repairs/6files under120s staging probe) → same image live14-nah under original9s probe →100%traffic/tag removed → invariant and anonymous302 checks. Command exits and rollback baseline are in `delivery-v3_2/reviews/evidence/D08-complex-release.json`; actual site/Excel proof is in `D08-complex.json`.

Immediate API rollback is `workbookcare-api-beta-00011-bav` with imagee6132f. Worker/Gateway do not require changing for this two-file registry overlay. Recheck drift and compatibility before any separately needed rollback; do not perform it merely as a test. D08 is stopped awaiting owner; standing beta authorization does not start the proposed next test unit. Historical release records follow.

---

# Current D08 protected synthetic release — 2026-09-13

This section supersedes the D01-only build flags below. The historical D01 workflow is preserved. Current release proof is `delivery-v3_2/reviews/evidence/D08-hosted-release.json`, image/source/dependency hashes are in `D08-hosted-image.json`, and actual site/Excel acceptance is in `D08-hosted.json`. Do not rerun deployment automatically after the D08 stop.

Current Worker: `521ad0aa-55f9-4606-b481-fc4861d8a60f` (100%). Current private Cloud Run: `workbookcare-api-beta-00011-bav` (100%, asia-northeast3). Gateway: `workbookcare-beta-d08-e6132fcdf496` (existing Gateway, asia-northeast1). Image digest: `sha256:e6132fcdf49617331ffc9337c2903732999d6ce9facf4ee45558c1a9d782173b` in the existing private `workbookcare-beta/workbookcare-images/workbookcare-api` repository.

## Validated runtime and release sequence

Docker daemon did not respond to the bounded read-only check. No Docker/Desktop/WSL restart or Cloud Build service was used. `scripts/prepare_delivery_oci.py` and `scripts/build_delivery_oci.py` preserve the executed staging helper bodies with repository-relative roots/gcloud discovery. The existing API Dockerfile is still the earlier diagnosis-only packaging path; it has NOT been validated as the D08 Java/POI build. Use the OCI path and record a fresh candidate's inputs rather than claiming Dockerfile parity.

1. Read live revision, traffic, Gateway OpenAPI/identity, Worker binding metadata and private IAM. Compare hashes without logging secret values. Record rollback IDs and abort on unrelated drift.
2. Fetch the existing base digest `sha256:e57d3782741461d315b55770b1c45e4ecff2d1981535831d9b50f0b1b40343db`, select its Linux amd64 manifest, download official Temurin17 JRE and Python cp312 Linux wheels, and record their hashes. Do not upload credentials. Preparation resolves inputs, so review any changed Java/dependency hashes before a future build. The tested release used Java17.0.20+101 and the exact wheel hashes in the image evidence.
3. Add application, POI classes/JARs, reference registries and fixed reference inputs to the same base. Build a local OCI layer and push it only to the existing registry. `python scripts/build_delivery_oci.py` builds without pushing; `--push` performs the separately authorized existing beta registry update. Repository copies passed syntax checks; the equivalent staging helpers built and pushed the tested image.
4. Stage the immutable candidate without shifting main traffic. Require private IAM, unchanged HMAC/secrets/origin/resource limits, `DELIVERY_BETA_ENABLED=true`, `HOSTED_SYNTHETIC_DELIVERY_ENABLED=true`, PAYMENT_MODE OFF, and max instances1. An IAM-protected temporary revision tag triggers actual startup. Image registration Ready alone is insufficient.
5. Run `DELIVERY_RUNTIME_VERIFY=true` with a staging-only startup budget120s. The tested revision00008-zul emitted exactly20 fixed Excel-reference cases, two actual repair profiles and six generated artifacts. Log only counts/status. Check actual ContainerHealthy and that main traffic still points to the prior revision. This fixed-synthetic engine check is not PG or maximum-capacity evidence.
6. Deploy the SAME verified image with `DELIVERY_RUNTIME_VERIFY=false` and the ORIGINAL startup probe `/health:8080`, failureThreshold3, periodSeconds3, timeoutSeconds1. The live revision00011-bav passed. Then shift100% traffic and remove the temporary tag. Request-time source/plan/approval/reference/patch checks remain enabled. Do not rerun the whole regression suite on every cold start.
7. Clone the existing Gateway config, adding only `/v1/delivery` by preserving existing POST JWT security/backend service identity/path translation. Verify the original spec hash after removing that one route. Update the existing Gateway only after private API proof.
8. Use the D01 hosted web flags below PLUS `VITE_DELIVERY_BETA_ENABLED=true`. Keep both feedback flags false, internal formula flag false, and hosted formula flag true. Run web tests/type/build first. Build `--mode hosted_beta` with explicit process env, not owner env-file edits.
9. Wrangler upload uses `--dry-run --keep-vars --strict --var FORMULA_AUDIT_ENABLED:true --var DELIVERY_BETA_ENABLED:true`, then upload without dry-run. Compare EVERY existing binding (with only the intended delivery flag change for the initial D08 release) before `versions deploy <verified-id>@100 --yes`. Later UX releases preserved all bindings byte-for-byte as canonical metadata. Keep checked-in flags default-off.
10. Re-read revision/traffic/Gateway/Worker. Check anonymous `/`, `/api/v1/scans`, `/api/v1/formula-audits`, `/api/v1/delivery` all redirect302 to the existing Access host. Use the connected authenticated browser for actual synthetic upload/expected summary/type/cell/plan/approval/download checks. Open downloaded XLSX in installed Excel, read-only, with macros/links disabled; compare immutable oracles and original hashes. Never bypass Access or substitute package examples for hosted acceptance.

Provider command exits are retained under `artifacts/verification/d08-hosted/release/commands.jsonl` and the committed release evidence. Raw images, tokens, registry auth, local runtime caches and generated files stay outside Git. Only reviewed synthetic screenshots and minimal result/hash evidence are selected for commit.

## Rollback and unresolved boundaries

- Immediate last-copy rollback Worker: `6cee3405-5ee3-42be-9d99-d33c044f9bba`; previous delivery implementation Worker: `63d3dfdd-71e0-4d03-93bf-22b4b8d7d89f`.
- Full pre-D08 rollback: Worker `91c06632-1302-4877-ae49-d4e44af3f3a2`, Gateway config `workbookcare-beta-m4-0ae6c63c06a7`, private Cloud Run revision `workbookcare-api-beta-00004-hhk`. Restore the compatible Worker before rolling API/Gateway back so no new delivery requests start. Retain Access/IAM/private bindings. Recheck current drift and traffic before any rollback; do not issue rollback merely to test it.
- Hosted synthetic grants require registered input hash/pair, owner, exact plan/spec and expiry. They create no paid order or change approval. PAYMENT_MODE remains OFF; production flags remain default-off.
- API store is ephemeral with15-minute TTL and max instances1. Restart/loss, full concurrent load and durable commerce are unresolved. Expiry denies access immediately, but physical cleanup waits for CPU activity; a30s deletion guarantee during idle is not claimed.
- Official Toss account/keys are not prepared. PG auth/approval/query/cancel/webhook and checkout SDK remain NOT_RUN. Local payment contract tests are not official PG evidence. Price/tax/legal/support, parent patch/static-scan hard OS deadline and broader capacity remain gated.

---

## Historical D01 workflow

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
