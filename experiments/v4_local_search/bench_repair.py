import os,sys,json,time,subprocess,queue,hashlib,signal,random
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
R=Path(__file__).resolve().parent;ROOT=R.parents[1]
sys.path.insert(0,str(ROOT/'task'));from validate_solution import validate,Instance,OpenedOffice,validate_solution
name=sys.argv[1];seconds=float(sys.argv[2]);out=R/'logs'/name;out.mkdir(exist_ok=False)
source=R/'logs/development60_v1';spec=json.loads((source/'MANIFEST.json').read_text())['spec'];selection=sys.argv[3] if len(sys.argv)>3 else 'profit';jobs=[(c,b,k) for c in spec['cases'] for b in ['highs','scip'] for k in ([48,128] if selection=='peel' else [24,48])];random.Random(933).shuffle(jobs)
slots=queue.Queue()
for cpu in sorted(os.sched_getaffinity(0))[16:20]:slots.put(cpu)
(out/'MANIFEST.json').write_text(json.dumps({'source':str(source),'seconds':seconds,'jobs':jobs,'script_sha256':hashlib.sha256((R/'repair_mip.py').read_bytes()).hexdigest(),'purpose':'Fixed mature checkpoint; joint workers/offices; same model, both backends. Independent of full60 quality.'},indent=2))
def run(job):
 c,b,k=job;cpu=slots.get();p=out/f'{c}_{b}_{k}';dest=p.with_suffix('.json');err=p.with_suffix('.stderr');resource=p.with_suffix('.resource');inp=ROOT/spec['cases'][c];inc=source/f'{c}_301_base.solution.json';t=time.monotonic();rc=None
 try:
  env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1')
  cmd=['/usr/bin/time','-f','rss_kb=%M user=%U sys=%S','-o',str(resource),'taskset','-c',str(cpu),sys.executable,str(R/'repair_mip.py'),str(inp),str(inc),str(dest),'--backend',b,'--seconds',str(seconds),'--budget',str(k),'--selection',selection]
  with err.open('w') as f:
   process=subprocess.Popen(cmd,stdout=subprocess.DEVNULL,stderr=f,env=env,start_new_session=True)
   try:rc=process.wait(timeout=seconds+15)
   except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);process.wait()
  wall=time.monotonic()-t;d=json.loads(dest.read_text()) if dest.exists() else {};sol=d.get('solution');value=validate_solution(Instance.load(inp),[OpenedOffice.model_validate(x) for x in sol]) if sol is not None else 'missing output';valid=not isinstance(value,str)
  row={'case':c,'selection':selection,'backend':b,'budget':k,'rc':rc,'wall':wall,'valid':valid,'success':rc==0 and valid and wall<=seconds+3,'objective':value if valid else None,'resource':resource.read_text() if resource.exists() else '',**{z:v for z,v in d.items() if z not in ('solution','events','selected')}}
  return row
 finally:slots.put(cpu)
rows=[]
with ThreadPoolExecutor(max_workers=4) as pool:
 for f in as_completed([pool.submit(run,j) for j in jobs]):
  r=f.result();rows.append(r);(out/'results.json').write_text(json.dumps(rows,indent=2));print(len(rows),r['case'],r['backend'],r['budget'],r.get('gain'),r.get('cuts'),r['success'],flush=True)
