import os,time,json,subprocess
from concurrent.futures import ThreadPoolExecutor
from bench import H,V
log=H/'logs/post_v2';log.mkdir();cases=['alphabig0','alphabig1','anti1','latent0','latent1','latent2','tightA0','tightA1','medium0','huge1']
# Same input solution, same q/style, fixed CPU threads; separate diverse ablation.
jobs=[(c,m,q,seed) for c in cases for m,q in [(1,12),(1,24),(1,36),(2,24),(3,24),(5,24)] for seed in [11,12]]
def run(job):
 c,m,q,seed=job;inp=H/'data/train'/f'{c}.json';ass=H/'logs/screen_v1'/f'{c}_1_base.asg';key=f'{c}_m{m}_q{q}_s{seed}';dest=log/f'{key}.json';env=dict(os.environ,B_Q=str(q))
 st=time.perf_counter();p=subprocess.run([str(H/'artifacts/post_v2'),str(inp),str(ass),'1',str(m),'1',str(seed)],env=env,capture_output=True,text=True,check=True,timeout=30);wall=time.perf_counter()-st
 dest.write_text(p.stdout);dest.with_suffix('.stderr').write_text(p.stderr);stats=json.loads(p.stderr.splitlines()[-1]);score=V.validate(inp,dest);assert not isinstance(score,str),score
 return dict(case=c,method=m,q=q,seed=seed,score=score,wall=wall,stats=stats,solution=str(dest),input=str(inp))
rows=[]
with ThreadPoolExecutor(3) as pool:
 for r in pool.map(run,jobs):
  rows.append(r);(log/'results.json').write_text(json.dumps(rows,indent=2));print(r['case'],r['method'],r['q'],r['seed'],round(100*(r['score']/r['stats']['before']-1),3),flush=True)
