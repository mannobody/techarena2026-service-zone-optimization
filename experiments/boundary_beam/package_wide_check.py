import json,time,subprocess,os,shutil
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from bench import H,V
while True:
 try:
  if len(json.loads((H/'logs/holdout30/results.json').read_text())['results'])==96:break
 except (FileNotFoundError,json.JSONDecodeError):pass
 time.sleep(10)
log=H/'logs/package_wide60';log.mkdir()
def run(name):
 w=log/name;w.mkdir();inp=H/'data/validation2'/f'{name}.json';shutil.copyfile(inp,w/'instance.json');shutil.copyfile(H/'artifacts/package_wide/solution',w/'solution');os.chmod(w/'solution',0o755);shutil.copyfile(H/'artifacts/package_wide/Makefile',w/'Makefile')
 env=dict(os.environ,TL='60',NT='2',SEED='71');env.pop('DBG',None);env.pop('BOUNDARY',None);env.pop('B_SUPPORT',None);st=time.perf_counter();p=subprocess.run(['make','run'],cwd=w,env=env,capture_output=True,text=True,timeout=80);wall=time.perf_counter()-st
 (w/'stderr.txt').write_text(p.stderr);score=V.validate(w/'instance.json',w/'solution.json');return dict(case=name,input=str(inp),output=str(w/'solution.json'),score=score,wall=wall,rc=p.returncode,error=score if isinstance(score,str) else None,seed=71,seconds=60,threads=2)
with ThreadPoolExecutor(2) as pool:rows=list(pool.map(run,['alphabig0','latent0']))
(log/'results.json').write_text(json.dumps(rows,indent=2));assert all(not r['error'] and not r['rc'] for r in rows);print(rows)
