from pathlib import Path
import sys,json,hashlib,math
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'apps/api'))
from app.delivery_calculation import calculate,engine_fingerprint
oracle=json.loads((R/'samples/delivery-v3_2/reference-cases.json').read_text(encoding='utf-8'))
reference=json.loads((R/'artifacts/verification/d03/excel-reference.json').read_text(encoding='utf-8-sig'))
assert reference['source_sha256']==hashlib.sha256((R/'samples/delivery-v3_2/reference-cases.json').read_bytes()).hexdigest()
rows=[]
def same(actual,expected):
 assert actual['type']==expected['type'],(actual['type'],expected['type'])
 assert math.isclose(actual['value'],expected['value'],rel_tol=1e-12,abs_tol=1e-12) if actual['type']=='number' else actual['value']==expected['value']
for case in oracle['cases']:
 cells={a:{'type':'text' if isinstance(v,str) else 'boolean' if isinstance(v,bool) else 'number','value':v,'style':'0'} for a,v in case['values'].items()}
 cells.update({a:{'type':'formula','value':v,'style':'0'} for a,v in case['formulas'].items()})
 expected=case['expected'];excel=next(row for row in reference['results'] if row['id']==case['id'])['values']
 result=calculate({'검증':cells})['values']['검증']
 for a,value in expected.items():same(excel[a],value);same(result[a],value)
 rows.append({'id':case['id'],'typed_result_count':len(expected),'excel_and_poi_match_policy':True})
 print('Verified:',case['id'],flush=True)
evidence={'status':'PASS','engine_fingerprint':engine_fingerprint(),'case_count':len(rows),'typed_result_count':sum(r['typed_result_count'] for r in rows),'excel_version':reference['version'],'excel_build':reference['build'],'oracle_sha256':reference['source_sha256'],'reference_sha256':hashlib.sha256((R/'artifacts/verification/d03/excel-reference.json').read_bytes()).hexdigest(),'rows':rows}
(R/'apps/api/app/delivery_reference.json').write_text(json.dumps(evidence,indent=2)+'\n',encoding='utf-8')
(R/'artifacts/verification/d03/reference-validation.json').write_text(json.dumps(evidence,indent=2)+'\n',encoding='utf-8')
print('Independent policy + installed Excel + actual isolated POI verified')
