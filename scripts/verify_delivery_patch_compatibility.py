from pathlib import Path
import sys,json
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'apps/api'))
from app.config import Settings
from app.delivery_inputs import inspect_input,PROFILE_1,PROFILE_2
from app.delivery_store import DeliveryStore
from app.delivery_plan import build_plan
from app.delivery_patch import patch_workbook,verify_output
from app.delivery_artifacts import make_artifacts
from app.delivery_execution import patch_fingerprint
out=R/'artifacts/verification/d04/compatibility';out.mkdir(parents=True,exist_ok=True)
store=DeliveryStore(out/'private-state');store.cleanup();rows=[]
source=(R/'samples/delivery-v3_2/delivery-rp01-rp02.xlsx').read_bytes()
for tag,profile,targets in [('RP01',PROFILE_1,['B2','B3']),('RP02',PROFILE_2,['F3'])]:
 job=store.create('synthetic-owner',source,inspect_input('synthetic.xlsx',source,Settings()),'compatibility-'+tag+'-'+__import__('uuid').uuid4().hex)
 policy={'profile':profile,'sheet':'검증','targets':targets,'role':'AMOUNT','confirmed':True,'anchor':'F2','anchor_formula':'=ROUND(C2*D2*(1-E2),0)'}
 plan=build_plan(job,policy)
 repaired=patch_workbook(source,job['snapshot'],plan)
 verification=verify_output(source,repaired,plan,Settings())
 package=make_artifacts(job,plan,repaired,verification,compatibility_bootstrap=True)
 for k,v in package['artifacts'].items():
  suffix='.html' if k=='VERIFICATION_HTML' else '.xlsx'
  (out/f'{tag}-{k}{suffix}').write_bytes(v['data'])
 (out/f'{tag}-manifest.json').write_text(json.dumps(package['manifest'],ensure_ascii=False,indent=2),encoding='utf-8')
 rows.append({'profile':tag,'source_hash':plan['source_hash'],'plan_digest':plan['digest'],'output_hash':verification['output_hash'],'files':package['manifest']['files'],'ready_published':False})
(out/'inputs.json').write_text(json.dumps({'patch_fingerprint':patch_fingerprint(),'rows':rows},ensure_ascii=False,indent=2),encoding='utf-8')
print('Actual patch, post-calculation and three artifacts created for Excel compatibility verification; not published READY.')
