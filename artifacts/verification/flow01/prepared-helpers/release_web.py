from pathlib import Path
import hashlib,json,os,re,subprocess,sys
import httpx
from urllib.parse import urlparse
R=Path(r'C:\Users\JinwonLee\project\ExcelSaaS')
O=Path('C:/Users/JinwonLee/project/DigitalTwin/.tmp/workbookcare-flow01/web-release');O.mkdir(parents=True,exist_ok=True)
phase=sys.argv[1]
env={**os.environ,'WRANGLER_SEND_METRICS':'false','CI':'1','CLOUDSDK_CORE_DISABLE_PROMPTS':'1'}
def sha(x):return hashlib.sha256(json.dumps(x,sort_keys=True).encode()).hexdigest()
def save(name,x):(O/(name+'.json')).write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
def read(name):return json.loads((O/(name+'.json')).read_text())
def run(args,label,parse=False,extra=None):
 p=subprocess.run(args,cwd=R,env=extra or env,capture_output=True,text=True,encoding='utf-8',errors='replace')
 item={'phase':phase,'command':label,'exit_code':p.returncode}
 with (O/'commands.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(item)+'\n')
 print(json.dumps(item),flush=True)
 if p.returncode: print('Provider error codes:',re.findall(r'\[code: (\d+)\]',p.stdout+p.stderr));raise SystemExit(p.returncode)
 return json.loads(p.stdout) if parse else p.stdout
def w(*args,parse=False):return run(['npx.cmd','--offline','--no-install','wrangler',*args,'--config','infra/cloudflare/wrangler.jsonc'],'wrangler '+' '.join(args),parse)
def g(*args):return run([r'C:\Users\JinwonLee\AppData\Local\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd',*args,'--project','workbookcare-beta','--format=json','--quiet'],'gcloud '+' '.join(args),True)
def worker():
 d=w('deployments','list','--json',parse=True);d=d['deployments'] if isinstance(d,dict) else d
 v=max(d,key=lambda x:x['created_on'])['versions'];assert len(v)==1 and v[0]['percentage']==100
 return v[0]['version_id']
def bindings(v):return w('versions','view',v,'--json',parse=True)['resources']['bindings']
def api():
 s=g('run','services','describe','workbookcare-api-beta','--region','asia-northeast3')
 iam=g('run','services','get-iam-policy','workbookcare-api-beta','--region','asia-northeast3')
 assert not any(m in ['allUsers','allAuthenticatedUsers'] for b in iam.get('bindings',[]) for m in b.get('members',[]))
 return {'revision':s['status']['latestReadyRevisionName'],'spec_hash':sha(s['spec']),'traffic_hash':sha(s['status']['traffic']),'iam_hash':sha(iam)}
def access():
 results=[]
 for p in ['/','/precision-verification','/compare','/automation','/help','/orders','/api/v1/scans','/api/v1/formula-audits','/api/v1/delivery']:
  r=httpx.get('https://workbookcare-beta.wonderlogic-studio.workers.dev'+p,follow_redirects=False,timeout=30)
  ok=r.status_code==302 and urlparse(r.headers.get('location','')).hostname=='old-breeze-11c7.cloudflareaccess.com'
  assert ok,p;results.append({'path':p,'status':r.status_code,'existing_access':ok})
 return results
if phase=='baseline':
 assert not (O/'baseline.json').exists();v=worker();assert v=='1fa2992b-c75d-400b-8acc-14dd484c7a40'
 a=api();assert a['revision']==json.loads((O.parent/'release/live.json').read_text())['revision']
 save('baseline',{'worker':v,'binding_hash':sha(bindings(v)),'api':a,'access':access()})
elif phase=='build':
 e={**env,'VITE_PRODUCT_ENV':'hosted_beta','VITE_API_BASE_URL':'/api','VITE_FORMULA_AUDIT_HOSTED_BETA_ENABLED':'true','VITE_FORMULA_AUDIT_INTERNAL_BETA_ENABLED':'false','VITE_FEEDBACK_CAPTURE_ENABLED':'false','VITE_HOSTED_BETA_FEEDBACK_ENABLED':'false','VITE_DELIVERY_BETA_ENABLED':'true'}
 run(['npm.cmd','run','build','--workspace','@workbookcare/web','--','--mode','hosted_beta'],'npm build hosted beta',extra=e)
 save('web',{'flags':{k:v for k,v in e.items() if k.startswith('VITE_')},'assets':{p.relative_to(R).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in (R/'apps/web/dist').rglob('*') if p.is_file()}})
elif phase=='upload':
 b=read('baseline');assert worker()==b['worker'];assert api()==b['api']
 for p,h in read('web')['assets'].items():assert hashlib.sha256((R/p).read_bytes()).hexdigest()==h
 overrides=['--var','FORMULA_AUDIT_ENABLED:true','--var','DELIVERY_BETA_ENABLED:true']
 w('versions','upload','--dry-run','--keep-vars','--strict',*overrides)
 out=w('versions','upload','--keep-vars','--strict',*overrides,'--tag','flow01','--message','Approved FLOW-01 reduced intermediate actions; same private boundaries')
 v=re.search(r'Worker Version ID:\s*([a-f0-9-]{36})',out).group(1)
 assert sha(bindings(v))==b['binding_hash'];save('upload',{'worker':v,'all_bindings_equal':True})
elif phase=='deploy':
 b=read('baseline');v=read('upload')['worker'];assert worker()==b['worker'];assert sha(bindings(v))==b['binding_hash'];assert api()==b['api']
 w('versions','deploy',v+'@100','--yes','--message','Approved FLOW-01 repair flow')
 assert worker()==v;assert api()==b['api']
 save('live',{'worker':v,'rollback_worker':b['worker'],'all_bindings_equal':True,'api_unchanged':True,'access':access()})
else:raise SystemExit('unknown phase')
