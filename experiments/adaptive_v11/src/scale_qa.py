import os,subprocess,json,time,sys,copy,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];ROOT=R.parents[1];sys.path.insert(0,str(ROOT/'task'));from validate_solution import validate
os.sched_setaffinity(0,{14,15});d=R/'logs/scale_qa_v4';d.mkdir(exist_ok=False)
while not (R/'artifacts/v4/COMPILED.json').exists():time.sleep(1)
exe=R/'artifacts/v4/candidate';original=R/'logs/specialists_v3';cases=[x for x in json.loads((original/'results.json').read_text())if'expected'in x];rows=[]
for row in cases:
 a=json.loads((original/(row['case']+'.json')).read_text())
 for factor in [1e-12,1e-6,1.,1e6,1e12]:
  b=copy.deepcopy(a)
  for s in b['sites']:s['reward']*=factor
  for o in b['offices']:o['cost']*=factor
  for costs in b['distances']:
   for j in range(len(costs)):costs[j]*=factor
  b['balanceCoefficient']*=factor
  name=row['case']+'_'+str(factor);inp=d/(name+'.json');inp.write_text(json.dumps(b));out=d/(name+'.solution.json');err=d/(name+'.stderr')
  with err.open('w')as f:p=subprocess.run([str(exe),str(inp),str(out),'2'],stderr=f,env=dict(PATH=os.environ['PATH']),timeout=4)
  value=validate(inp,out);expected=row['expected']*factor
  norm=sum(abs(s['reward'])for s in b['sites'])+sum(abs(v)for v in b['distances']for v in v)+sum(abs(o['cost'])for o in b['offices'])
  good=isinstance(value,(int,float))and abs(value-expected)<=1e-10*max(norm,1e-300)
  r=dict(case=row['case'],factor=factor,expected=expected,official=value,match=good,valid=isinstance(value,(int,float)),rc=p.returncode);rows.append(r);assert good and p.returncode==0,r
# The originally failing micro-positive instance is tested without tolerance masking.
a=json.loads((R/'logs/scale_counterexample_v3/instance.json').read_text());inp=d/'micro.json';inp.write_text(json.dumps(a));out=d/'micro.solution.json'
with (d/'micro.stderr').open('w')as f:p=subprocess.run([str(exe),str(inp),str(out),'2'],stderr=f,timeout=4)
v=validate(inp,out);assert v>1e-10 and abs(v-2e-10)<1e-20,(v,p.returncode)
rows.append(dict(case='micro_counterexample',expected=2e-10,official=v,valid=True,match=True,rc=p.returncode))
# Same viewed exact-class values from the unmodified long mechanism source, now in corrected source.
for inp in sorted((R/'inputs/line_mechanism').glob('*.json')):
 out=d/(inp.stem+'_corrected.solution.json');err=d/(inp.stem+'_corrected.stderr')
 with err.open('w')as f:p=subprocess.run([str(exe),str(inp),str(out),'2'],stderr=f,timeout=4)
 v=validate(inp,out);prior=json.loads((R/'logs/line_screen8'/f'{inp.stem}_0_adaptive.json').read_text())['official'];assert abs(v-prior)<1e-7 and p.returncode==0,(inp,v,prior)
 rows.append(dict(case=inp.stem,expected=prior,official=v,valid=True,match=True,rc=p.returncode))
(d/'results.json').write_text(json.dumps(rows,indent=2));print(json.dumps(dict(cases=len(rows),valid=sum(x['valid']for x in rows),matches=sum(x['match']for x in rows))),flush=True)
