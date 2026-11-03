import sys,os,json,queue,subprocess,signal,time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
R=Path(__file__).resolve().parent;ROOT=R.parents[2];sys.path.insert(0,str(ROOT/'task'));from validate_solution import validate
cases=sys.argv[1].split(',');tag=sys.argv[2];dest=R/'logs'/tag;dest.mkdir(exist_ok=False);slots=queue.Queue();[slots.put(c) for c in [6,7]]
def run(case,kind,backend):
 cpu=slots.get();os.sched_setaffinity(0,{cpu});name=f'{case}_{kind}_{backend}';err=dest/f'{name}.stderr';stdout=dest/f'{name}.stdout';res=dest/f'{name}.resource';start=time.monotonic();rc=None;timeout=False
 try:
  with err.open('w') as e,stdout.open('w') as out:
   p=subprocess.Popen(['/usr/bin/time','-f','rss_kb=%M user=%U sys=%S','-o',str(res),'taskset','-c',str(cpu),'/tmp/szo-research-venv/bin/python',str(R/'mip_neighbor.py'),case,str(kind),backend,'20'],stderr=e,stdout=out,start_new_session=True,env={'PATH':os.environ['PATH'],'OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1'})
   try:rc=p.wait(timeout=35)
   except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait();timeout=True
  wall=time.monotonic()-start;result=R/'logs/mip_neighbors'/f'{name}.json';d=json.loads(result.read_text()) if result.exists() else {};sol=dest/f'{name}.solution.json';sol.write_text(json.dumps(d.get('solution',[])));v=validate(R/'inputs'/f'dev_{case}.json',sol);valid=not isinstance(v,str)
  row=dict(case=case,kind=kind,backend=backend,rc=rc,timeout=timeout,wall=wall,valid=valid,objective=v if valid else None,gain=d.get('gain'),conditional_optimal=d.get('conditional_optimal'),status=d.get('status'),success=rc==0 and not timeout and valid and wall<=23,affinity=[cpu],resource=res.read_text())
  (dest/f'{name}.json').write_text(json.dumps(row,indent=2));return row
 finally:slots.put(cpu)
rows=[]
with ThreadPoolExecutor(max_workers=2) as pool:
 for f in as_completed([pool.submit(run,c,k,b) for c in cases for k in [0,2] for b in ['highs','scip']]):
  r=f.result();rows.append(r);(dest/'results.json').write_text(json.dumps(rows,indent=2));print(len(rows),r,flush=True)
