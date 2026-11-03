import json,time,subprocess,os,shutil
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from bench import H,V
# Wait until the four-thread 60s repeat frees its slots.
while True:
 try:
  if len(json.loads((H/'logs/holdout60/results.json').read_text())['results'])==8:break
 except (FileNotFoundError,json.JSONDecodeError):pass
 time.sleep(10)
log=H/'logs/package60';log.mkdir()
cases=[H/'data/holdout/alphabig0.json',H/'data/holdout/latent0.json']
def run(inp):
 w=log/inp.stem;w.mkdir();shutil.copyfile(inp,w/'instance.json');env=dict(os.environ,TL='60',NT='2',SEED='51',B_RESERVE='0')
 env.pop('DBG',None);env.pop('DBG2',None);st=time.perf_counter();p=subprocess.run([str(H/'artifacts/package_tail/solution')],cwd=w,env=env,capture_output=True,text=True,timeout=80);wall=time.perf_counter()-st
 (w/'stderr.txt').write_text(p.stderr);score=V.validate(w/'instance.json',w/'solution.json');return dict(case=inp.stem,input=str(inp),output=str(w/'solution.json'),score=score,wall=wall,error=score if isinstance(score,str) else None,rc=p.returncode,seed=51,seconds=60,threads=2)
with ThreadPoolExecutor(2) as pool:rows=list(pool.map(run,cases))
(log/'results.json').write_text(json.dumps(rows,indent=2));assert all(not r['error'] and not r['rc'] for r in rows);print(rows)
