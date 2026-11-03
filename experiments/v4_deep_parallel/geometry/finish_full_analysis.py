import json,time,sys,subprocess,os
from pathlib import Path
R=Path(__file__).resolve().parent
while True:
 p=R/'logs/full60_dev/results.json'
 if p.exists() and len(json.loads(p.read_text()))==48:break
 time.sleep(2)
os.sched_setaffinity(0,{0})
for case in ['cluster','multiskill','large']:
 subprocess.run(['/tmp/szo-research-venv/bin/python',str(R/'analyze_geometry.py'),case],check=True)
subprocess.run([sys.executable,str(R/'summarize.py'),'full60_dev'],check=True,stdout=(R/'logs/full60_summary.stdout').open('w'))
(R/'CPU0_5_RELEASED.json').write_text(json.dumps(dict(finished=time.time(),runs=48),indent=2))
print('CPU0..5 released',flush=True)
