# FALSE-REPAIR-GUARD01 API-only guarded release

Live baseline read-only checked 2026-09-27: API `workbookcare-api-beta-00033-dum` at image `sha256:d2265d9e56756fd240e1ddf93509d9fa096bd6d77acd499caff9d41ab1caa5c9`, traffic 100%; Worker `44ed2196-cca5-4fa9-963c-16497a3ff77a`, traffic 100%. The helper checks these again, plus IAM, Gateway, Access, bindings, runtime env/secret references, identity, scaling, ingress, probe and image/traffic hashes. It does not deploy the frontend or Worker.

Run only after final regression and native compatibility reference are reviewed and source edits have stopped. From repository root in PowerShell, first set `$py = '.\apps\api\.venv\Scripts\python.exe'`, then run:

1. `& $py -B artifacts/synthetic_validation/false-repair-guard01-release/release-tools/freeze_release_sources.py`
2. `& $py -B artifacts/synthetic_validation/false-repair-guard01-release/release-tools/build_api_overlay.py`
3. `& $py -B artifacts/synthetic_validation/false-repair-guard01-release/release-tools/deploy_api_guarded.py baseline`
4. `& $py -B artifacts/synthetic_validation/false-repair-guard01-release/release-tools/deploy_api_guarded.py image`
5. Review `source-freeze.json`, image `build.json`, `output/api-release/baseline.json`, and local/independent review before any mutation.
6. `& $py -B artifacts/synthetic_validation/false-repair-guard01-release/release-tools/deploy_api_guarded.py push --confirm-mutation FALSE_REPAIR_GUARD01_APPROVED_MUTATION`
7. `& $py -B artifacts/synthetic_validation/false-repair-guard01-release/release-tools/deploy_api_guarded.py stage --confirm-mutation FALSE_REPAIR_GUARD01_APPROVED_MUTATION`
8. `& $py -B artifacts/synthetic_validation/false-repair-guard01-release/release-tools/deploy_api_guarded.py proof`
9. `& $py -B artifacts/synthetic_validation/false-repair-guard01-release/release-tools/deploy_api_guarded.py live --confirm-mutation FALSE_REPAIR_GUARD01_APPROVED_MUTATION`
10. `& $py -B artifacts/synthetic_validation/false-repair-guard01-release/release-tools/deploy_api_guarded.py traffic --confirm-mutation FALSE_REPAIR_GUARD01_APPROVED_MUTATION`
11. `& $py -B artifacts/synthetic_validation/false-repair-guard01-release/release-tools/deploy_api_guarded.py after`

Each phase writes fresh evidence and refuses overwriting it. A failed phase needs inspection before retry. `proof` requires existing RP03 runtime proof and the new valid synthetic guard preflight event: E3 `123` with `00000` refused, B2/B3 numeric-text controls eligible. No raw env/token is serialized. Do not use the false-repair raw fixture as native Excel compatibility evidence; the separate three-profile native run supplies that gate. `traffic` changes customer routing only after Linux proof and baseline runtime restoration.
