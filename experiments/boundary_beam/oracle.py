import random,itertools,json,subprocess,time,functools
from pathlib import Path
from shapely import MultiPoint,Point
H=Path(__file__).resolve().parent;D=H/'data/oracle';D.mkdir(exist_ok=True)
rows=[]
for seed in range(48):
 r=random.Random(101000+seed);m=3;n=8;mode=['normal','A0','bigalpha','multiskill','missing','collinear','duplicates','anti'][seed%8]
 xy=[(r.random()*10,r.random()*10) for _ in range(n)]
 xy[:3]=[(0,0),(10,0),(5,10)]
 if mode=='collinear':xy=[(x,0) for x,y in xy];xy[:3]=[(0,0),(10,0),(5,0)]
 if mode=='duplicates':xy[5]=xy[4]
 workers=[[0],[0],[0],[1],[1],[1]] if mode!='multiskill' else [[0,1],[0],[1]]
 if mode=='missing':workers=[[0],[0],[0]]
 sites=[dict(x=x,y=y,reward=r.randint(1,18),tasks=[] if i<m else [r.randrange(2) for _ in range(r.randrange(3))]) for i,(x,y) in enumerate(xy)]
 off=[dict(x=x,y=y,cost=1,maxSize=r.randint(3,6)) for x,y in xy[:3]]
 dist=[[r.randint(0,20) for s in sites] for o in off]
 for o in range(m):dist[o][o]=0
 data=dict(sites=sites,offices=off,workers=workers,distances=dist,maxDifference=0 if mode=='A0' else 8,balanceCoefficient=1000 if mode=='bigalpha' else .5)
 p=D/f'{seed}.json';p.write_text(json.dumps(data));assign=list(range(m))+[-1]*(n-m);ap=D/f'{seed}.asg';ap.write_text(' '.join(map(str,assign))+f' {n-m} '+' '.join(map(str,range(m,n))))
 points=[Point(x,y) for x,y in xy+xy[:3]]
 cols={}
 for o in range(m):
  for mask in range(1<<(n-m)):
   ss=[o]+[x for x in range(m,n) if mask>>(x-m)&1];hull=MultiPoint([xy[x] for x in ss]+[xy[o]]).convex_hull
   footprint=sum(1<<i for i,pnt in enumerate(points) if hull.covers(pnt));need=sum(1<<k for k in set(k for x in ss for k in sites[x]['tasks']))
   cols[o,mask]=(ss,footprint,need,sum(len(sites[x]['tasks']) for x in ss),sum(sites[x]['reward']-dist[o][x] for x in ss)-1)
 @functools.lru_cache(None)
 def staff(needs):
  for wa in itertools.product(range(-1,m),repeat=len(workers)):
   have=[0]*m
   for w,o in enumerate(wa):
    if o>=0:
     for k in workers[w]:have[o]|=1<<k
   if all(have[o]&needs[o]==needs[o] for o in range(m)):return True
  return False
 best=-1e100
 for a in itertools.product(range(-1,m),repeat=n-m):
  masks=[sum(1<<j for j,o in enumerate(a) if o==p) for p in range(m)];cs=[cols[o,masks[o]] for o in range(m)];sizes=[len(c[0]) for c in cs]
  if any(sizes[o]>off[o]['maxSize'] for o in range(m)) or max(sizes)-min(sizes)>data['maxDifference']:continue
  if any(cs[o][1]&cs[p][1] for o in range(m) for p in range(o)):continue
  if not staff(tuple(c[2] for c in cs)):continue
  loads=[c[3] for c in cs];best=max(best,sum(c[4] for c in cs)-data['balanceCoefficient']*(max(loads)-min(loads)))
 for strong in [0,1]:
  t=time.perf_counter();res=subprocess.run([str(H/'artifacts/oracle'),str(p),str(ap),str(strong)],capture_output=True,text=True,check=True);row=json.loads(res.stdout)
  assert row['valid'] and not row['stopped'] and abs(row['score']-best)<1e-7,(seed,best,row)
  rows.append(dict(seed=101000+seed,mode=mode,strong=strong,expected=best,wall=time.perf_counter()-t,**row))
(H/'logs/oracle.json').write_text(json.dumps(rows,indent=2));print(len(rows),'oracle checks passed')
