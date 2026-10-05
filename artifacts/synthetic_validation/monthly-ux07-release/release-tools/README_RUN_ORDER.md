# MONTHLY-UX07 release helper run order

All helper files and default outputs stay under `artifacts/synthetic_validation/monthly-ux07-release/release-tools` in the ExcelSaaS repo. These helpers do not mutate cloud state unless an operator supplies the explicit confirmation token shown below.

The invalid local image `sha256:a088bc14578202bcd3d0e030826d4222428adb082a991b48f25eb72d38748d57` was superseded before any push. Do not push it. The current corrected local overlay is recorded in `output/image/build.json`.

1. Freeze reviewed inputs:
   `python artifacts/synthetic_validation/monthly-ux07-release/release-tools/freeze_release_sources.py`

2. Build the local OCI overlay package only:
   `python artifacts/synthetic_validation/monthly-ux07-release/release-tools/build_api_overlay.py`

3. API operator phases after helper review:
   - `python artifacts/synthetic_validation/monthly-ux07-release/release-tools/deploy_api_guarded.py baseline`
   - `python artifacts/synthetic_validation/monthly-ux07-release/release-tools/deploy_api_guarded.py image`
   - `python artifacts/synthetic_validation/monthly-ux07-release/release-tools/deploy_api_guarded.py push --confirm-mutation MONTHLY_UX07_APPROVED_MUTATION`
   - `python artifacts/synthetic_validation/monthly-ux07-release/release-tools/deploy_api_guarded.py stage --confirm-mutation MONTHLY_UX07_APPROVED_MUTATION`
   - `python artifacts/synthetic_validation/monthly-ux07-release/release-tools/deploy_api_guarded.py proof`
   - `python artifacts/synthetic_validation/monthly-ux07-release/release-tools/deploy_api_guarded.py live --confirm-mutation MONTHLY_UX07_APPROVED_MUTATION`
   - `python artifacts/synthetic_validation/monthly-ux07-release/release-tools/deploy_api_guarded.py traffic --confirm-mutation MONTHLY_UX07_APPROVED_MUTATION`
   - `python artifacts/synthetic_validation/monthly-ux07-release/release-tools/deploy_api_guarded.py after`

4. Web operator phases only after API `after.json` exists:
   - `python artifacts/synthetic_validation/monthly-ux07-release/release-tools/release_web6.py baseline`
   - `python artifacts/synthetic_validation/monthly-ux07-release/release-tools/release_web6.py build`
   - `python artifacts/synthetic_validation/monthly-ux07-release/release-tools/release_web6.py upload --confirm-mutation MONTHLY_UX07_APPROVED_MUTATION`
   - `python artifacts/synthetic_validation/monthly-ux07-release/release-tools/release_web6.py deploy --confirm-mutation MONTHLY_UX07_APPROVED_MUTATION`

Stage behavior: the staged revision uses only a temporary `python -m release_tools.rp03_startup_wrapper` command and expanded startup probe to run the existing runtime verification plus the RP03 approve/execute/download3 synthetic proof. The proof phase requires both `delivery_runtime_verified` and `monthly_rp03_runtime_verified` events from the exact staged revision and image.

Live behavior: the live revision uses the same verified image, restores command, args, startup probe, and environment from the baseline revision in memory, asserts only baseline runtime hashes are persisted, and keeps old traffic at 100 percent until the `traffic` phase. The `traffic` phase verifies the pushed image, staged proof, live runtime restoration, private IAM, and old traffic before switching to the live revision and removing temporary release tags. The `after` phase rechecks IAM, Gateway, Worker bindings, Access, image, revision, traffic, and rollback information.

No permanent debug route, auth change, pricing/payment change, IAM loosening, Gateway change, storage binding change, Worker binding drift, raw env serialization, or DigitalTwin output path is allowed by these helpers.
