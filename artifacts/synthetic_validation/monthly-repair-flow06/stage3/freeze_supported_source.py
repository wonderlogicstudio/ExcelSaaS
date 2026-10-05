from pathlib import Path
import sys, json, hashlib
sys.path.insert(0, 'apps/api')
sys.path.insert(0, 'apps/api/tests')
from test_delivery_inputs import monthly_workbook_bytes
raw = monthly_workbook_bytes()
out = Path('artifacts/synthetic_validation/monthly-repair-flow06/stage3')
source = out / 'monthly-rp03-supported-6sheet.xlsx'
if not source.exists():
    source.write_bytes(raw)
actual = source.read_bytes()
manifest = {
    'status': 'FROZEN_SUPPORTED_MONTHLY_RP03_SOURCE',
    'source': str(source),
    'sha256': hashlib.sha256(actual).hexdigest(),
    'sheet_count': 6,
    'target': {'sheet': 'Budget', 'cell': 'N18'},
    'before_formula': '=N15-N14',
    'after_formula': "='M10'!B16-'M10'!B15",
    'expected_value': -5,
    'original_13_sheet_oracle_replaced': False,
    'compatibility_ready_claimed': False,
}
(out / 'supported-source-manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(json.dumps(manifest, ensure_ascii=False, indent=2))
