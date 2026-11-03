from pathlib import Path
import json,random,importlib.util,hashlib
H=Path(__file__).resolve().parent;R=H.parents[1];D=H/'data/controlled';D.mkdir()
spec=importlib.util.spec_from_file_location('validator',R/'task/validate_solution.py');V=importlib.util.module_from_spec(spec);spec.loader.exec_module(V)
rows=[]
def save(name,weights,profits,alpha,A):
 m=len(weights);sites=[];offices=[];sol=[];owners=[]
 for o,ww in enumerate(weights):
  offices.append(dict(x=o*10.,y=0.,cost=0,maxSize=len(ww)));ss=[]
  for j,w in enumerate(ww):
   ss.append(len(sites));owners.append(o);sites.append(dict(x=o*10.+.1+(j%31)/100.,y=.1+(j//31)/1000.,reward=200,tasks=[0]*w))
  sol.append(dict(officeId=o,sites=ss,workers=[o]))
 pp=[p for row in profits for p in row];data=dict(sites=sites,offices=offices,workers=[[0] for _ in range(m)],distances=[[200-pp[s] if owners[s]==o else 1000 for s in range(len(sites))] for o in range(m)],maxDifference=A,balanceCoefficient=alpha)
 p=D/f'{name}.json';q=D/f'{name}.solution.json';p.write_text(json.dumps(data));q.write_text(json.dumps(sol));score=V.validate(p,q);assert not isinstance(score,str),score
 rows.append(dict(case=name,input=str(p),incumbent=str(q),score=score,n=len(sites),max_load=max(map(sum,weights)),alpha=alpha,A=A,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
save('count_gap',[[2,1,1]]*2,[[100,-20,-20],[-100,60,60]],70,0)
for case,n,m,mult,alpha,A in [('dense_load',480,4,1,30,480),('gcd_large',3000,4,100,10,3000),('count_tight',1200,4,1,30,0),('many_sites',10000,20,1,40,3)]:
 r=random.Random(231000+len(rows));nn=n//m;w=[1+j%5 for j in range(nn)];weights=[[x*mult for x in w] for _ in range(m)];profits=[[r.uniform(-45,120) for j in range(nn)] for o in range(m)];save(case,weights,profits,alpha,A)
(H/'data/controlled_manifest.json').write_text(json.dumps(rows,indent=2));print([(r['case'],r['score']) for r in rows])
