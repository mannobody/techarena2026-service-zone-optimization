#!/usr/bin/env python3
"""Reproducible paired runs; explicit NT=2, exit/timeout/validator audited separately."""
import os,sys,json,time,subprocess,hashlib,re,random,queue,threading,signal,fcntl
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
ROOT=Path(__file__).resolve().parents[3]; R=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'task'))
from validate_solution import validate
spec=json.loads(Path(sys.argv[1]).read_text()); dest=R/'logs'/spec['name'];dest.mkdir(exist_ok=False)
cpus=sorted(os.sched_getaffinity(0))[spec.get('cpu_offset',0):]; jobs=min(spec.get('jobs',6),max(1,len(cpus)//2))
slots=queue.Queue()
for i in range(jobs): slots.put(cpus[2*i:2*i+2])
clean={k:v for k,v in os.environ.items() if k in ('PATH','HOME','LANG','LD_LIBRARY_PATH')}
tasks=[(case,seed,label,config) for case in spec['cases'] for seed in spec['seeds'] for label,config in spec['variants'].items()]
if spec.get('pairs'): tasks=[t for t in tasks if [t[0],t[1]] in spec['pairs']]
random.Random(691).shuffle(tasks)
manifest={'spec':spec,'affinity':cpus,'jobs':jobs,'binaries':{k:hashlib.sha256((ROOT/v['binary']).read_bytes()).hexdigest() for k,v in spec['variants'].items()},'inputs':{k:hashlib.sha256((ROOT/v).read_bytes()).hexdigest() for k,v in spec['cases'].items()}}
(dest/'MANIFEST.json').write_text(json.dumps(manifest,indent=2))
def run(t):
 case,seed,label,config=t; name=f'{case}_{seed}_{label}'; prefix=dest/name
 inp=ROOT/spec['cases'][case];out=prefix.with_suffix('.solution.json');err=prefix.with_suffix('.stderr');res=prefix.with_suffix('.resource')
 env=clean|{'NT':'2','SEED':str(seed)}|config.get('env',{})
 affinity=slots.get(); os.sched_setaffinity(0,set(affinity)); lock=(R/f'cpu_{affinity[0]}.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX);start=time.monotonic();started=time.time();timeout=False
 cmd=['/usr/bin/time','-f','rss_kb=%M user=%U sys=%S','-o',str(res),'taskset','-c',','.join(map(str,affinity)),str(ROOT/config['binary']),str(inp),str(out),str(spec['seconds'])]
 try:
  with err.open('w') as f:
   p=subprocess.Popen(cmd,env=env,stderr=f,stdout=subprocess.DEVNULL,start_new_session=True)
   try: rc=p.wait(timeout=spec['seconds']+10)
   except subprocess.TimeoutExpired: os.killpg(p.pid,signal.SIGKILL);p.wait();rc=None;timeout=True
  wall=time.monotonic()-start
  val=validate(inp,out); valid=not isinstance(val,str)
  text=err.read_text(); m=re.search(r'threads=(\d+)',text)
  actual_nt=int(m[1]) if m else None
  error=bool(re.search(r'error:|VERIFY|INVALID',text))
  row={'started_unix':started,'ended_unix':time.time(),'case':case,'seed':seed,'variant':label,'rc':rc,'timeout':timeout,'wall':wall,'valid':valid,'objective':val if valid else None,'validation_error':val if not valid else None,'actual_nt':actual_nt,'error_log':error,'success':rc==0 and not timeout and wall<=spec['seconds']+3 and valid and not error,'affinity':affinity,'resource':res.read_text() if res.exists() else ''}
  prefix.with_suffix('.json').write_text(json.dumps(row,indent=2));return row
 finally: fcntl.flock(lock,fcntl.LOCK_UN);lock.close();slots.put(affinity)
rows=[]
with ThreadPoolExecutor(max_workers=jobs) as pool:
 for f in as_completed([pool.submit(run,t) for t in tasks]):
  row=f.result();rows.append(row);print(len(rows),len(tasks),row['case'],row['seed'],row['variant'],round(row['objective'] or 0,6),row['success'],flush=True)
  (dest/'results.json').write_text(json.dumps(rows,indent=2))
