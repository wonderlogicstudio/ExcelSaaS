from pathlib import Path
import sys,subprocess,tempfile,shutil,os,json
R=Path(__file__).resolve().parents[1];S=Path(__file__).parent;sys.path.insert(0,str(R/'apps/api'))
from app.delivery_calculation import ENGINE_DIR,_policy
from app.delivery_process import process_limits
source=ENGINE_DIR/'SandboxProbe.java';assert source.is_file()
compiled=subprocess.run(['javac','-d',str(ENGINE_DIR/'classes'),str(source)],capture_output=True,text=True)
assert compiled.returncode==0
with tempfile.TemporaryDirectory(prefix='workbookcare-sandbox-proof-') as temp:
 root=Path(temp);outside=root/'outside.txt';outside.write_text('SYNTHETIC_PRIVATE_ONLY');scratch=root/'scratch';scratch.mkdir()
 java=Path(shutil.which('java'));policy=scratch/'policy';policy.write_text(_policy(scratch,java),encoding='utf-8')
 p=subprocess.Popen([str(java),'-Xmx128m','-XX:MaxMetaspaceSize=96m','-XX:CompressedClassSpaceSize=32m','-XX:ReservedCodeCacheSize=32m','-XX:MaxDirectMemorySize=16m','-XX:ActiveProcessorCount=1','-Djava.security.manager','-Djava.security.policy=='+str(policy),'-cp',str(ENGINE_DIR/'classes'),'SandboxProbe',str(outside)],cwd=scratch,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL)
 with process_limits(p):out,_=p.communicate(timeout=15)
 assert p.returncode==0,out.decode();lines=out.decode().splitlines();assert len(lines)==4 and all(x.endswith(':DENIED') for x in lines)
 evidence={'kind':'ACTUAL_JAVA_SECURITY_MANAGER_AND_OS_PROCESS_LIMIT','status':'PASS','denied_operations':lines,'java_major':17,'platform':os.name,'customer_workbooks_used':False}
 (R/'artifacts/verification/d03/sandbox.json').write_text(json.dumps(evidence,indent=2)+'\n',encoding='utf-8')
 print(json.dumps(evidence))
