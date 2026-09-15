from pathlib import Path
import json,subprocess,os,hashlib
import httpx
from urllib.parse import urlparse
R=Path('C:/Users/JinwonLee/project/ExcelSaaS');S=Path('C:/Users/JinwonLee/project/DigitalTwin/.tmp/workbookcare-flow01');O=S/'web-release'
b=json.loads((O/'baseline.json').read_text());c=json.loads((O/'upload.json').read_text());result={}
for label,version in [('existing',b['worker']),('candidate',c['worker'])]:
 p=subprocess.run(['npx.cmd','--offline','--no-install','wrangler','versions','view',version,'--json','--config','infra/cloudflare/wrangler.jsonc'],cwd=R,env={**os.environ,'WRANGLER_SEND_METRICS':'false','CI':'1'},capture_output=True,text=True,encoding='utf-8',errors='replace')
 assert p.returncode==0,'read-only version lookup failed'
 bindings=json.loads(p.stdout)['resources']['bindings']
 flags=[{k:v for k,v in x.items() if k in ['name','type','text']} for x in bindings if x.get('name') in ['FORMULA_AUDIT_ENABLED','DELIVERY_BETA_ENABLED']]
 result[label]={'version':version,'flags':flags,'binding_hash':hashlib.sha256(json.dumps(bindings,sort_keys=True).encode()).hexdigest()}
assert result['existing']['binding_hash']==result['candidate']['binding_hash']==b['binding_hash']
access=[]
for path in ['/','/api/v1/scans','/api/v1/formula-audits','/api/v1/delivery']:
 r=httpx.get('https://workbookcare-beta.wonderlogic-studio.workers.dev'+path,follow_redirects=False,timeout=30)
 item={'path':path,'status':r.status_code,'existing_access':urlparse(r.headers.get('location','')).hostname=='old-breeze-11c7.cloudflareaccess.com'}
 assert item['status']==302 and item['existing_access'];access.append(item)
result['anonymous_access']=access;result['all_bindings_identical']=True;result['mutation_performed']=False
(O/'private-scope-proof.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result))
