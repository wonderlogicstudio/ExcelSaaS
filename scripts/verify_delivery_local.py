"""Owned local-only synthetic UI runner. Never deploys or restarts existing services."""
from __future__ import annotations
import argparse
import os
import socket
import subprocess
import time
from pathlib import Path
import httpx

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--stage', choices=['d07','d07-comparison','d07-operations','d08','d08-comparison'], required=True)
parser.add_argument('--script', choices=['verify-payment-delivery.mjs','verify-comparison-output.mjs','verify-delivery-operations.mjs','verify-delivery-holdout.mjs'], required=True)
args = parser.parse_args()
for port in [8189,5189]:
    with socket.socket() as sock:
        if sock.connect_ex(('127.0.0.1',port)) == 0:
            raise RuntimeError('Chosen local verification port is already occupied')
env={**os.environ,'APP_ENV':'internal_beta','PAYMENT_MODE':'LOCAL_CONTRACT','FORMULA_PATTERN_AUDIT_ENABLED':'true','HOSTED_BETA_FORMULA_AUDIT_ENABLED':'false','CORS_ORIGINS':'http://127.0.0.1:5189','PYTHONDONTWRITEBYTECODE':'1','DELIVERY_BETA_ENABLED':'true','DELIVERY_DATA_DIR':str(ROOT/f'artifacts/verification/{args.stage}/private-state'),'DELIVERY_VERIFICATION_STAGE':args.stage,'VITE_DELIVERY_BETA_ENABLED':'true','VITE_API_BASE_URL':'http://127.0.0.1:8189','VITE_PRODUCT_ENV':'hosted_beta','VITE_FORMULA_AUDIT_HOSTED_BETA_ENABLED':'true','VITE_FORMULA_AUDIT_INTERNAL_BETA_ENABLED':'false','VITE_HOSTED_BETA_FEEDBACK_ENABLED':'false','VITE_FEEDBACK_CAPTURE_ENABLED':'false'}
procs=[]
try:
    procs.append(subprocess.Popen([str(ROOT/'apps/api/.venv/Scripts/python.exe'),'-m','uvicorn','app.main:app','--host','127.0.0.1','--port','8189','--no-access-log'],cwd=ROOT/'apps/api',env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL))
    procs.append(subprocess.Popen(['npm.cmd','run','dev','--workspace','@workbookcare/web','--','--host','127.0.0.1','--port','5189'],cwd=ROOT,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL))
    for url in ['http://127.0.0.1:8189/health','http://127.0.0.1:5189']:
        for _ in range(80):
            try:
                if httpx.get(url,timeout=1).status_code==200: break
            except httpx.HTTPError: pass
            time.sleep(.25)
        else: raise RuntimeError('Local test server did not become ready')
    result=subprocess.run(['node','scripts/'+args.script],cwd=ROOT,env=env)
    raise SystemExit(result.returncode)
finally:
    for proc in procs:
        subprocess.run(['taskkill','/PID',str(proc.pid),'/T','/F'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
