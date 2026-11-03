import json,time,sys,subprocess,os,signal,hashlib
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
R=Path(__file__).resolve().parent
while True:
 p=R/'logs/mip_batch2/results.json'
 if p.exists() and len(json.loads(p.read_text()))==12:break
 time.sleep(5)
def run(cpu,backend):
 os.sched_setaffinity(0,{cpu});dest=R/'logs/long_mip';dest.mkdir(exist_ok=True)
 for warm,seconds in [('v4',600),('native',20)]:
  prefix=dest/f'{backend}_{warm}';t=time.monotonic();rc=None;timeout=False
  with prefix.with_suffix('.stderr').open('w') as err,prefix.with_suffix('.stdout').open('w') as out:
   p=subprocess.Popen(['/usr/bin/time','-f','rss_kb=%M user=%U sys=%S','-o',str(prefix.with_suffix('.resource')),'taskset','-c',str(cpu),'/tmp/szo-research-venv/bin/python',str(R/'long_mip.py'),backend,str(seconds),warm],stderr=err,stdout=out,start_new_session=True,env={'PATH':os.environ['PATH'],'OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1'})
   try:rc=p.wait(timeout=seconds+20)
   except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait();timeout=True
  info=dict(rc=rc,timeout=timeout,wall=time.monotonic()-t,cpu=cpu,backend=backend,warm=warm)
  prefix.with_suffix('.run.json').write_text(json.dumps(info,indent=2));print(info,flush=True)
with ThreadPoolExecutor(max_workers=2) as e:list(e.map(lambda args:run(*args),[(6,'highs'),(7,'scip')]))
