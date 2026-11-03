import json,os,sys,time,subprocess,importlib.util,argparse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
H=Path(__file__).resolve().parent;R=H.parents[1];BIN=H/'artifacts'
spec=importlib.util.spec_from_file_location('validator',R/'task/validate_solution.py');V=importlib.util.module_from_spec(spec);spec.loader.exec_module(V)
def native(inp,out,exe,seconds,seed,threads,flags):
 env=dict(os.environ,NT=str(threads),SEED=str(seed),DBG='1')
 for k in ['BOUNDARY','B_SUPPORT','B_Q','B_RESERVE','FINAL_POLISH','WORKER_DFS','WARM_START','EXACT2','LAZY','WFIX','LEVEL']:env.pop(k,None)
 env.update(flags);start=time.perf_counter()
 p=subprocess.run([str(BIN/exe),str(inp),str(out),str(seconds)],capture_output=True,text=True,env=env,timeout=seconds+35)
 wall=time.perf_counter()-start;out.with_suffix('.stderr').write_text(p.stderr)
 score=V.validate(inp,out)
 return dict(score=score if not isinstance(score,str) else None,error=score if isinstance(score,str) else None,wall=wall,rc=p.returncode)
def main():
 global BIN
 ap=argparse.ArgumentParser();ap.add_argument('--tag',required=True);ap.add_argument('--split',default='train');ap.add_argument('--mode',default='screen');ap.add_argument('--seconds',type=float,default=6);ap.add_argument('--post',type=float,default=1);ap.add_argument('--seeds',default='1');ap.add_argument('--cases',default='');ap.add_argument('--threads',type=int,default=1);ap.add_argument('--jobs',type=int,default=3);ap.add_argument('--bin-dir');ap.add_argument('--variants',default='base,bb,support,beam,diverse,weak');a=ap.parse_args()
 if a.bin_dir:BIN=Path(a.bin_dir).resolve()
 # User steering: pending long_run was launched before the 60-second limit request.
 if a.tag=='holdout280':a.tag='holdout60';a.seconds=60
 log=H/'logs'/a.tag
 if a.tag=='holdout60_broad' and log.exists():
  print('60-second broad series already dispatched; preserving existing logs.');return
 log.mkdir();files=sorted((H/'data'/a.split).glob('*.json'))
 if a.cases:files=[p for p in files if p.stem in a.cases.split(',')]
 variants={'base':(0,0),'bb':(1,0),'support':(1,1),'beam':(2,0),'diverse':(3,1),'weak':(4,0),'wide':(1,1),'beam32':(2,1),'diverse32':(3,1),'adaptive':(5,1),'tail':(1,1),'reserve':(1,1)}
 def run(job):
  inp,seed=job;case=inp.stem;rows=[]
  if a.mode=='screen':
   out=log/f'{case}_{seed}_base.json';r=native(inp,out,'baseline',a.seconds,seed,a.threads,{})
   rows.append(dict(case=case,seed=seed,variant='base',input=str(inp),solution=str(out),**r))
   data=json.loads(inp.read_text());asg=[-1]*len(data['sites'])
   for off in json.loads(out.read_text()):
    for x in off['sites']:asg[x]=off['officeId']
   ass=out.with_suffix('.asg');ass.write_text(' '.join(map(str,asg)))
   for name in a.variants.split(','):
    if name=='base':continue
    method,style=variants[name];dest=log/f'{case}_{seed}_{name}.json'
    start=time.perf_counter();p=subprocess.run([str(BIN/'post'),str(inp),str(ass),str(a.post),str(method),str(style),str(seed)],capture_output=True,text=True,timeout=a.post+25)
    wall=time.perf_counter()-start;dest.write_text(p.stdout);dest.with_suffix('.stderr').write_text(p.stderr)
    stats=json.loads(p.stderr.strip().splitlines()[-1]);score=V.validate(inp,dest)
    rows.append(dict(case=case,seed=seed,variant=name,input=str(inp),solution=str(dest),score=score,error=score if isinstance(score,str) else None,wall=wall,rc=p.returncode,stats=stats))
  else:
   names=a.variants.split(',');names=names[seed%len(names):]+names[:seed%len(names)]
   for name in names:
    m,st=variants[name];out=log/f'{case}_{seed}_{name}.json';r=native(inp,out,'baseline' if name=='base' else 'candidate_tail' if name in ['tail','reserve'] else 'candidate_v2' if name in ['wide','beam32','diverse32','adaptive'] else 'candidate',a.seconds,seed,a.threads,dict(BOUNDARY=str(m),B_SUPPORT=str(st),B_RESERVE=str(int(name=='reserve'))))
    rows.append(dict(case=case,seed=seed,variant=name,input=str(inp),solution=str(out),**r))
  return rows
 rows=[]
 with ThreadPoolExecutor(a.jobs) as pool:
  for result in pool.map(run,[(p,s) for s in map(int,a.seeds.split(',')) for p in files]):
   rows+=result;(log/'results.json').write_text(json.dumps(dict(config=vars(a),results=rows),indent=2))
   print(' '.join(f"{r['case']} s{r['seed']} {r['variant']}={r['score']}" for r in result),flush=True)
 assert all(not r['error'] and r['rc']==0 for r in rows)
if __name__=='__main__':main()
