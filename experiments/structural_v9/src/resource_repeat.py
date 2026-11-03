"""Diagnostic replication after primary finishes; never replaces primary data."""
import hashlib,json,os,subprocess,sys,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];ROOT=R.parents[1];os.sched_setaffinity(0,{14,15})
while json.loads((R/'CAMPAIGN_STATUS.json').read_text())['stage']!='complete':time.sleep(5)
freeze=json.loads((R/'FREEZE.json').read_text())
def check():
    for p,h in freeze['files'].items():assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h,p
check();(R/'RESOURCE_REPEAT_STATUS.json').write_text(json.dumps(dict(stage='running',started_unix=time.time())))
with (R/'logs/resource_repeat280.progress').open('x')as f:subprocess.run([sys.executable,str(R/'src/run.py'),str(R/'RESOURCE_REPEAT280.json')],cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,check=True)
with (R/'logs/resource_repeat280.summary.txt').open('x')as f:subprocess.run([sys.executable,str(R/'src/summarize.py'),'resource_repeat280'],cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,check=True)
check();(R/'RESOURCE_REPEAT_STATUS.json').write_text(json.dumps(dict(stage='complete',ended_unix=time.time())));print('resource diagnostic complete')
