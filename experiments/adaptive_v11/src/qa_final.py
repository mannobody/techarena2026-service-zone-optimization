import json,os,subprocess,time,sys,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];ROOT=R.parents[1];sys.path.insert(0,str(ROOT/'task'));sys.path.insert(0,str(ROOT/'tools'))
from validate_solution import validate
import gen
os.sched_setaffinity(0,{14,15});revision=sys.argv[1]if len(sys.argv)>1 else'v3';d=R/'logs'/('qa_'+revision);d.mkdir(exist_ok=False);inputs=d/'inputs';inputs.mkdir();gen.edge(str(inputs));tests=list(inputs.glob('*.json'))
# Exercise actual racing above tiny threshold, early stopping, high load and both promotion sides.
tests +=[R/'inputs/dev'/f'{n}.json'for n in ['euclid240','equal180','anti220','multi260','grid180','huge10000']]
rows=[]
for inp in tests:
 for policy in [0,1,2]:
  name=inp.stem+'_'+str(policy);out=d/(name+'.solution.json');err=d/(name+'.stderr');begin=time.monotonic()
  env=dict(PATH=os.environ['PATH'],AP_POLICY=str(policy),AP_SHARE='1',SEED='11600')
  with err.open('w')as f:p=subprocess.run(['taskset','-c',os.getenv('QA_CPU','3,6'),str(R/'artifacts'/revision/'candidate'),str(inp),str(out),'1.5'],env=env,stderr=f,timeout=5)
  wall=time.monotonic()-begin;v=validate(inp,out);txt=err.read_text()
  rows.append(dict(case=inp.stem,policy=policy,rc=p.returncode,wall=wall,official=v,valid=isinstance(v,(int,float)),error=any(x in txt for x in ['error:','VERIFY','INVALID']),input_sha256=hashlib.sha256(inp.read_bytes()).hexdigest()))
  (d/'results.json').write_text(json.dumps(rows,indent=2))
print(json.dumps(dict(runs=len(rows),valid=sum(x['valid']for x in rows),bad=[x for x in rows if not x['valid']or x['rc']or x['error']])),flush=True)
assert all(x['valid']and x['rc']==0 and not x['error']for x in rows)
