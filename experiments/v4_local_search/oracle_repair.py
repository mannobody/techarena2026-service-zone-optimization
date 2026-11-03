import itertools,json,random,time,sys,math
from pathlib import Path
from repair_mip import improve,score
R=Path(__file__).resolve().parent;out=R/'logs'/(sys.argv[1] if len(sys.argv)>1 else 'repair_oracle');out.mkdir(exist_ok=False)
rows=[]
for seed in range(30):
 r=random.Random(88000+seed);n=5;m=2
 data={'sites':[dict(x=r.randrange(7),y=0 if seed%4==0 else r.randrange(7),reward=r.randrange(3,21),tasks=[r.randrange(2) for _ in range(r.randrange(4))]) for _ in range(n)],'offices':[dict(x=-1 if o==0 else 8,y=0 if seed%4==0 else r.randrange(7),cost=r.randrange(0,5),maxSize=r.randrange(1,5)) for o in range(m)],'workers':[[0,1],[0],[1]],'distances':[[r.randrange(0,15) for _ in range(n)] for o in range(m)],'maxDifference':seed%3,'balanceCoefficient':seed%5}
 if seed%7==0:data['workers']=[[0,1]]
 if seed%11==0:data['workers']=[]
 if seed%13==0:data['sites'][0]['tasks']=[2]
 best=0.;inc=[]
 for asg in itertools.product(range(-1,m),repeat=n):
  sites={o:[s for s in range(n) if asg[s]==o] for o in range(m)};ops=[o for o in range(m) if sites[o]]
  if any(len(sites[o])>data['offices'][o]['maxSize'] for o in ops):continue
  if ops and max(len(sites[o]) for o in ops)-min(len(sites[o]) for o in ops)>data['maxDifference']:continue
  for ws in itertools.product([-1]+ops,repeat=len(data['workers'])):
   sol=[dict(officeId=o,sites=sites[o],workers=[w for w,q in enumerate(ws) if q==o]) for o in ops];v=score(data,sol)
   if not isinstance(v,str):
    if v>best:best=v;inc=sol
    break
 (out/f'case{seed}.json').write_text(json.dumps(data))
 for backend in ['highs','scip']:
  result=improve(data,[],seconds=10,budget=n,backend=backend)
  ok=result['conditional_optimal'] and abs(result['value']-best)<1e-6
  row={'seed':seed,'backend':backend,'expected':best,'ok':ok,**result};rows.append(row)
  (out/'results.json').write_text(json.dumps(rows,indent=2));print(seed,backend,ok,best,result['value'],result['cuts'],flush=True)
  assert ok,row
print('PASS',len(rows))
