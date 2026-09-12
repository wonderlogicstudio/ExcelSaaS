"""Create deterministic synthetic files for the actual product pipeline, not ready-made outputs."""
from pathlib import Path
from io import BytesIO,StringIO
from datetime import datetime
from zipfile import ZipFile,ZipInfo,ZIP_DEFLATED
import csv,json,hashlib
from openpyxl import Workbook

R=Path(__file__).resolve().parents[1];out=R/'samples/delivery-v3_2';data=json.loads((out/'comparison-reference.json').read_text(encoding='utf-8'))


def file_bytes(rows,kind):
 values=[['거래번호','금액']]+[[r['key'],r['amount']] for r in rows]
 if kind=='csv':
  stream=StringIO(newline='');csv.writer(stream).writerows(values);return stream.getvalue().encode('utf-8-sig')
 book=Workbook();sheet=book.active;sheet.title='명세'
 book.properties.creator='WorkbookCare synthetic fixture';book.properties.created=book.properties.modified=datetime(2026,9,13)
 for row in values:
  sheet.append(row)
  for cell in sheet[sheet.max_row]:
   if isinstance(cell.value,str):cell.data_type='s'
 stream=BytesIO();book.save(stream);book.close();stable=BytesIO()
 with ZipFile(BytesIO(stream.getvalue())) as a,ZipFile(stable,'w') as b:
  for name in sorted(a.namelist()):
   entry=ZipInfo(name,(2026,9,13,0,0,0));entry.compress_type=ZIP_DEFLATED;b.writestr(entry,a.read(name))
 return stable.getvalue()


if __name__=='__main__':
 files={};pairs=[]
 cases={'baseline':{'A':data['baseline']['A'],'B':data['baseline']['B']},'equal':{'A':[{'key':'0001','amount':'0'},{'key':'0002','amount':'100'}],'B':[{'key':'0001','amount':'0'},{'key':'0002','amount':'100'}]},'large':{'A':[{'key':'K','amount':'10000000000000001'}],'B':[{'key':'K','amount':'10000000000000000'}]}}
 for tag,pair in cases.items():
  for kind in ['csv','xlsx'] if tag=='baseline' else ['csv']:
   hashes=[]
   for side,rows in pair.items():
    name=f'comparison-{tag}-{side}.{kind}';payload=file_bytes(rows,kind);(out/name).write_bytes(payload);h=hashlib.sha256(payload).hexdigest();hashes.append(h);files[name]=h
   pairs.append({'case':tag,'format':kind,'A':hashes[0],'B':hashes[1]})
 manifest={'kind':'DETERMINISTIC_SYNTHETIC_PRODUCT_INPUTS','files':files,'pairs':pairs,'expected':{'baseline':data['expected']['summary'],'equal':{'MATCHED':2,'difference_groups':0},'large':{'delta':'1','A':'10000000000000001','B':'10000000000000000'}}}
 (out/'comparison-inputs.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
 (R/'apps/api/app/comparison_synthetic_sources.json').write_text(json.dumps({'pairs':pairs},indent=2)+'\n',encoding='utf-8',newline='\n')
 print('Created deterministic synthetic comparison inputs and fixed expected metadata')
