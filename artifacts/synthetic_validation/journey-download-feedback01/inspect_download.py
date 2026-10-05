import json,hashlib,zipfile,xml.etree.ElementTree as ET
from pathlib import Path
root=Path(r'C:\Users\JinwonLee\project\ExcelSaaS')
source=root/'artifacts/synthetic_validation/monthly-repair-flow06/stage3/monthly-rp03-supported-6sheet.xlsx'
output=Path(r'C:\Users\JinwonLee\Downloads\workbookcare_repaired_b14aa3f6-e157-43b5-a4e4-6ccb28f062d1.xlsx')
ns={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
def cells(path):
 with zipfile.ZipFile(path) as z:
  result={n:{c.attrib['r']:ET.tostring(c,encoding='unicode') for c in ET.fromstring(z.read(n)).findall('.//s:c',ns)} for n in z.namelist() if n.startswith('xl/worksheets/sheet') and n.endswith('.xml')}
  target=ET.fromstring(z.read('xl/worksheets/sheet1.xml')).find('.//s:c[@r="N18"]',ns)
  return result,{'formula':target.findtext('s:f',namespaces=ns),'cached_value':target.findtext('s:v',namespaces=ns)}
a,b=cells(source);c,d=cells(output)
changed=[f'{s}:{cell}' for s in a for cell in set(a[s])|set(c[s]) if a[s].get(cell)!=c[s].get(cell)]
assert hashlib.sha256(source.read_bytes()).hexdigest()=='c5e4589ca19ca892a005d92b71101aa1abbf7e1ffdb04d97b9b808cc1a617dab'
assert d['formula']=="'M10'!B16-'M10'!B15" and float(d['cached_value'])==-5
business_changes=[]
cache_updates=[]
for s in a:
 for address in set(a[s])|set(c[s]):
  old=ET.fromstring(a[s][address]);new=ET.fromstring(c[s][address])
  if old.find('s:f',ns) is not None and new.find('s:f',ns) is not None and old.findtext('s:f',namespaces=ns)==new.findtext('s:f',namespaces=ns):
   if old.findtext('s:v',namespaces=ns)!=new.findtext('s:v',namespaces=ns):cache_updates.append(f'{s}:{address}')
   for node in (old,new):
    value=node.find('s:v',ns)
    if value is not None:node.remove(value)
  if ET.tostring(old)!=ET.tostring(new):business_changes.append(f'{s}:{address}')
assert business_changes==['xl/worksheets/sheet1.xml:N18'],business_changes
print(json.dumps({'status':'PASS','source_hash_preserved':True,'before':b,'after':d,'changed_cells_including_cache':changed,'business_changes':business_changes,'unchanged_formula_cache_updates':cache_updates,'repair_sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'scope':'OOXML read only; cached result not independent Excel recalculation','remaining_artifacts':'not received'},ensure_ascii=False))