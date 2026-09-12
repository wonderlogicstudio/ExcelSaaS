"""Register measured Excel compatibility; never invent or upgrade missing evidence."""
from pathlib import Path
import hashlib,json,sys
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'apps/api'))
from app.delivery_execution import patch_fingerprint
from app.delivery_plan import reference_status
root=R/'artifacts/verification/d04/compatibility'
data=json.loads((root/'excel-reopen.json').read_text(encoding='utf-8-sig'))
inputs=json.loads((root/'inputs.json').read_text(encoding='utf-8'))
assert reference_status()['status']=='PASS'
assert data['status']=='PASS' and data['patch_fingerprint']==inputs['patch_fingerprint']==patch_fingerprint()
assert set(data['profiles'])=={'RP01','RP02'} and len(data['results'])==2
for row in data['results']:
 assert all(row[k] is True for k in ['repaired_opened','changes_opened','actual_values_match','literal_report_formulas','read_only_hash_unchanged'])
 assert row['output_hash']==hashlib.sha256((root/(row['profile']+'-REPAIRED_XLSX.xlsx')).read_bytes()).hexdigest()
(R/'apps/api/app/delivery_patch_reference.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Measured Excel output evidence registered; current engine and patch fingerprints PASS.')
