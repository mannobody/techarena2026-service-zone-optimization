"""Reopen a closed office by splitting the existing convex territory covering it.
Each child envelope is contained in that one old hull. Global MILP handles counts/workers.
Diagnostic operator, not enabled in the native candidate.
"""
from grouped import *
from grouped_flow import improve
from shapely import MultiPoint,covers

def search(I,inc,seconds=57,checkpoint=None):
 start=time.perf_counter();best=inc;before=value(I,inc);bestval=before;oldpool=territory(I,inc);by={r['officeId']:r for r in inc};pairs=[]
 for o in oldpool:
  covered=set(I.column(o,by[o]['sites']).footprint)
  for p in range(I.m):
   if p in by or I.cap[p]<=0 or I.n+p not in covered:continue
   delta=sum(max(0,float(I.profit[p,s]-I.profit[o,s])) for s in oldpool[o])-I.cost[p];pairs.append((delta,o,p))
 logs=[]
 for _,o,p in sorted(pairs,reverse=True)[:3]:
  origin=I.xy[I.n+o];target=I.xy[I.n+p];d=target-origin
  if np.linalg.norm(d)<1e-12:continue
  for theta in [-.5,0.,.5]:
   if time.perf_counter()-start>seconds-.1:break
   cs,sn=np.cos(theta),np.sin(theta);normal=np.array([cs*d[0]-sn*d[1],sn*d[0]+cs*d[1]]);mid=(origin+target)*.5
   pool={k:list(ss) for k,ss in oldpool.items()};pool[o]=[s for s in oldpool[o] if np.dot(I.xy[s]-mid,normal)<0];pool[p]=[s for s in oldpool[o] if np.dot(I.xy[s]-mid,normal)>=0]
   if not pool[o] or not pool[p]:continue
   # Independent whole-envelope check, including unserved sites and closed offices.
   counts=np.zeros(I.n+I.m,np.int32)
   for k,ss in pool.items():counts+=np.asarray(covers(MultiPoint(I.xy[ss+[I.n+k]]).convex_hull,I.points),dtype=np.int32)
   if counts.max(initial=0)>1:continue
   remaining=seconds-(time.perf_counter()-start);r=improve(I,inc,min(6,remaining),mode='joint',pools=pool,fixed_open=True);logs.append(dict(office=o,new=p,theta=theta,**{k:v for k,v in r.items() if k!='solution'}))
   if r['value']>bestval+1e-7:
    best,bestval=r['solution'],r['value']
    if checkpoint:
     path=Path(checkpoint);tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(dict(solution=best,before=before,value=bestval,seconds=time.perf_counter()-start,status='checkpoint',trials=logs)));tmp.replace(path)
 return dict(solution=best,before=before,value=bestval,seconds=time.perf_counter()-start,status='completed_trials',trials=logs)
