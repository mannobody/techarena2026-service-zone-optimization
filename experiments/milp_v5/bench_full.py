import sys,json,os,time,subprocess,argparse,importlib.util
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
H=Path(__file__).resolve().parent;R=H.parents[1]
spec=importlib.util.spec_from_file_location('validator',R/'task/validate_solution.py');V=importlib.util.module_from_spec(spec);spec.loader.exec_module(V)
p=argparse.ArgumentParser();p.add_argument('--tag',required=True);p.add_argument('--split',default='train');p.add_argument('--variants',default='base');p.add_argument('--seeds',default='1');p.add_argument('--seconds',type=float,default=60);p.add_argument('--threads',type=int,default=2);p.add_argument('--jobs',type=int,default=4);p.add_argument('--cases',default='');p.add_argument('--post-from');p.add_argument('--exe',default='post');a=p.parse_args();D=H/'logs'/a.tag;D.mkdir()
def run(job):
 inp,seed,var=job;out=D/f'{inp.stem}_{seed}_{var}.json';env=dict(os.environ,NT=str(a.threads),SEED=str(seed),DBG='1',LD_LIBRARY_PATH='/tmp/ta-boundary-venv/lib64/python3.14/site-packages/highspy')
 for k in ['BOUNDARY','B_SUPPORT','B_Q','B_RESERVE','FINAL_POLISH','WORKER_DFS','WARM_START','EXACT2','LAZY','WFIX','LEVEL','GEO_MODE','GEO_SHARE','GEO_INDEX','GEO_EXACT','DP_MODE','FORCE_OPS','MIP','MIP_MODE','MIP_RESERVE']:env.pop(k,None)
 if a.post_from:
  source=H/'logs'/a.post_from/f'{inp.stem}_1_base.json';asg=[-1]*len(json.loads(inp.read_text())['sites'])
  for of in json.loads(source.read_text()):
   for s in of['sites']:asg[s]=of['officeId']
  ass=out.with_suffix('.asg');ass.write_text(' '.join(map(str,asg)));cmd=[str(H/'artifacts'/a.exe),str(inp),str(ass),str(a.seconds),var,str(seed)]
 else:
  exe=str(H.parent/'server_v4/artifacts/package/solution') if var=='base' else a.exe
  if var!='base':env.update(MIP_MODE='2',MIP_RESERVE='2')
  if var in ['scan','grid']:env['GEO_INDEX']=str(int(var=='grid'))
  cmd=[str(H/'artifacts'/exe),str(inp),str(out),str(a.seconds)]
 start=time.monotonic();pr=subprocess.run(cmd,env=env,text=True,capture_output=True,timeout=a.seconds+30);wall=time.monotonic()-start
 if a.post_from:out.write_text(pr.stdout)
 out.with_suffix('.stderr').write_text(pr.stderr);score=V.validate(inp,out)
 row=dict(case=inp.stem,seed=seed,variant=var,input=str(inp),solution=str(out),score=score if not isinstance(score,str) else None,error=score if isinstance(score,str) else None,rc=pr.returncode,wall=wall)
 if a.post_from:
  try:row['stats']=json.loads(pr.stderr.strip().splitlines()[-1])
  except Exception:pass
 return row
files=sorted(((H.parent/'geometry_islands/data/validation2') if a.split=='train' else (H/'data'/a.split)).glob('*.json'))
if a.cases:files=[p for p in files if p.stem in a.cases.split(',')]
rows=[]
with ThreadPoolExecutor(a.jobs) as ex:
 jobs=[(inp,seed,var) for seed in map(int,a.seeds.split(',')) for inp in files for var in a.variants.split(',')]
 for f in as_completed([ex.submit(run,j) for j in jobs]):
  r=f.result();rows.append(r);(D/'results.json').write_text(json.dumps(dict(config=vars(a),results=rows),indent=2));print(r['case'],r['seed'],r['variant'],r['score'],r['error'],flush=True)
assert all(r['error'] is None and r['rc']==0 for r in rows)
