"""Finalist numerical certificates on the unused seventh CPU pair, before packaging."""
from pathlib import Path
import os,sys,json,subprocess,hashlib
R=Path(__file__).resolve().parents[1];ROOT=R.parents[1];sys.path.insert(0,str(ROOT/'task'));from validate_solution import validate
os.sched_setaffinity(0,{20,21});old=ROOT/'experiments/adaptive_v11';scale=old/'logs/scale_qa_v4';cases=json.loads((scale/'results.json').read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();spec=json.loads((R/'SCREEN20.json').read_text())
for label in ['hybrid','plateau','geometry']:
 cfg=spec['variants'][label];exe=ROOT/cfg['binary'];d=R/'logs'/('scale_'+label);d.mkdir(exist_ok=False);rows=[]
 for i,x in enumerate(cases):
  inp=scale/(x['case']+'_'+str(x['factor'])+'.json')if'factor'in x else scale/'micro.json'if x['case']=='micro_counterexample'else old/'inputs/line_mechanism'/(x['case']+'.json')
  out=d/(str(i)+'.solution.json');err=d/(str(i)+'.stderr');env=dict(PATH=os.environ['PATH'],NT='2',**cfg.get('env',{}))
  with err.open('w')as f:p=subprocess.run([str(exe),str(inp),str(out),'2'],cwd=ROOT,env=env,stderr=f,timeout=5)
  v=validate(inp,out);a=json.loads(inp.read_text());norm=sum(abs(z['reward'])for z in a['sites'])+sum(abs(c)for ds in a['distances']for c in ds)+sum(abs(o['cost'])for o in a['offices']);ok=isinstance(v,(int,float))and abs(v-x['expected'])<=1e-10*max(norm,1e-300)
  if x['case']=='micro_counterexample':ok=ok and v>1e-10 and abs(v-2e-10)<1e-20
  row=dict(case=x['case'],factor=x.get('factor'),expected=x['expected'],official=v,rc=p.returncode,valid=isinstance(v,(int,float)),match=ok,input=str(inp.relative_to(ROOT)),input_sha256=sha(inp));rows.append(row);assert ok and p.returncode==0,row
 (d/'results.json').write_text(json.dumps(rows,indent=2));(d/'RECEIPT.json').write_text(json.dumps(dict(variant=label,binary_sha256=sha(exe),configuration=cfg.get('env',{}),cases=len(rows),valid=sum(x['valid']for x in rows),matches=sum(x['match']for x in rows),affinity=[20,21],disjoint_from_quality_pairs=True),indent=2));print(label,'scale',len(rows),'pass',flush=True)
