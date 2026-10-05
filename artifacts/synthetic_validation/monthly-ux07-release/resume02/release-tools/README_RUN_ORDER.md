# MONTHLY-UX07 resume02 guarded release helper run order

All commands use the fresh resume02 helper paths. Earlier attempt artifacts are preserved and must not be edited.

Corrected local overlay, not pushed:
`asia-northeast3-docker.pkg.dev/workbookcare-beta/workbookcare-images/workbookcare-api@sha256:d2265d9e56756fd240e1ddf93509d9fa096bd6d77acd499caff9d41ab1caa5c9`

Invalid prior local images, do not push:
- `sha256:a088bc14578202bcd3d0e030826d4222428adb082a991b48f25eb72d38748d57`
- `sha256:e229f7df95435b69e677f5e9758c956cd0c666c739d8673e76f3410744d75b99`

Dry local preparation already run:
1. `python artifacts/synthetic_validation/monthly-ux07-release/resume02/release-tools/freeze_release_sources.py`
2. `python artifacts/synthetic_validation/monthly-ux07-release/resume02/release-tools/build_api_overlay.py`
3. helper syntax parse and OCI tar path inspection

API release phases after reviewer PASS and operator/browser readiness:
1. `python artifacts/synthetic_validation/monthly-ux07-release/resume02/release-tools/deploy_api_guarded.py baseline`
2. `python artifacts/synthetic_validation/monthly-ux07-release/resume02/release-tools/deploy_api_guarded.py image`
3. `python artifacts/synthetic_validation/monthly-ux07-release/resume02/release-tools/deploy_api_guarded.py push --confirm-mutation MONTHLY_UX07_APPROVED_MUTATION`
4. `python artifacts/synthetic_validation/monthly-ux07-release/resume02/release-tools/deploy_api_guarded.py stage --confirm-mutation MONTHLY_UX07_APPROVED_MUTATION`
5. `python artifacts/synthetic_validation/monthly-ux07-release/resume02/release-tools/deploy_api_guarded.py proof`
6. `python artifacts/synthetic_validation/monthly-ux07-release/resume02/release-tools/deploy_api_guarded.py live --confirm-mutation MONTHLY_UX07_APPROVED_MUTATION`
7. `python artifacts/synthetic_validation/monthly-ux07-release/resume02/release-tools/deploy_api_guarded.py traffic --confirm-mutation MONTHLY_UX07_APPROVED_MUTATION`
8. `python artifacts/synthetic_validation/monthly-ux07-release/resume02/release-tools/deploy_api_guarded.py after`

Web release phases only after API `after.json` exists:
1. `python artifacts/synthetic_validation/monthly-ux07-release/resume02/release-tools/release_web6.py baseline`
2. `python artifacts/synthetic_validation/monthly-ux07-release/resume02/release-tools/release_web6.py build`
3. `python artifacts/synthetic_validation/monthly-ux07-release/resume02/release-tools/release_web6.py upload --confirm-mutation MONTHLY_UX07_APPROVED_MUTATION`
4. `python artifacts/synthetic_validation/monthly-ux07-release/resume02/release-tools/release_web6.py deploy --confirm-mutation MONTHLY_UX07_APPROVED_MUTATION`

Resume02 corrections covered:
- `--update-env-vars DELIVERY_RUNTIME_VERIFY=false` in stage avoids clearing baseline env.
- Live restore builds `--set-env-vars` and `--set-secrets` from the baseline revision in memory, preserving literal env and `valueFrom` secret refs without serializing raw values.
- Empty baseline command/args emit explicit empty `--command` and `--args`; post-deploy revision hashes verify the reset.
- Service/revision invariant hashes cover ingress, identity, env names/valueFrom hash, resources, volumes, scaling, timeout, command/args/probe/env runtime hashes, Gateway, IAM, Worker bindings, Access and image/revision/traffic chain.
- Push phase uploads config/layer/manifest to the same registry host and asserts Docker content digest before marking `pushed: true`.
- Stage/proof/live/traffic bind actual revision image, source freeze hash and runtime proof to the same pushed digest.
- Web helper verifies live API/IAM from provider reads and checks frozen frontend source plus dist assets before upload.

No helper writes to DigitalTwin. No permanent debug route, auth change, pricing/payment change, IAM loosening, Gateway change, storage binding change, Worker binding drift, raw env serialization or cloud mutation is allowed without the explicit confirmation token.