from pathlib import Path
import json,os,time,subprocess,shutil
from grouped import Instance,value
H=Path(__file__).resolve().parent;D=H/'logs/fallback60';D.mkdir();rows=[]
for mode in ['missing','disabled']:
 d=D/mode;d.mkdir();inp=H.parent/'geometry_islands/data/edge/edge_multiskill.json'
 if not inp.exists():inp=next(p for p in (H.parent/'geometry_islands/data/edge').glob('*multiskill*.json'))
 shutil.copyfile(inp,d/'instance.json');env=dict(os.environ,TL='60',NT='2',SEED='141',DBG='1');env.pop('LD_LIBRARY_PATH',None)
 if mode=='disabled':env.update(MIP='0',LD_LIBRARY_PATH='/tmp/ta-boundary-venv/lib64/python3.14/site-packages/highspy')
 else:env.pop('MIP',None)
 t=time.monotonic();q=subprocess.run([str(H/'artifacts/package/solution')],cwd=d,env=env,text=True,capture_output=True,timeout=63);wall=time.monotonic()-t;(d/'stderr.txt').write_text(q.stderr);assert q.returncode==0;score=value(Instance.read(inp),json.loads((d/'solution.json').read_text()));assert not isinstance(score,str),score;assert 'v5_mip' not in q.stderr;rows.append(dict(mode=mode,value=score,wall=wall,valid=True));(D/'results.json').write_text(json.dumps(rows,indent=2));print(rows[-1],flush=True)
