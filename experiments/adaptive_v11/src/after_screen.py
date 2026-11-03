import json,subprocess,sys,time,os
from pathlib import Path
R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
os.sched_setaffinity(0,{14,15})
while not (R/'logs/screen45_v2/results.json').exists()or len(json.loads((R/'logs/screen45_v2/results.json').read_text()))<80:time.sleep(1)
subprocess.run([sys.executable,str(R/'src/analysis.py'),'screen45_v2'],cwd=ROOT,check=True)
while not (R/'artifacts/current_modular/COMPILED.json').exists():time.sleep(1)
s=json.loads((R/'SCREEN45_V2.json').read_text());s['name']='current45';s['cases']={k:v for k,v in s['cases'].items()if k in ['anti220','grid180','equal180','huge10000']};s['variants']={k:v for k,v in s['variants'].items()if k in ['v4','v10']};s['variants']['current']=dict(binary='experiments/adaptive_v11/artifacts/current_modular/candidate')
(R/'CURRENT45.json').write_text(json.dumps(s,indent=2))
with (R/'logs/current45.output').open('x')as f:subprocess.run([sys.executable,str(R/'src/run_instrumented.py'),str(R/'CURRENT45.json')],cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,check=True)
subprocess.run([sys.executable,str(R/'src/analysis.py'),'current45'],cwd=ROOT,check=True)
(R/'SCREEN_STATUS.json').write_text(json.dumps(dict(stage='screens_complete'),indent=2))
