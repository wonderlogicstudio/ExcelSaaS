"""Reviewed one-shot operational preflight and approved exact traffic transition."""
import runpy,sys
from pathlib import Path
sys.argv=['deploy_api.py','image']
d=runpy.run_path(str(Path(__file__).with_name('deploy_api.py')))
d['g'].__globals__['phase']='guarded_traffic'
b=d['read']('baseline.json');live=d['read']('live.json');stage=d['read']('stage.json');proof=d['read']('linux-runtime.json')
assert proof['revision']==stage['revision']==live['verified_image_revision']
assert stage['image']==live['image']
assert all(x['reference_cases']==20 and x['repair_profiles']==2 and x['artifacts']==6 for x in proof['checks'])
s=d['service']()
assert d['invariant'](s)==b['invariant'] and d['iam']()==b['iam']
assert any(t.get('revisionName')==b['revision'] and t.get('percent')==100 for t in s['status']['traffic'])
v=d['g']('run','revisions','describe',live['revision'],'--region',d['REGION'])
c=v['spec']['containers'][0];conditions={x['type']:x['status'] for x in v['status']['conditions']}
assert c['image']==live['image']
assert conditions.get('Ready')=='True' and conditions.get('ContainerHealthy')=='True'
assert c['startupProbe']['failureThreshold']==3
assert {x['name']:x.get('value') for x in c['env']}['DELIVERY_RUNTIME_VERIFY']=='false'
assert d['payment_off'](s)
d['save']('traffic-preflight.json',{'status':'PASS','revision':live['revision'],'image':live['image'],'private_iam_unchanged':True,'invariant_unchanged':True,'old_traffic_100':True,'runtime_verify':False,'startup_probe_failure_threshold':3,'linux_proof_matches':True,'unused_helper_phase':'traffic'})
d['g']('run','services','update-traffic',d['SERVICE'],'--region',d['REGION'],'--to-revisions',live['revision']+'=100','--remove-tags','horizontal01')
print('Guarded exact traffic transition completed.')
