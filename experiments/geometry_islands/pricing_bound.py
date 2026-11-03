"""Validate geometry-aware Lagrangian pricing bounds on exhaustive finite models."""
import json,random,subprocess,itertools,math
from pathlib import Path
from shapely.geometry import MultiPoint,Point
H=Path(__file__).resolve().parent;rows=[]
for seed in range(24):
 r=random.Random(151000+seed);n=8;xy=[(r.random(),r.random()) for _ in range(n+3)];profit=[r.randint(-3,16) for _ in range(n)];tasks=[r.randint(1,4) for _ in range(n)];price=[r.uniform(0,5) for _ in xy];cap=r.randint(2,6);limit=r.randint(4,15)
 opts=[];best=-1e100
 for bits in range(1<<n):
  S=[i for i in range(n) if bits>>i&1]
  if len(S)>cap or sum(tasks[i] for i in S)>limit:continue
  hull=MultiPoint([xy[0]]+[xy[i+1] for i in S]).convex_hull;covered=[j for j,p in enumerate(xy) if hull.covers(Point(p))]
  best=max(best,sum(profit[i] for i in S)-sum(price[j] for j in covered))
 ubs=[];flat=[]
 for mu,nu in itertools.product([0,1,2,4,8,16],[0,.5,1,2,4]):
  w=[-x for x in price]
  for i in range(n):w[i+1]+=max(0,profit[i]-mu-nu*tasks[i])
  text=f'{len(xy)} {n+1} 0 0\n'+''.join(f'{x:.17g} {y:.17g} {v:.17g} 0\n' for (x,y),v in zip(xy,w))+' '.join(map(str,range(n+1)))+'\n'
  p=subprocess.run([str(H/'artifacts/oracle_v2')],input=text,text=True,capture_output=True,timeout=65);v=float(p.stdout.split()[0]);ub=mu*cap+nu*limit+v
  assert ub>=best-1e-7,(seed,mu,nu,ub,best)
  ubs.append(dict(mu=mu,nu=nu,bound=ub));flat.append(mu*cap+nu*limit-price[0]+sum(max(0,profit[i]-price[i+1]-mu-nu*tasks[i]) for i in range(n)))
 b=min(ubs,key=lambda x:x['bound']);rows.append(dict(seed=151000+seed,cap=cap,task_limit=limit,optimum=best,island_upper=b['bound'],geometry_ignored_upper=min(flat),multipliers=b,all_bounds=ubs,input=dict(points=xy,profits=profit,tasks=tasks,point_prices=price)))
(H/'logs/pricing_bound.json').write_text(json.dumps(rows,indent=2));print('verified',len(rows)*30,'bounds');print('strictly stronger',sum(r['island_upper']<r['geometry_ignored_upper']-1e-6 for r in rows));print('closed gaps',sum(abs(r['island_upper']-r['optimum'])<1e-6 for r in rows));print('mean absolute tightening',sum(r['geometry_ignored_upper']-r['island_upper'] for r in rows)/len(rows))
