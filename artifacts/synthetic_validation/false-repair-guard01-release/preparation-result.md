# FALSE-REPAIR-GUARD01 API release preparation

Scope: local helper and read-only baseline only. No source freeze, image build, registry upload, Cloud Run mutation, Worker change or frontend build/deploy was run.

Read-only live provider checks on 2026-09-27:

- `gcloud.cmd run services describe workbookcare-api-beta --region asia-northeast3 --project workbookcare-beta --format=json --quiet` (projected revision, image and traffic only): exit 0 with API revision `workbookcare-api-beta-00033-dum`, image digest `sha256:d2265d9e56756fd240e1ddf93509d9fa096bd6d77acd499caff9d41ab1caa5c9`, traffic 100%. Initial sandboxed invocation: exit 1 because Cloud SDK credential/log files under AppData were denied; escalated read-only invocation succeeded.
- `npx.cmd --offline --no-install wrangler deployments list --json --config infra/cloudflare/wrangler.jsonc` (projected latest deployment identifiers only): exit 0 with Worker `44ed2196-cca5-4fa9-963c-16497a3ff77a`, traffic 100%.

Local checks from repository root:

- `py -3.10 -B -c "import ast,pathlib; p=pathlib.Path('artifacts/synthetic_validation/false-repair-guard01-release/release-tools'); [ast.parse(f.read_text(encoding='utf-8')) for f in p.glob('*.py')]; print('syntax PASS')"`: exit 0, 9 helper Python files parse.
- `./apps/api/.venv/Scripts/python.exe -B -c "... import rp03_startup_wrapper; print(_guard_verify(Path('.')))"`: exit 0, padded E3 refused and numeric B2/B3 controls eligible2. First local attempt exited 1 because openpyxl emitted an empty workbookProtection node; `book.security = None` corrected this synthetic setup, and the successful check is the final result.
- `./apps/api/.venv/Scripts/python.exe -B -m pytest artifacts/synthetic_validation/false-repair-guard01-release/release-tools/test_registry_location.py artifacts/synthetic_validation/false-repair-guard01-release/release-tools/test_release_gcloud.py -q -p no:cacheprovider`: exit 0, 9 passed.
- `Get-FileHash -Algorithm SHA256 apps/api/app/delivery_inputs.py,apps/api/app/repair_rules/numeric_text.py,apps/api/app/delivery_patch_reference.json`: exit 0; hashes `c5b5afc05549b384ea434d9056cc64cf450b7d8f29d9e18043afb3f99bfcdcb8`, `6803476418403b8aaa46b34d4dcb814dc13d8d1520ad20ffb9064395a1dc42f7`, `133e9e964d76eb7fd1ed4986f03eef1a45e3f649aff2b14fa77bbc57b0f644de` respectively.

The copied release helper differs from MONTHLY-UX07 resume02 only in pinned base revisions, image/Worker, new overlay file and wrapper path, new stage guard event, stage-to-live recovery check, local output paths, mutation token, and API-only run order. Existing IAM/Gateway/env/secret/Access/Worker-binding guards remain. Final regression and native compatibility source lock are external gates; freeze/build/release phases remain NOT_RUN.
