from pathlib import Path
import subprocess,json,os,time,shutil,importlib.util,hashlib
from concurrent.futures import ThreadPoolExecutor,as_completed
H=Path(__file__).resolve().parent;R=H.parents[1];G=H.parent/'geometry_islands';D=H/'logs/package_safe60';D.mkdir()
spec=importlib.util.spec_from_file_location('validator',R/'task/validate_solution.py');V=importlib.util.module_from_spec(spec);spec.loader.exec_module(V)
exe=H/'artifacts/package_safe/solution';assert exe.exists()
inputs=[(p.parent.name,p) for split in ['edge','precision'] for p in sorted((G/'data'/split).glob('*.json'))]
inputs += [('crossing',p) for p in sorted((G/'data').glob('crossing_family_*.json')) if 'solution' not in p.stem]
def run(item):
 split,inp=item;d=D/f'{split}_{inp.stem}';d.mkdir();shutil.copyfile(inp,d/'instance.json');env=dict(os.environ,TL='60',NT='2',SEED='101',DBG='1',LD_LIBRARY_PATH='/tmp/ta-boundary-venv/lib64/python3.14/site-packages/highspy')
 for k in ['GEO_INDEX','GEO_EXACT','BOUNDARY','B_RESERVE','WORKER_DFS','WARM_START','FINAL_POLISH','LAZY','WFIX','EXACT2','FORCE_OPS','MIP','MIP_MODE','MIP_RESERVE']:env.pop(k,None)
 t=time.monotonic();pr=subprocess.run([str(exe)],cwd=d,env=env,capture_output=True,text=True,timeout=90);wall=time.monotonic()-t;(d/'stderr.txt').write_text(pr.stderr);score=V.validate(d/'instance.json',d/'solution.json')
 return dict(split=split,case=inp.stem,input=str(inp),solution=str(d/'solution.json'),score=score if not isinstance(score,str) else None,error=score if isinstance(score,str) else None,rc=pr.returncode,wall=wall,seconds=60,threads=2,seed=101)
rows=[]
with ThreadPoolExecutor(3) as ex:
 for f in as_completed([ex.submit(run,p) for p in inputs]):
  r=f.result();rows.append(r);(D/'results.json').write_text(json.dumps(rows,indent=2));print(r['case'],r['score'],r['error'],flush=True)
assert all(r['rc']==0 and r['error'] is None for r in rows)
print('ALL VALID',len(rows),flush=True)
