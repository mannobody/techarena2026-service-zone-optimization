import os,sys,json,subprocess,time,shutil
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from bench import H,R,V
sys.path.insert(0,str(R/'tools'));import gen
D=H/'data/edge';D.mkdir();gen.edge(D)
log=H/'logs/edges';log.mkdir()
def run(inp):
 work=log/inp.stem;work.mkdir();shutil.copyfile(inp,work/'instance.json')
 env=dict(os.environ,TL='3',NT='2',SEED='41',DBG='1',B_RESERVE='0')
 start=time.perf_counter();p=subprocess.run([str(H/'artifacts/candidate_tail')],cwd=work,env=env,capture_output=True,text=True,timeout=30);wall=time.perf_counter()-start
 (work/'stderr.txt').write_text(p.stderr);score=V.validate(work/'instance.json',work/'solution.json')
 return dict(case=inp.stem,score=score,wall=wall,rc=p.returncode,error=score if isinstance(score,str) else None,input=str(inp),output=str(work/'solution.json'),limit=3,threads=2,seed=41)
with ThreadPoolExecutor(2) as pool:rows=list(pool.map(run,sorted(D.glob('*.json'))))
(log/'results.json').write_text(json.dumps(rows,indent=2));assert all(not r['error'] and not r['rc'] for r in rows);print(len(rows),'VALID',max(r['wall'] for r in rows))
