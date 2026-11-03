from pathlib import Path
import sys,json,subprocess,os
from concurrent.futures import ThreadPoolExecutor,as_completed
H=Path(__file__).resolve().parent
if len(sys.argv)>1:
 from milp import Instance,improve
 case,mode,inp,sol=sys.argv[1:];r=improve(Instance.read(inp),json.loads(Path(sol).read_text()),60,mode);r.update(case=case,input=inp,incumbent=sol,limit=60,threads=1)
 (H/'logs/milp60'/f'{case}_{mode}.json').write_text(json.dumps(r,indent=2));print(json.dumps({k:v for k,v in r.items() if k!='solution'}));sys.exit()
D=H/'logs/milp60';D.mkdir();items=[dict(case='controlled_'+r['case'],input=r['input'],incumbent=r['incumbent']) for r in json.loads((H/'data/controlled_manifest.json').read_text())]
items += [dict(case='ordinary_'+r['case'],input=r['input'],incumbent=r['solution']) for r in json.loads((H.parent/'server_v4/logs/package60/results.json').read_text()) if r['split']=='validation2']
jobs=[(r,'assigned') for r in items]+[(r,mode) for r in items if r['case'] in ['ordinary_alphabig0','ordinary_tightA0','ordinary_multiskill0','ordinary_huge0','ordinary_latent1'] for mode in ['territory','joint']]
def run(job):
 r,mode=job;pr=subprocess.run([sys.executable,__file__,r['case'],mode,r['input'],r['incumbent']],text=True,capture_output=True,timeout=90,env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1'));(D/f'{r["case"]}_{mode}.stderr').write_text(pr.stderr)
 if pr.returncode:return dict(case=r['case'],mode=mode,rc=pr.returncode,error=pr.stderr)
 return {k:v for k,v in json.loads((D/f'{r["case"]}_{mode}.json').read_text()).items() if k!='solution'}
rows=[]
with ThreadPoolExecutor(4) as ex:
 for f in as_completed([ex.submit(run,j) for j in jobs]):
  r=f.result();rows.append(r);(D/'results.json').write_text(json.dumps(rows,indent=2));print(json.dumps(r),flush=True)
