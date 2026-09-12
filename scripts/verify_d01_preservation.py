"""Audit a D01 delta against its startup Git ref and owner-file hash snapshot."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--base-ref', required=True)
parser.add_argument('--snapshot', required=True, type=Path)
parser.add_argument('--output', required=True, type=Path)
args = parser.parse_args()
root = Path(__file__).resolve().parents[1]


def git(*command: str) -> bytes:
    return subprocess.check_output(['git', *command], cwd=root)


protected = json.loads(args.snapshot.read_text(encoding='utf-8'))
owner_files = {name: digest for name, digest in protected.items()
               if name.startswith('docs/delivery-v3_2/') or name == 'docs/11_DECISIONS.md'}
for name, digest in owner_files.items():
    assert hashlib.sha256((root / name).read_bytes()).hexdigest() == digest, name

for name in ('docs/09_CURRENT_MILESTONE.md', 'docs/10_PROGRESS.md', 'docs/MILESTONE_REVIEW.md'):
    original = git('show', f'{args.base_ref}:{name}').decode('utf-8')
    current = (root / name).read_text(encoding='utf-8')
    assert original.split('\n', 1)[1] in current, f'Prior record was lost: {name}'

immutable_paths = [
    'apps/api/app/scanner.py', 'apps/api/app/formula_patterns.py',
    'apps/api/app/main.py', 'apps/api/app/config.py', 'apps/api/app/control_plane.py',
    'apps/web/src/lib/feedback.ts', 'apps/web/src/components/FormulaAuditPanel.tsx',
    'infra', 'docs/44_HOSTED_BETA_H3_OPERATIONAL_HARDENING.md',
    'docs/45_H3_PROCESSING_INVENTORY_AND_NOTICE_DRAFT.md',
    'docs/46_H3_SAFE_ERROR_TAXONOMY.md', 'docs/47_H3_SYNTHETIC_E2E_AND_ROLLBACK_CHECKLIST.md',
]
assert not git('diff', '--name-only', args.base_ref, '--', *immutable_paths).strip()
sources = git('ls-files', '-z', 'samples').decode('utf-8').split('\0')
workbooks = [name for name in sources if name.endswith(('.xlsx', '.xlsm'))]
for name in workbooks:
    assert (root / name).read_bytes() == git('show', f'{args.base_ref}:{name}'), name

fixtures = ['apps/web/src/data/demo-result.fixture.json', *[
    f'samples/m3/fixtures/{name}.scan-result.json'
    for name in ('low-or-zero-findings', 'revalidation-before', 'revalidation-after')
]]
for name in fixtures:
    original = json.loads(git('show', f'{args.base_ref}:{name}'))
    current = json.loads((root / name).read_text(encoding='utf-8'))
    for key in ('products', 'finding_counts'):
        current['scan_result'].pop(key, None)
    current['scan_result']['quote']['planned_deliverables'] = (
        original['scan_result']['quote']['planned_deliverables']
    )
    assert current == original, f'Non-product fixture evidence changed: {name}'

summary = {
    'status': 'PASS', 'base_ref': args.base_ref,
    'owner_package_and_decision_files_unchanged': len(owner_files),
    'prior_milestone_progress_review_preserved': True,
    'immutable_scanner_m4_feedback_infra_h3_paths': immutable_paths,
    'original_synthetic_workbooks_unchanged': len(workbooks),
    'fixture_changes_limited_to_product_projection': fixtures,
    'detection_labels_ids_timestamps_risk_prices_unchanged': True,
}
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(summary, ensure_ascii=False))
