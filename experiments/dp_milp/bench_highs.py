from pathlib import Path
import sys,json,subprocess,time,os
from concurrent.futures import ThreadPoolExecutor,as_completed
H=Path(__file__).resolve().parent;D=H/'logs/highs60'
if len(sys.argv)>1:
 from highs_selection import Instance,improve
 case,inp,sol=sys.argv[1:];warm=json.loads((H/'logs/native_post_relative60'/f'{case}_2.json').read_text());r=improve(Instance.read(inp),json.loads(Path(sol).read_text()),58,warm,D/f'{case}.checkpoint.json');r.update(case=case,input=inp,incumbent=sol);(D/f'{case}.json').write_text(json.dumps(r,indent=2));sys.exit()
D.mkdir();items=[dict(case='controlled_'+r['case'],input=r['input'],incumbent=r['incumbent']) for r in json.loads((H/'data/controlled_manifest.json').read_text())]
items += [dict(case='ordinary_'+r['case'],input=r['input'],incumbent=r['solution']) for r in json.loads((H.parent/'server_v4/logs/package60/results.json').read_text()) if r['split']=='validation2' and r['case'] in ['alphabig0','huge0']]
def run(r):
 from milp import Instance,value
 warm=json.loads((H/'logs/native_post_relative60'/f'{r["case"]}_2.json').read_text());dest=D/f'{r["case"]}.checkpoint.json';v=value(Instance.read(r['input']),warm);dest.write_text(json.dumps(dict(solution=warm,value=v,status='initial',seconds=0)))
 t=time.monotonic()
 try:
  p=subprocess.run([sys.executable,__file__,r['case'],r['input'],r['incumbent']],text=True,capture_output=True,timeout=60,env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1'));(D/f'{r["case"]}.stderr').write_text(p.stderr)
  if p.returncode:return dict(**r,error=p.stderr,rc=p.returncode)
  result=json.loads((D/f'{r["case"]}.json').read_text());result['hard_timeout']=False
 except subprocess.TimeoutExpired:result=json.loads(dest.read_text());result.update(r,hard_timeout=True,status='external_deadline')
 result.update(process_wall=time.monotonic()-t,limit=60,threads=1);return {k:v for k,v in result.items() if k!='solution'}
rows=[]
with ThreadPoolExecutor(3) as ex:
 for f in as_completed([ex.submit(run,r) for r in items]):
  r=f.result();rows.append(r);(D/'results.json').write_text(json.dumps(rows,indent=2));print(json.dumps(r),flush=True)
