"""Safe territory enlargement independent of capacity/count/skills decisions.
Keeps every incumbent hull and all input-point packing; optional uncovered offices.
"""
from grouped import *
from shapely import MultiPoint,covers,Point

def expand(I,inc,seconds=2,open_new=False,max_attempts=5000):
 start=time.perf_counter();end=start+seconds;by={r['officeId']:r for r in inc};hulls={o:MultiPoint(I.xy[r['sites']+[I.n+o]]).convex_hull for o,r in by.items()};masks={o:np.asarray(covers(h,I.points)) for o,h in hulls.items()};count=np.zeros(I.n+I.m,np.int32)
 for mask in masks.values():count+=mask
 assert count.max(initial=0)<=1
 candidates=[]
 if open_new:
  for o in range(I.m):
   if o in by or not I.cap[o] or count[I.n+o]:continue
   pp=sorted((float(I.profit[o,s]) for s in range(I.n) if I.servable[s] and not count[s]),reverse=True)
   optimistic=sum(max(0,p) for p in pp[:I.cap[o]])-I.cost[o];candidates.append((optimistic,o))
  for _,o in sorted(candidates,reverse=True)[:3]:
   hull=Point(I.xy[I.n+o]);mask=np.asarray(covers(hull,I.points))
   if np.any(count[mask]):continue
   hulls[o]=hull;masks[o]=mask;count+=mask
 offers=[]
 for o in hulls:
  ss=[s for s in range(I.n) if I.servable[s] and not count[s] and I.profit[o,s]>0]
  ss=sorted(ss,key=lambda s:float(I.profit[o,s]),reverse=True)[:(2048 if o not in by else 64)]
  offers.extend((float(I.profit[o,s]),o,s) for s in ss)
 attempts=accepted=0
 for _,o,s in sorted(offers,key=lambda t:(t[1] not in by,t[0]),reverse=True):
  if attempts>=max_attempts or time.perf_counter()>=end:break
  if count[s] and not masks[o][s]:continue
  if masks[o][s]:continue
  attempts+=1;h=hulls[o];xy=list(h.exterior.coords) if h.geom_type=='Polygon' else list(h.coords);trial=MultiPoint(xy+[tuple(I.xy[s])]).convex_hull;mask=np.asarray(covers(trial,I.points))
  if np.any((count-masks[o].astype(np.int32))[mask]):continue
  count-=masks[o];count+=mask;masks[o]=mask;hulls[o]=trial;accepted+=1
 pools={o:[int(s) for s in np.flatnonzero(mask[:I.n]) if I.servable[s]] for o,mask in masks.items()}
 return pools,dict(expand_seconds=time.perf_counter()-start,attempts=attempts,accepted=accepted,proposed_offices=sorted(set(pools)-set(by)))
