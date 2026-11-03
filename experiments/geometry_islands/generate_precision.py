import json,importlib.util
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[1];D=H/'data/precision';D.mkdir()
spec=importlib.util.spec_from_file_location('validator',R/'task/validate_solution.py');V=importlib.util.module_from_spec(spec);spec.loader.exec_module(V)
rows=[]
for name,delta,offset in [('wide',1e-8,0),('thin',1e-10,0),('thinner',1e-12,0),('translated',2e-10,1e6),('coincident',0,0)]:
 k=4;sites=[];offices=[]
 for i in range(k):
  offices.append(dict(x=offset,y=offset+i*delta,cost=0,maxSize=2))
  sites.extend([dict(x=offset+1,y=offset+i*delta,reward=10,tasks=[0]),dict(x=offset+.6,y=offset+i*delta+delta*.2,reward=10,tasks=[0])])
 d=dict(sites=sites,offices=offices,workers=[[0] for _ in range(k)],distances=[[0 if s//2==o else 100 for s in range(k*2)] for o in range(k)],maxDifference=0,balanceCoefficient=0)
 sol=[dict(officeId=o,sites=[2*o,2*o+1],workers=[o]) for o in range(k if delta else 1)]
 p=D/f'{name}.json';p.write_text(json.dumps(d));q=H/'data'/f'precision_{name}_witness.json';q.write_text(json.dumps(sol));score=V.validate(p,q);assert not isinstance(score,str),(name,score);rows.append(dict(case=name,input=str(p),witness=str(q),score=score))
(H/'data/precision_manifest.json').write_text(json.dumps(rows,indent=2));print(rows)
