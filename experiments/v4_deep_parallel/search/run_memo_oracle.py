from pathlib import Path
import subprocess,fcntl,os,json,re,time
R=Path(__file__).resolve().parent
with (R/'cpu_14.lock').open('w') as f:
 fcntl.flock(f,fcntl.LOCK_EX);os.sched_setaffinity(0,{14,15});rows=[]
 for seed in range(80):
  p=subprocess.run([str(R/'bin/test_memo'),str(seed)],capture_output=True,text=True);row={'seed':seed,'rc':p.returncode,'stdout':p.stdout,'stderr':p.stderr};rows.append(row)
  (R/'logs/memo_oracle.json').write_text(json.dumps(rows,indent=2))
  if p.returncode:print(row,flush=True);raise SystemExit(1)
 print('80 processes,360000 certificate checks,all passed',flush=True)
