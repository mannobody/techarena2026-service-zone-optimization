from pathlib import Path
import subprocess,json,os,time,shutil,importlib.util,hashlib
from concurrent.futures import ThreadPoolExecutor,as_completed
H=Path(__file__).resolve().parent;R=H.parents[1];G=H.parent/'geometry_islands';D=H/'logs/package60';D.mkdir()
spec=importlib.util.spec_from_file_location('validator',R/'task/validate_solution.py');V=importlib.util.module_from_spec(spec);spec.loader.exec_module(V)
exe=H/'artifacts/package/solution';assert exe.exists()
inputs=[(p.parent.name,p) for split in ['validation2','edge','precision'] for p in sorted((G/'data'/split).glob('*.json'))]
inputs += [('crossing',p) for p in sorted((G/'data').glob('crossing_family_*.json')) if 'solution' not in p.stem]
def run(item):
 split,inp=item;d=D/f'{split}_{inp.stem}';d.mkdir();shutil.copyfile(inp,d/'instance.json');env=dict(os.environ,TL='60',NT='2',SEED='101',DBG='1')
 for k in ['GEO_INDEX','GEO_EXACT','BOUNDARY','B_RESERVE','WORKER_DFS','WARM_START','FINAL_POLISH','LAZY','WFIX','EXACT2','FORCE_OPS']:env.pop(k,None)
 t=time.monotonic();pr=subprocess.run([str(exe)],cwd=d,env=env,capture_output=True,text=True,timeout=90);wall=time.monotonic()-t;(d/'stderr.txt').write_text(pr.stderr);score=V.validate(d/'instance.json',d/'solution.json')
 return dict(split=split,case=inp.stem,input=str(inp),solution=str(d/'solution.json'),score=score if not isinstance(score,str) else None,error=score if isinstance(score,str) else None,rc=pr.returncode,wall=wall,seconds=60,threads=2,seed=101)
rows=[]
with ThreadPoolExecutor(6) as ex:
 for f in as_completed([ex.submit(run,p) for p in inputs]):
  r=f.result();rows.append(r);(D/'results.json').write_text(json.dumps(rows,indent=2));print(r['case'],r['score'],r['error'],flush=True)
assert all(r['rc']==0 and r['error'] is None for r in rows)
p=H/'MANIFEST.json';m=json.loads(p.read_text());m.update(status='Validated server candidate v4; not submitted; general score superiority unproven',package_checks=dict(total=len(rows),valid=len(rows),seconds=60,threads=2,jobs=6,seed=101,max_wall=max(r['wall'] for r in rows)));p.write_text(json.dumps(m,indent=2));print('ALL VALID',len(rows),flush=True)
