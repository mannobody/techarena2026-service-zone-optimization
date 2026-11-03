from pathlib import Path
import sys,json,time,subprocess,os
from concurrent.futures import ThreadPoolExecutor,as_completed
H=Path(__file__).resolve().parent;D=H/'logs/split60'
if len(sys.argv)>1:
 from split_office import *
 case,inp,inc=sys.argv[1:];r=search(Instance.read(inp),json.loads(Path(inc).read_text()),57,D/f'{case}.checkpoint.json');(D/f'{case}.json').write_text(json.dumps(r,indent=2));sys.exit()
D.mkdir();items=[dict(case=r['case'],input=r['input'],incumbent=r['solution']) for r in json.loads((H.parent/'server_v4/logs/package60/results.json').read_text()) if r['split']=='validation2' and r['case'] in ['alphabig0','tightA0','large0','huge0','latent1']]
items.append(dict(case='diagnostic_missing_office',input=str(H.parent/'dp_milp/data/full_holdout/large0.json'),incumbent=str(H.parent/'dp_milp/logs/full_holdout60/large0_111_candidate.json')))
def run(r):
 dest=D/f'{r["case"]}.checkpoint.json';dest.write_text(json.dumps(dict(solution=json.loads(Path(r['incumbent']).read_text()),status='initial')));t=time.monotonic()
 try:
  q=subprocess.run([sys.executable,__file__,r['case'],r['input'],r['incumbent']],capture_output=True,text=True,timeout=60,env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1'));(D/f'{r["case"]}.stderr').write_text(q.stderr);assert q.returncode==0,q.stderr;out=json.loads((D/f'{r["case"]}.json').read_text());hard=False
 except subprocess.TimeoutExpired:out=json.loads(dest.read_text());hard=True
 from grouped import Instance,value
 I=Instance.read(r['input']);score=value(I,out['solution']);assert not isinstance(score,str),score
 return dict(**{k:v for k,v in out.items() if k not in ['solution','value']},**r,value=score,valid=True,hard_timeout=hard,wall=time.monotonic()-t)
rows=[]
with ThreadPoolExecutor(2) as ex:
 for f in as_completed([ex.submit(run,r) for r in items]):
  r=f.result();rows.append(r);(D/'results.json').write_text(json.dumps(rows,indent=2));print(r['case'],r['value'],r['wall'],len(r.get('trials',[])),flush=True)
