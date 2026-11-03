from master_perspective import *
import random,itertools
D=H/'logs/oracle_perspective';D.mkdir();results=[]
for seed in range(311000,311030):
 rng=random.Random(seed);n=6;m=2;xy=rng.sample([(x,y) for x in range(5) for y in range(5)],n+m)
 data=dict(sites=[dict(x=x,y=y,reward=rng.randint(0,40),tasks=rng.choice([[],[0],[1],[0,1],[0,0]])) for x,y in xy[:n]],offices=[dict(x=x,y=y,cost=rng.randint(0,12),maxSize=rng.randint(1,n)) for x,y in xy[n:]],workers=[[0],[1],[0,1]],distances=[[rng.randint(0,30) for _ in range(n)] for _ in range(m)],maxDifference=rng.choice([0,1,n]),balanceCoefficient=rng.choice([0,.5,5,30]))
 I=Instance(data);regions=[]
 for o in range(m):
  for j in range(3):
   ss=rng.sample(list(range(n)),rng.randint(1,n));mask=np.asarray(covers(MultiPoint(I.xy[ss+[n+o]]).convex_hull,I.points));foot=tuple(map(int,np.flatnonzero(mask)));regions.append(dict(o=o,sites=[s for s in foot if s<n],footprint=foot,tag='oracle'))
 feas=set()
 for wof in itertools.product(range(-1,m),repeat=I.w):
  masks=[0]*m
  for w,o in enumerate(wof):
   if o>=0:
    for k in I.workers[w]:masks[o]|=1<<k
  for req in itertools.product(range(4),repeat=m):
   if all(req[o]&masks[o]==req[o] for o in range(m)):feas.add(req)
 best=0
 for es in itertools.product([None,0,1,2],[None,3,4,5]):
  fs=[set(regions[e]['footprint']) for e in es if e is not None]
  if len(fs)==2 and fs[0]&fs[1]:continue
  choices=[]
  for o,e in enumerate(es):
   opts=[]
   if e is None:opts=[(0,0,0,0)]
   else:
    ss=regions[e]['sites']
    for bits in range(1,1<<len(ss)):
     sites=[s for j,s in enumerate(ss) if bits>>j&1]
     if len(sites)>I.cap[o]:continue
     req=sum(1<<k for k in {k for s in sites for k in I.sites[s]['tasks']});opts.append((len(sites),sum(int(I.tasks[s]) for s in sites),req,sum(float(I.profit[o,s]) for s in sites)-I.cost[o]))
   choices.append(opts)
  for cs in itertools.product(*choices):
   counts=[c[0] for c in cs if c[0]];loads=[c[1] for c in cs if c[0]]
   if not counts or max(counts)-min(counts)>I.a or tuple(c[2] for c in cs) not in feas:continue
   best=max(best,sum(c[3] for c in cs)-I.alpha*(max(loads)-min(loads)))
 r=improve(I,[],regions,{},seconds=10);assert not r['invalid'],r['invalid'];assert abs(r['value']-best)<1e-6,(seed,r['value'],best,r['status']);assert abs(r['bound']-best)<1e-6,(seed,r['bound'],best)
 (D/f'{seed}.json').write_text(json.dumps(dict(data=data,regions=regions,expected=best,result=r),indent=2));results.append(dict(seed=seed,expected=best,value=r['value'],status=r['status']));print(seed,best,flush=True)
(D/'results.json').write_text(json.dumps(results,indent=2))
