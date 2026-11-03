#!/usr/bin/env python3
"""Within-(instance,seed) blocked A/B, all variants pinned to the identical CPU pair."""
import os,sys,json,time,subprocess,hashlib,re,random,queue,signal,fcntl
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
ROOT=Path(__file__).resolve().parents[3];R=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'task'));from validate_solution import validate
spec=json.loads(Path(sys.argv[1]).read_text());dest=R/'logs'/spec['name'];dest.mkdir(exist_ok=False)
cpus=spec.get('cpus',[8,9,10,11,12,13,14,15]);jobs=min(spec.get('jobs',4),len(cpus)//2);slots=queue.Queue()
for i in range(jobs):slots.put(cpus[2*i:2*i+2])
blocks=[(case,seed) for case in spec['cases'] for seed in spec['seeds']];random.Random(719).shuffle(blocks)
manifest={'spec':spec,'blocking':'All variants of each case/seed run sequentially on the same affinity; independently randomized order. Shared pair locks include compile/microbench jobs.','binaries':{k:hashlib.sha256((ROOT/v['binary']).read_bytes()).hexdigest() for k,v in spec['variants'].items()},'inputs':{k:hashlib.sha256((ROOT/v).read_bytes()).hexdigest() for k,v in spec['cases'].items()}}
(dest/'MANIFEST.json').write_text(json.dumps(manifest,indent=2));clean={k:v for k,v in os.environ.items() if k in ('PATH','HOME','LANG','LD_LIBRARY_PATH')}
def block(t):
 case,seed=t;aff=slots.get();os.sched_setaffinity(0,set(aff));lock=(R/f'cpu_{aff[0]}.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX);rows=[]
 labels=list(spec['variants']);random.Random(seed+sum(map(ord,case))).shuffle(labels)
 try:
  for label in labels:
   config=spec['variants'][label];prefix=dest/f'{case}_{seed}_{label}';inp=ROOT/spec['cases'][case];out=prefix.with_suffix('.solution.json');err=prefix.with_suffix('.stderr');res=prefix.with_suffix('.resource')
   env=clean|{'NT':'2','SEED':str(seed)}|config.get('env',{});start=time.monotonic();started=time.time();timeout=False
   cmd=['/usr/bin/time','-f','rss_kb=%M user=%U sys=%S','-o',str(res),'taskset','-c',','.join(map(str,aff)),str(ROOT/config['binary']),str(inp),str(out),str(spec['seconds'])]
   with err.open('w') as f:
    p=subprocess.Popen(cmd,env=env,stderr=f,stdout=subprocess.DEVNULL,start_new_session=True)
    try:rc=p.wait(timeout=spec['seconds']+10)
    except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait();rc=None;timeout=True
   wall=time.monotonic()-start;val=validate(inp,out);valid=not isinstance(val,str);txt=err.read_text();m=re.search(r'threads=(\d+)',txt);actual_nt=int(m[1]) if m else None;error=bool(re.search(r'error:|VERIFY|INVALID',txt))
   row={'started_unix':started,'ended_unix':time.time(),'case':case,'seed':seed,'variant':label,'rc':rc,'timeout':timeout,'wall':wall,'valid':valid,'objective':val if valid else None,'validation_error':None if valid else val,'actual_nt':actual_nt,'error_log':error,'success':rc==0 and not timeout and wall<=spec['seconds']+3 and valid and not error and actual_nt==2,'affinity':aff,'resource':res.read_text() if res.exists() else ''}
   prefix.with_suffix('.json').write_text(json.dumps(row,indent=2));rows.append(row);print(case,seed,label,round(row['objective'] or 0,6),row['success'],flush=True)
  return rows
 finally:fcntl.flock(lock,fcntl.LOCK_UN);lock.close();slots.put(aff)
rows=[]
with ThreadPoolExecutor(max_workers=jobs) as pool:
 for f in as_completed([pool.submit(block,t) for t in blocks]):
  rows+=f.result();(dest/'results.json').write_text(json.dumps(rows,indent=2))
