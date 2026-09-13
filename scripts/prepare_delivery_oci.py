import hashlib, importlib.metadata as md, json, subprocess, sys, tomllib
from pathlib import Path
import httpx

R=Path(__file__).resolve().parents[1]
O=R/'artifacts/verification/d08-hosted/image';O.mkdir(parents=True,exist_ok=True)
import shutil
GC=shutil.which("gcloud.cmd") or shutil.which("gcloud")
assert GC, "gcloud is required"
HOST='asia-northeast3-docker.pkg.dev'
REPO='workbookcare-beta/workbookcare-images/workbookcare-api'
DIGEST='sha256:e57d3782741461d315b55770b1c45e4ecff2d1981535831d9b50f0b1b40343db'
def save(name,v): (O/name).write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
token=subprocess.run([GC,'auth','print-access-token'],capture_output=True,text=True,check=True).stdout.strip()
with httpx.Client(auth=('oauth2accesstoken',token),timeout=60,follow_redirects=True) as c:
 headers={'Accept':'application/vnd.oci.image.index.v1+json, application/vnd.docker.distribution.manifest.list.v2+json, application/vnd.docker.distribution.manifest.v2+json, application/vnd.oci.image.manifest.v1+json'}
 r=c.get(f'https://{HOST}/v2/{REPO}/manifests/{DIGEST}',headers=headers)
 r.raise_for_status();assert 'sha256:'+hashlib.sha256(r.content).hexdigest()==DIGEST
 index=r.json();selected=next(m for m in index['manifests'] if m.get('platform')=={'architecture':'amd64','os':'linux'})
 r=c.get(f'https://{HOST}/v2/{REPO}/manifests/{selected["digest"]}',headers=headers);r.raise_for_status()
 assert 'sha256:'+hashlib.sha256(r.content).hexdigest()==selected['digest']
 manifest=r.json();save('base-manifest.json',manifest)
 r=c.get(f'https://{HOST}/v2/{REPO}/blobs/{manifest["config"]["digest"]}');r.raise_for_status();save('base-config.json',r.json())
 print(json.dumps({'base_os':r.json()['os'],'architecture':r.json()['architecture'],'user':r.json()['config'].get('User'),'base_layers':len(manifest['layers'])}),flush=True)
del token
with httpx.Client(follow_redirects=True,timeout=120) as c:
 r=c.get('https://api.adoptium.net/v3/assets/latest/17/hotspot',params={'architecture':'x64','image_type':'jre','os':'linux','vendor':'eclipse'});r.raise_for_status()
 asset=r.json()[0];p=asset['binary']['package'];save('java-source.json',{'version':asset['version']['semver'],'url':p['link'],'sha256':p['checksum']})
 dest=O/'java-linux.tar.gz'
 if not dest.exists():
  with c.stream('GET',p['link']) as stream:
   stream.raise_for_status()
   with dest.open('wb') as f:
    for chunk in stream.iter_bytes():f.write(chunk)
 assert hashlib.sha256(dest.read_bytes()).hexdigest()==p['checksum']
 print('Official Linux Java archive checksum verified',flush=True)
deps=tomllib.loads((R/'apps/api/pyproject.toml').read_text())['project']['dependencies']
import re
pinned=[]
for dep in deps:
 name=re.match(r'[\w-]+',dep)[0];extra='[standard]' if name=='uvicorn' else ''
 pinned.append(name+extra+'=='+md.version(name))
save('runtime-requirements.json',pinned)
argv=[sys.executable,'-m','pip','download','--dest',str(O/'wheels'),'--platform','manylinux2014_x86_64','--platform','manylinux_2_28_x86_64','--python-version','312','--implementation','cp','--abi','cp312','--only-binary=:all:',*pinned]
p=subprocess.run(argv,capture_output=True,text=True)
print(json.dumps({'command':'pip download pinned runtime Linux cp312 wheels','exit_code':p.returncode}),flush=True)
if p.returncode:print(p.stdout[-2000:]+p.stderr[-2000:]);raise SystemExit(p.returncode)
save('wheel-hashes.json',{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (O/'wheels').glob('*.whl')})
print('Linux image inputs prepared',flush=True)
