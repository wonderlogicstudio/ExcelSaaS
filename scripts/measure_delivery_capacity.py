"""Measure real local comparison child and report limits; rejected cases are not PASS."""
from pathlib import Path
import base64,json,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'apps/api'))
from app.comparison_process import run_comparison
from app.delivery_artifact_process import make_comparison_artifacts
from app.errors import WorkbookCareError
OUT=ROOT/'artifacts/verification/d08';OUT.mkdir(parents=True,exist_ok=True);rows=[]
for count in [1000,5000,20000]:
    raw=('ID,amount\r\n'+''.join(f'K{i:05d},{i}\r\n' for i in range(1,count+1))).encode()
    criteria={'period':'SYNTHETIC','amount_meaning':'total','currency':'KRW','unit':'KRW_WON'}
    side={'sheet':'CSV','range':f'A1:B{count+1}','header_row':1,'key_columns':['A'],'amount_column':'B','exclusions':[],'criteria':criteria}
    spec={'A':side,'B':side,'policy':{'confirmed':True,**criteria,'normalization':'NONE','tolerance_krw':'0'}}
    message={'action':'compare','sources':{s:{'filename':'synthetic.csv','file_base64':base64.b64encode(raw).decode()} for s in ['A','B']},'spec':spec}
    started=time.monotonic();row={'rows_per_source':count,'source_bytes_each':len(raw),'expected_groups':count,'expected_known_total':str(count*(count+1)//2)}
    try:
        model=run_comparison(message)
        assert model['summary']['group_count']==count and model['summary']['known_amount_totals']=={'A':row['expected_known_total'],'B':row['expected_known_total']}
        row.update(comparison='PASS',comparison_seconds=round(time.monotonic()-started,3))
        package=make_comparison_artifacts(model,{'id':'synthetic-capacity','expires':time.time()+120})
        row.update(report='PASS',file_bytes={k:v['bytes'] for k,v in package['manifest']['files'].items()})
    except WorkbookCareError as error:
        row.update(status='LIMIT_REJECTED_NOT_SUPPORTED_CAPACITY',error_code=error.code,report=row.get('report','NOT_COMPLETED'))
    row['seconds']=round(time.monotonic()-started,3);rows.append(row)
    (OUT/'capacity.json').write_text(json.dumps({'kind':'ACTUAL_WINDOWS_CHILD_PROCESS_CAPACITY_MEASUREMENT_NOT_HOSTED_LOAD_TEST','cases':rows},indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(row),flush=True)
