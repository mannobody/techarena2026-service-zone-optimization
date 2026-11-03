import os,json,time,sys,subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'experiments/colgen'))
from test_models import validator
log=HERE/'logs/large30';log.mkdir(parents=True,exist_ok=True)
jobs=[(c,v,seed) for seed in (1,2) for c in ('huge0','huge1') for v in ('before_o2','candidate')]
def run(job):
 c,v,seed=job;inp=ROOT/'experiments/clustering/data'/(c+'.json');out=log/f'{c}_{v}_{seed}.solution.json';env=dict(os.environ,NT='2',SEED=str(seed),DBG='1');start=time.perf_counter()
 p=subprocess.run([str(HERE/'artifacts'/v),str(inp),str(out),'30'],env=env,capture_output=True,text=True,timeout=50);s=validator.validate(inp,out);(log/f'{c}_{v}_{seed}.stderr.txt').write_text(p.stderr)
 return dict(case=c,variant=v,seed=seed,limit=30,threads=2,wall=time.perf_counter()-start,score=s,error=s if isinstance(s,str) else None,returncode=p.returncode)
rows=[]
with ThreadPoolExecutor(4) as pool:
 for row in pool.map(run,jobs):
  rows.append(row);(log/'results.json').write_text(json.dumps(dict(config=dict(seconds=30,threads=2,seeds=[1,2],jobs=4),results=rows),indent=2));print(row,flush=True)
