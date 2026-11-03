from pathlib import Path
import sys,json,subprocess,os
from concurrent.futures import ThreadPoolExecutor,as_completed
H=Path(__file__).resolve().parent
if len(sys.argv)>1:
 from milp_warm import Instance,improve
 case,mode,inp,sol=sys.argv[1:];r=improve(Instance.read(inp),json.loads(Path(sol).read_text()),58,mode,H/'logs/milp_warm60'/f'{case}_{mode}.checkpoint.json',json.loads((H/'logs/native_post_relative60'/f'{case}_2.json').read_text()));r.update(case=case,input=inp,incumbent=sol,limit=60,threads=1)
 (H/'logs/milp_warm60'/f'{case}_{mode}.json').write_text(json.dumps(r,indent=2));print(json.dumps({k:v for k,v in r.items() if k!='solution'}));sys.exit()
D=H/'logs/milp_warm60';D.mkdir();items=[dict(case='controlled_'+r['case'],input=r['input'],incumbent=r['incumbent']) for r in json.loads((H/'data/controlled_manifest.json').read_text())]
items += [dict(case='ordinary_'+r['case'],input=r['input'],incumbent=r['solution']) for r in json.loads((H.parent/'server_v4/logs/package60/results.json').read_text()) if r['split']=='validation2']
jobs=[(r,'assigned') for r in items if r['case'] in ['controlled_many_sites','controlled_count_tight','controlled_gcd_large']]
def run(job):
 import time
 r,mode=job;dest=D/f'{r["case"]}_{mode}.checkpoint.json'
 # Parent publishes a validated incumbent before the child starts.
 from milp import Instance,value
 inc=json.loads((H/'logs/native_post_relative60'/f'{r["case"]}_2.json').read_text());before=value(Instance.read(r['input']),json.loads(Path(r['incumbent']).read_text()));warm_value=value(Instance.read(r['input']),inc)
 dest.write_text(json.dumps(dict(solution=inc,value=warm_value,before=before,status='initial',seconds=0,candidates=None,mode=mode,rejected=None)))
 t=time.monotonic()
 try:
  pr=subprocess.run([sys.executable,__file__,r['case'],mode,r['input'],r['incumbent']],text=True,capture_output=True,timeout=60,env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1'))
  (D/f'{r["case"]}_{mode}.stderr').write_text(pr.stderr)
  if pr.returncode:return dict(case=r['case'],mode=mode,rc=pr.returncode,error=pr.stderr)
  result=json.loads((D/f'{r["case"]}_{mode}.json').read_text());result['hard_timeout']=False
 except subprocess.TimeoutExpired:
  result=json.loads(dest.read_text());result.update(case=r['case'],input=r['input'],incumbent=r['incumbent'],hard_timeout=True,status='external_deadline',limit=60,threads=1)
 result['process_wall']=time.monotonic()-t
 return {k:v for k,v in result.items() if k!='solution'}

rows=[]
with ThreadPoolExecutor(4) as ex:
 for f in as_completed([ex.submit(run,j) for j in jobs]):
  r=f.result();rows.append(r);(D/'results.json').write_text(json.dumps(rows,indent=2));print(json.dumps(r),flush=True)
