from pathlib import Path
import json,os,time,subprocess,importlib.util,argparse
from concurrent.futures import ThreadPoolExecutor,as_completed
H=Path(__file__).resolve().parent;R=H.parents[1]
spec=importlib.util.spec_from_file_location('validator',R/'task/validate_solution.py');V=importlib.util.module_from_spec(spec);spec.loader.exec_module(V)
p=argparse.ArgumentParser();p.add_argument('--tag',default='native_post60');p.add_argument('--exe',default='post_scaled');p.add_argument('--modes',default='0,1,2');a=p.parse_args();D=H/'logs'/a.tag;D.mkdir()
items=[dict(case='controlled_'+r['case'],input=r['input'],incumbent=r['incumbent']) for r in json.loads((H/'data/controlled_manifest.json').read_text())]
items += [dict(case='ordinary_'+r['case'],input=r['input'],incumbent=r['solution']) for r in json.loads((H.parent/'server_v4/logs/package60/results.json').read_text()) if r['split']=='validation2']
def run(job):
 r,mode=job;inp=Path(r['input']);stem=r['case']+'_'+mode;asg=[-1]*len(json.loads(inp.read_text())['sites'])
 for o in json.loads(Path(r['incumbent']).read_text()):
  for x in o['sites']:asg[x]=o['officeId']
 ap=D/(stem+'.asg');ap.write_text(' '.join(map(str,asg)));out=D/(stem+'.json');env=dict(os.environ,NT='1',DP_MODE=mode);env.pop('DBG',None)
 t=time.monotonic();pr=subprocess.run([str(H/'artifacts'/a.exe),str(inp),str(out),str(ap),'60','5'],env=env,text=True,capture_output=True,timeout=90);wall=time.monotonic()-t;(D/(stem+'.stderr')).write_text(pr.stderr)
 score=V.validate(inp,out);stats=json.loads(pr.stderr.strip().splitlines()[-1]);return dict(**r,mode=mode,score=score,error=score if isinstance(score,str) else None,rc=pr.returncode,wall=wall,solution=str(out),stats=stats)
rows=[]
with ThreadPoolExecutor(3) as ex:
 for f in as_completed([ex.submit(run,(r,m)) for r in items for m in a.modes.split(',')]):
  r=f.result();rows.append(r);(D/'results.json').write_text(json.dumps(rows,indent=2));print(r['case'],r['mode'],r['score'],r['stats']['dp_seconds'],flush=True)
assert all(r['rc']==0 and r['error'] is None for r in rows)
