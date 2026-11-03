from regions import *
from conditional import improve
import json

def configurations(I,inc):
 ops=[r['officeId'] for r in inc];rank=[]
 for o in range(I.m):
  if o not in ops and I.cap[o]>0:
   ps=sorted((float(I.profit[o,s]) for s in range(I.n) if I.servable[s]),reverse=True);rank.append((sum(max(0,p) for p in ps[:I.cap[o]])-I.cost[o],o))
 for new in [None]+[o for _,o in sorted(rank,reverse=True)[:1]]:
  oo=ops+([] if new is None else [new]);dist=np.sum((I.xy[:,None,:]-I.xy[I.n+np.array(oo)][None,:,:])**2,axis=2)
  for bias in ([0] if new is None else [-.45,0,.45]):
   ds=dist.copy()
   if new is not None:ds[:,-1]+=bias*min(float(np.sum((I.xy[I.n+new]-I.xy[I.n+o])**2)) for o in ops)
   winner=np.argmin(ds,axis=1);pools={};count=np.zeros(I.n+I.m,int)
   for j,o in enumerate(oo):
    if winner[I.n+o]!=j:continue
    other=np.min(np.delete(ds,j,axis=1),axis=1) if len(oo)>1 else np.full(I.n+I.m,np.inf)
    ss=[int(s) for s in np.flatnonzero((winner[:I.n]==j)&(ds[:I.n,j]<other[:I.n])) if I.servable[s]]
    if not ss:continue
    mask=np.asarray(covers(MultiPoint(I.xy[ss+[I.n+o]]).convex_hull,I.points));count+=mask;pools[o]=[int(s) for s in np.flatnonzero(mask[:I.n]) if I.servable[s]]
   if count.max(initial=0)>1:continue
   yield pools,dict(new=new,bias=bias)

def run(I,sol,seconds=54,checkpoint=None):
 start=time.perf_counter();before=value(I,sol);best=sol;score=before;trials=[];configs=list(configurations(I,sol))
 for j,(pools,config) in enumerate(configs):
  left=seconds-(time.perf_counter()-start)
  if left<=.05:break
  r=improve(I,sol,seconds=left/(len(configs)-j),mode='joint',pools=pools,fixed_open=False,checkpoint=checkpoint)
  trials.append(dict(**config,**{k:v for k,v in r.items() if k!='solution'}))
  if r['value']>score:best,score=r['solution'],r['value']
  if checkpoint:Path(checkpoint).write_text(json.dumps(dict(solution=best,value=score,before=before,status='checkpoint')))
 return dict(solution=best,value=score,before=before,trials=trials,status='configs',seconds=time.perf_counter()-start)
