# HORIZONTAL-01 integration release helpers

Prepared only; no deployment or provider mutation was run by this builder task.

Files:
- `build_image.py`: RULES-01 image overlay flow with only `apps/api/app/formula_patterns.py` added on top of the proven API image.
- `deploy_api.py`: guarded API phases: `baseline`, `image`, `stage`, `proof`, `live`, `traffic`, `after`.
- `release_web6.py`: guarded Worker/UI phases: `baseline`, `build`, `upload`, `deploy`.

Safety differences from the proven source helpers:
- Registry push requires `--push --confirm-push HORIZONTAL01_APPROVED_PUSH`.
- API cloud mutations require `--confirm-mutation HORIZONTAL01_APPROVED_MUTATION` on `stage`, `live`, and `traffic`.
- Worker upload/deploy require `--confirm-mutation HORIZONTAL01_APPROVED_MUTATION`.
- API baseline refuses to overwrite an existing `release/baseline.json`.
- Web baseline refuses to overwrite an existing `web-release/baseline.json` and requires the API `release/after.json`, `release/live.json`, and pushed image metadata from the promoted API helper.
- Source guards compare the frozen Horizontal01 integration hashes and keep only the known `apps/api/engine/dependencies.lock.json` dirty exception out of the image/source checks.
- The expected protected-beta pins are current for this handoff: API revision `workbookcare-api-beta-00023-juy`, API image digest `sha256:8f68132ce9c6285e447b3a1cd1a767691c62579e08752ecffb45e30e6f9c12e7`, Worker version `3b513785-21e8-4efe-8bc3-fcdf9301d0eb`, Gateway config `workbookcare-beta-d08-e6132fcdf496`.

Reviewed API order:
1. `python build_image.py`
2. `python deploy_api.py baseline`
3. `python build_image.py --push --confirm-push HORIZONTAL01_APPROVED_PUSH`
4. `python deploy_api.py image`
5. `python deploy_api.py stage --confirm-mutation HORIZONTAL01_APPROVED_MUTATION`
6. `python deploy_api.py proof`
7. `python deploy_api.py live --confirm-mutation HORIZONTAL01_APPROVED_MUTATION`
8. `python deploy_api.py traffic --confirm-mutation HORIZONTAL01_APPROVED_MUTATION`
9. `python deploy_api.py after`

Reviewed UI order, only after API `after` is complete:
1. `python release_web6.py baseline`
2. `python release_web6.py build`
3. `python release_web6.py upload --confirm-mutation HORIZONTAL01_APPROVED_MUTATION`
4. `python release_web6.py deploy --confirm-mutation HORIZONTAL01_APPROVED_MUTATION`
