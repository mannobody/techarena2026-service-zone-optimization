"""Candidate convex envelopes; all input points participate in packing."""
from pathlib import Path
import sys,time
import numpy as np
from shapely import MultiPoint,covers
H=Path(__file__).resolve().parent
sys.path.insert(0,str(H.parent/'milp_v5'))
from grouped import Instance,value

def generate(I,inc,mode='both',seconds=4):
 start=time.perf_counter();end=start+seconds;regions=[];seen=set();base={};ops=[r['officeId'] for r in inc]
 def add(o,sites,tag,blocked=None):
  ss=list(map(int,sites));h=MultiPoint(I.xy[ss+[I.n+o]]).convex_hull;mask=np.asarray(covers(h,I.points))
  if blocked is not None and np.any(mask&blocked):return None
  footprint=tuple(map(int,np.flatnonzero(mask)));key=(o,footprint)
  if key in seen:return None
  seen.add(key);pool=[s for s in footprint if s<I.n and I.servable[s]]
  if not pool or I.cap[o]<=0:return None
  regions.append(dict(o=o,sites=pool,footprint=footprint,tag=tag));return len(regions)-1
 for r in inc:base[r['officeId']]=add(r['officeId'],r['sites'],'base')
 masks={o:np.isin(np.arange(I.n+I.m),regions[e]['footprint']) for o,e in base.items()};count=sum(masks.values(),np.zeros(I.n+I.m,int));assert count.max(initial=0)<=1
 pairs=[]
 for i,o in enumerate(ops):
  for p in ops[i+1:]:
   ss=sorted(set(regions[base[o]]['sites']+regions[base[p]]['sites']))
   gain=sum(max(0,float(I.profit[p,s]-I.profit[o,s])) for s in regions[base[o]]['sites'])+sum(max(0,float(I.profit[o,s]-I.profit[p,s])) for s in regions[base[p]]['sites'])
   dist=float(np.sum((I.xy[I.n+o]-I.xy[I.n+p])**2));pairs.append((gain/(1+dist**.5),o,p))
 if mode in ('pair','both'):
  for _,o,p in sorted(pairs,reverse=True)[:3]:
   if time.perf_counter()>end:break
   blocked=(count-masks[o].astype(int)-masks[p].astype(int))>0
   available=[s for s in range(I.n) if I.servable[s] and not blocked[s]]
   free=sorted((s for s in available if not count[s]),key=lambda s:max(I.profit[o,s],I.profit[p,s]),reverse=True)[:256]
   pool=sorted(set(regions[base[o]]['sites']+regions[base[p]]['sites']+free));a=I.xy[I.n+o];b=I.xy[I.n+p];d=b-a
   if np.dot(d,d)==0:continue
   for rot,t in [(0,.25),(0,.5),(0,.75),(.5,.5),(-.5,.5)]:
    normal=d+rot*np.array([-d[1],d[0]]);proj=I.xy@normal;cut=(1-t)*proj[I.n+o]+t*proj[I.n+p]
    for office,left in [(o,True),(p,False)]:
     ss=[s for s in pool if (proj[s]<cut if left else proj[s]>cut)]
     if add(office,ss,'pair',blocked) is None:
      # A convex union may cross a third zone: build a safe subset greedily.
      cur=[];attempts=0
      for s in sorted(ss,key=lambda s:float(I.profit[office,s]),reverse=True):
       if time.perf_counter()>end or attempts>=256:break
       attempts+=1;h=MultiPoint(I.xy[cur+[s,I.n+office]]).convex_hull;mask=np.asarray(covers(h,I.points))
       if not np.any(mask&blocked):cur.append(s)
      add(office,cur,'pair_greedy',blocked)
 if mode in ('power','both') and time.perf_counter()<end:
  ranks=[]
  for o in range(I.m):
   if o not in ops and I.cap[o]>0:
    ps=sorted((float(I.profit[o,s]) for s in range(I.n) if I.servable[s]),reverse=True);ranks.append((sum(max(0,p) for p in ps[:I.cap[o]])-I.cost[o],o))
  fresh=[o for _,o in sorted(ranks,reverse=True)[:1]]
  for new in [None]+fresh:
   oo=ops+([] if new is None else [new]);dist=np.sum((I.xy[:,None,:]-I.xy[I.n+np.array(oo)][None,:,:])**2,axis=2)
   for bias in ([0] if new is None else [-.45,0,.45]):
    if time.perf_counter()>end:break
    ds=dist.copy()
    if new is not None:
     scale=min(float(np.sum((I.xy[I.n+new]-I.xy[I.n+o])**2)) for o in ops)
     ds[:,-1]+=bias*scale
    winner=np.argmin(ds,axis=1)
    for j,o in enumerate(oo):
     if winner[I.n+o]!=j:continue
     # Strict cells exclude ties, except the office; packing catches degeneracy.
     other=np.min(np.delete(ds,j,axis=1),axis=1) if len(oo)>1 else np.full(I.n+I.m,np.inf)
     ss=[int(s) for s in np.flatnonzero((winner[:I.n]==j)&(ds[:I.n,j]<other[:I.n])) if I.servable[s]]
     add(o,ss,'power_new' if new is not None else 'power')
 return regions,base,dict(region_seconds=time.perf_counter()-start,regions=len(regions),region_sites=sum(len(e['sites']) for e in regions),new_offices=sorted({e['o'] for e in regions}-set(ops)),tags={t:sum(e['tag']==t for e in regions) for t in {e['tag'] for e in regions}})
