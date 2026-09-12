"""Fault injection only into an explicitly isolated local synthetic verification directory."""
from pathlib import Path
import argparse,json,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'apps/api'))
from app.config import get_settings
from app.delivery_store import DeliveryStore
from app.delivery_operations import maintain
from app.payment_service import fixed_synthetic

p=argparse.ArgumentParser();p.add_argument('--job-id',required=True);p.add_argument('--action',choices=['expire-plan','expire-input','missing-artifact'],required=True);args=p.parse_args()
s=get_settings();assert s.app_env=='internal_beta' and s.payment_mode=='LOCAL_CONTRACT'
directory=Path(s.delivery_data_dir).resolve();allowed=ROOT/'artifacts/verification'
assert directory.is_relative_to(allowed.resolve()) and directory.parent.name in {'d07','d07-operations','d08'} and directory.name=='private-state'
store=DeliveryStore(directory)
with store.connection() as db:
 row=db.execute('SELECT owner FROM jobs WHERE id=?',(args.job_id,)).fetchone()
assert row
job=store.load(row['owner'],args.job_id);assert fixed_synthetic(job)
with store.connection() as db:
 if args.action=='expire-input':db.execute('UPDATE jobs SET expires=? WHERE id=?',(time.time()-1,job['id']))
 elif args.action=='expire-plan':
  state=job['state'];assert state.get('plan') and state['status'] not in {'RUNNING','READY'}
  state['plan']['expires_at']=time.time()-1
  db.execute('UPDATE jobs SET state=?,revision=revision+1 WHERE id=?',(json.dumps(state),job['id']))
 else:
  assert job['state']['status']=='READY'
  kind='CHANGES_XLSX' if job['product']=='APPROVED_REPAIR' else 'COMPARISON_REPORT_XLSX'
  assert db.execute('DELETE FROM delivery_artifacts WHERE job_id=? AND kind=?',(job['id'],kind)).rowcount==1
maintain(store)
print('Local synthetic fault applied. No PG or hosted operation.')
