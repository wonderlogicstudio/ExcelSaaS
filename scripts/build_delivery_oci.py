"""Build a Dockerless OCI delta on the existing private beta image. No credentials saved."""
import argparse, copy, gzip, hashlib, io, json, os, subprocess, tarfile, zipfile
from pathlib import Path, PurePosixPath
from urllib.parse import urljoin, urlparse
import httpx

R=Path(__file__).resolve().parents[1]
O=R/'artifacts/verification/d08-hosted/image'
REG='https://asia-northeast3-docker.pkg.dev'
REPO='workbookcare-beta/workbookcare-images/workbookcare-api'
API=REG+'/v2/'+REPO
import shutil
GC=shutil.which("gcloud.cmd") or shutil.which("gcloud")
assert GC, "gcloud is required"
def sha(b):return 'sha256:'+hashlib.sha256(b).hexdigest()
def save(name,v): (O/name).write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
parser=argparse.ArgumentParser();parser.add_argument('--push',action='store_true');args=parser.parse_args()
tarpath=O/'delivery-layer.tar';sources={}
def safe(name):
 p=PurePosixPath(name);assert not p.is_absolute() and '..' not in p.parts;return str(p)
with tarfile.open(tarpath,'w') as tar:
 def add(name,data,mode=0o644):
  name=safe(name);entry=tarfile.TarInfo(name);entry.size=len(data);entry.mode=mode;entry.mtime=0
  tar.addfile(entry,io.BytesIO(data))
 add('app/.wh..wh..opq',b'')
 add('usr/local/lib/python3.12/site-packages/.wh..wh..opq',b'')
 for p in sorted((R/'apps/api/app').rglob('*')):
  if p.is_file() and p.suffix in {'.py','.json','.html'} and '__pycache__' not in p.parts:
   data=p.read_bytes();sources[str(p.relative_to(R)).replace('\\','/')]=sha(data)
   add('app/app/'+p.relative_to(R/'apps/api/app').as_posix(),data)
 for p in sorted((R/'apps/api/engine').rglob('*')):
  if p.is_file() and p.suffix in {'.java','.json','.class','.jar'}:
   data=p.read_bytes();sources[str(p.relative_to(R)).replace('\\','/')]=sha(data)
   add('app/engine/'+p.relative_to(R/'apps/api/engine').as_posix(),data)
 for name in ['reference-cases.json','delivery-rp01-rp02.xlsx']:
  p=R/'samples/delivery-v3_2'/name;data=p.read_bytes();sources[p.relative_to(R).as_posix()]=sha(data)
  add('app/verification/'+name,data)
 wheels=json.loads((O/'wheel-hashes.json').read_text())
 for name,digest in sorted(wheels.items()):
  p=O/'wheels'/name;assert hashlib.sha256(p.read_bytes()).hexdigest()==digest
  with zipfile.ZipFile(p) as z:
   for member in z.infolist():
    if member.is_dir():continue
    dest=safe(member.filename)
    parts=PurePosixPath(dest).parts
    if '.data' in parts[0]:
     assert parts[1] in {'purelib','platlib','scripts','data','headers'}
     if parts[1] not in {'purelib','platlib'}:continue
     dest='/'.join(parts[2:])
    add('usr/local/lib/python3.12/site-packages/'+dest,z.read(member))
 java=json.loads((O/'java-source.json').read_text());assert sha((O/'java-linux.tar.gz').read_bytes())=='sha256:'+java['sha256']
 with tarfile.open(O/'java-linux.tar.gz','r:gz') as j:
  members=j.getmembers();prefix=members[0].name.split('/')[0]
  for member in members:
   rel=PurePosixPath(member.name).relative_to(prefix).as_posix()
   if rel=='.':continue
   safe(rel);entry=copy.copy(member);entry.name='opt/java/openjdk/'+rel;entry.uid=entry.gid=0;entry.uname=entry.gname='';entry.mtime=0
   if entry.issym():
    import posixpath
    resolved=posixpath.normpath(str(PurePosixPath(rel).parent/entry.linkname))
    assert not entry.linkname.startswith('/') and not resolved.startswith('../') and resolved!='..'
   assert entry.isfile() or entry.isdir() or entry.issym()
   tar.addfile(entry,j.extractfile(member) if entry.isfile() else None)
diff=sha(tarpath.read_bytes())
layer=O/'delivery-layer.tar.gz'
with tarpath.open('rb') as src,layer.open('wb') as dest,gzip.GzipFile(fileobj=dest,mode='wb',mtime=0,filename='') as z:
 while chunk:=src.read(1024**2):z.write(chunk)
config=json.loads((O/'base-config.json').read_text());config['rootfs']['diff_ids'].append(diff)
config['history'].append({'created':'2026-09-13T00:00:00Z','created_by':'WorkbookCare protected beta Dockerless verified runtime layer'})
config['created']='2026-09-13T00:00:00Z'
config['config']['Env']=[e for e in config['config']['Env'] if not e.startswith(('PATH=','JAVA_HOME=','DELIVERY_RUNTIME_VERIFY='))]+['PATH=/opt/java/openjdk/bin:/usr/local/bin:/usr/local/sbin:/usr/sbin:/usr/bin:/sbin:/bin','JAVA_HOME=/opt/java/openjdk','DELIVERY_RUNTIME_VERIFY=true']
configdata=json.dumps(config,separators=(',',':')).encode();(O/'config.json').write_bytes(configdata)
manifest=json.loads((O/'base-manifest.json').read_text());manifest['config']['digest']=sha(configdata);manifest['config']['size']=len(configdata)
manifest['layers'].append({'mediaType':'application/vnd.oci.image.layer.v1.tar+gzip','digest':sha(layer.read_bytes()),'size':layer.stat().st_size})
manifestdata=json.dumps(manifest,separators=(',',':')).encode();(O/'manifest.json').write_bytes(manifestdata)
evidence={'image':REG.removeprefix('https://')+'/'+REPO+'@'+sha(manifestdata),'source_sha256':sources,'java':java,'wheels':wheels,'layer_bytes':layer.stat().st_size,'base_user':config['config']['User'],'build':'local-oci-delta-no-docker-no-cloud-build','pushed':False}
save('build.json',evidence);print(json.dumps({'built_image':evidence['image'],'layer_bytes':evidence['layer_bytes']}),flush=True)
if args.push:
 token=subprocess.run([GC,'auth','print-access-token'],capture_output=True,text=True,check=True).stdout.strip()
 with httpx.Client(auth=('oauth2accesstoken',token),timeout=180,follow_redirects=True) as c:
  for file in [O/'config.json',layer]:
   digest=sha(file.read_bytes());r=c.head(API+'/blobs/'+digest)
   if r.status_code==200:continue
   assert r.status_code==404,r.status_code
   r=c.post(API+'/blobs/uploads/');r.raise_for_status();loc=urljoin(REG,r.headers['location']);assert urlparse(loc).hostname==urlparse(REG).hostname
   separator='&' if '?' in loc else '?'
   with file.open('rb') as f:r=c.put(loc+separator+'digest='+digest,content=f,headers={'Content-Type':'application/octet-stream','Content-Length':str(file.stat().st_size)})
   assert r.status_code in {201,202},r.status_code
   print('Verified layer uploaded to existing private registry',flush=True)
  tag='delivery-d08-'+sha(manifestdata).split(':')[1][:12]
  r=c.put(API+'/manifests/'+tag,content=manifestdata,headers={'Content-Type':manifest['mediaType']});r.raise_for_status()
  assert r.headers.get('docker-content-digest')==sha(manifestdata)
 evidence['pushed']=True;save('build.json',evidence);print('Private OCI image digest verified',flush=True)
