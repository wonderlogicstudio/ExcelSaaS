from pathlib import Path
import hashlib,json,subprocess,sys
R=Path('C:/Users/JinwonLee/project/ExcelSaaS'); S=Path(__file__).parent
sys.path.insert(0,str(R/'apps/api'))
from app.delivery_execution import patch_fingerprint
from app.delivery_plan import reference_status
D=S/'compatibility'
inputs=json.loads((D/'inputs.json').read_text(encoding='utf-8'))
assert inputs['patch_fingerprint']==patch_fingerprint()
assert reference_status()['status']=='PASS'
source=R/'samples/delivery-v3_2/delivery-rp01-rp02.xlsx'
source_hash=hashlib.sha256(source.read_bytes()).hexdigest()
baseline=json.loads((S/'baseline.json').read_text(encoding='utf-8'))
assert source_hash==baseline['protected']['samples/delivery-v3_2/delivery-rp01-rp02.xlsx']
before={}
for row in inputs['rows']:
 assert row['source_hash']==source_hash and row['ready_published'] is False
 for kind,meta in row['files'].items():
  path=D/(row['profile']+'-'+kind+('.html' if kind=='VERIFICATION_HTML' else '.xlsx'))
  digest=hashlib.sha256(path.read_bytes()).hexdigest()
  assert digest==meta['sha256'] and path.stat().st_size==meta['bytes']
  before[path.name]=digest
p=subprocess.run(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',str(S/'verify_excel.ps1')],capture_output=True,text=True,encoding='utf-8',errors='replace')
(S/'excel-command.json').write_text(json.dumps({'command':'powershell.exe -NoProfile -ExecutionPolicy Bypass -File verify_excel.ps1','exit_code':p.returncode},indent=2),encoding='utf-8')
if p.returncode:
 print('Excel synthetic verification failed; exit_code='+str(p.returncode));raise SystemExit(p.returncode)
assert inputs['patch_fingerprint']==patch_fingerprint()
assert all(hashlib.sha256((D/name).read_bytes()).hexdigest()==digest for name,digest in before.items())
e=json.loads((D/'excel-reopen.json').read_text(encoding='utf-8-sig'))
assert e['status']=='PASS' and e['patch_fingerprint']==inputs['patch_fingerprint']
assert set(e['profiles'])=={'RP01','RP02'} and len(e['results'])==2
for row in e['results']:
 assert all(row[k] is True for k in ['repaired_opened','changes_opened','actual_values_match','literal_report_formulas','read_only_hash_unchanged'])
 assert row['output_hash']==before[row['profile']+'-REPAIRED_XLSX.xlsx']
record={'status':'PASS','actual_excel_files_opened':4,'all_generated_artifact_hashes_unchanged':before,'source_sha256':source_hash,'patch_fingerprint':inputs['patch_fingerprint'],'reference_registered':False,'excel_version':e['excel_version'],'excel_build':e['excel_build']}
(S/'excel-bound-evidence.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
print(json.dumps({'status':'PASS','actual_excel_files_opened':4,'all6artifact_hashes_bound':True,'reference_registered':False}))
