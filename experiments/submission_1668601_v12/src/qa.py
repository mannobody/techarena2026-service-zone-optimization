"""Correctness-only checks on disjoint CPUs before quality screening."""
import json,time,os,subprocess,sys,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];ROOT=R.parents[1];sys.path.insert(0,str(ROOT/'task'));from validate_solution import validate
os.sched_setaffinity(0,{3,6});d=R/'logs/qa';d.mkdir(exist_ok=False)
s=json.loads((R/'SCREEN20.json').read_text());inputs=list((ROOT/'experiments/adaptive_v11/logs/qa_v4/inputs').glob('*.json'))
inputs +=[ROOT/'experiments/adaptive_v11/inputs/dev'/f'{n}.json'for n in ['euclid240','equal180','grid180','multi260']]
inputs +=[ROOT/'experiments/v8_exact_neighborhoods/inputs/worker_budget_isolated.json',ROOT/'experiments/adaptive_v11/inputs/line_mechanism/line9.json']
rows=[]
for label,conf in s['variants'].items():
 binary=ROOT/conf['binary'];build=binary.parent/'BUILD.json'
 if label!='submission':
  while not build.exists():time.sleep(1)
  assert json.loads(build.read_text())['rc']==0,label
 for inp in inputs:
  name=label+'_'+inp.stem;out=d/(name+'.solution.json');err=d/(name+'.stderr');env=dict(PATH=os.environ['PATH'],NT='2',SEED='12600',**conf.get('env',{}));begin=time.monotonic()
  with err.open('w')as f:p=subprocess.run(['taskset','-c','3,6',str(binary),str(inp),str(out),'1.5'],env=env,stderr=f,timeout=6)
  v=validate(inp,out);txt=err.read_text();row=dict(variant=label,case=inp.stem,rc=p.returncode,wall=time.monotonic()-begin,valid=isinstance(v,(int,float)),official=v,error=any(x in txt for x in ['error:','VERIFY','INVALID']),input_sha256=hashlib.sha256(inp.read_bytes()).hexdigest());rows.append(row)
  (d/'results.json').write_text(json.dumps(rows,indent=2));assert row['valid']and row['rc']==0 and not row['error'],row
 print(label,'QA pass',len(inputs),flush=True)
(R/'QA_STATUS.json').write_text(json.dumps(dict(stage='complete',runs=len(rows),variants=len(s['variants']),all_valid=True),indent=2));print('all QA complete',len(rows),flush=True)
