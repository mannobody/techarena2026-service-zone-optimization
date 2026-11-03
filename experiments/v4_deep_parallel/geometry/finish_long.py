import json,time,sys,subprocess,os
from pathlib import Path
R=Path(__file__).resolve().parent
while True:
 p=R/'logs/v4_anti600/results.json'
 if p.exists() and len(json.loads(p.read_text()))==1:break
 time.sleep(3)
os.sched_setaffinity(0,{6,7})
subprocess.run([sys.executable,str(R/'anytime_summary.py')],check=True)
subprocess.run([sys.executable,str(R/'post_long.py'),'mature600_tail','1','0,7,15','anti','post_tail'],check=True)
print('GEOMETRY ALL EXPERIMENTS COMPLETE',flush=True)
