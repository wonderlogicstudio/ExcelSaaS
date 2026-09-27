# UNSUPPORTED-PROPOSAL-UX01 protected Worker release preparation

Status: `BASELINE_AND_HOSTED_BUILD_PASS`; Worker upload/deploy `NOT_RUN` in preparation.

The helper is copied from `journey-download-feedback01-release` with only API00037/Worker44ed baseline pins, a fresh API evidence pointer, release token/tag/message, and fresh frontend source freeze. It retains existing `--keep-vars --strict`, dry-run, exact binding-hash comparison, private IAM check, nine Access redirects, source and asset digests, and API unchanged checks. Frontend freeze covers 97 source/config files with SHA-256 `da91ed08f35554bfeacfbe5ba8c25debcb231c539aba96b60684fd97093e3c28`.

Commands from repository root, both with `require_escalated`:

1. `py -3.10 -B artifacts/synthetic_validation/unsupported-proposal-ux01-release/run_release.py baseline` — exit 0. Live Worker `44ed2196-cca5-4fa9-963c-16497a3ff77a`; binding hash `67b4034829544f49ddf9a4fc71c9628587f7e001e4c5a984b714f73928254d2b`; API revision `workbookcare-api-beta-00037-bid`, image SHA-256 `efdbbba3e20e4958a59a2cfef27d097e8ae1ceb9dd57d957a039f91a7034db28`; private IAM hash `294ac4fc8b363b4fd1d2b1b4762667b42118c17e4d83b01daa8ca2a5dc0e7342`; all nine existing Access paths returned 302.
2. `py -3.10 -B artifacts/synthetic_validation/unsupported-proposal-ux01-release/run_release.py build` — exit 0. Source/API/Worker freeze checks and hosted-beta `tsc -b && vite build` passed. `output/web.json` records hosted flags and exact hashes for four dist assets.

Prepared mutation commands, **not executed by this preparation task**:

1. `py -3.10 -B artifacts/synthetic_validation/unsupported-proposal-ux01-release/run_release.py upload --confirm-mutation UNSUPPORTED_PROPOSAL_UX01_RELEASE_APPROVED`
2. After checking `output/upload.json` and exact binding equality: `py -3.10 -B artifacts/synthetic_validation/unsupported-proposal-ux01-release/run_release.py deploy --confirm-mutation UNSUPPORTED_PROPOSAL_UX01_RELEASE_APPROVED`

The helper records each subprocess exit in `output/commands.jsonl`, and refuses to overwrite phase evidence. `output/baseline.json` and `output/web.json` are the review inputs. No API, resource, security, or payment change is part of this Worker-only release.
