"""Conditional site-selection MILP. Assigned pool = same choices as resize_dp.
Territory pool may add sites within unchanged convex hulls. No geometric callbacks.
"""
from pathlib import Path
import sys,time
import numpy as np
from pyscipopt import Model,quicksum,Eventhdlr,SCIP_EVENTTYPE
import json
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H.parent/'colgen'))
from model import Instance
from test_models import validator

def value(I,sol):return validator.validate_solution(validator.Instance.model_validate(I.data),[validator.OpenedOffice.model_validate(s) for s in sol])
def improve(I,inc,seconds=60,mode='assigned',checkpoint_path=None):
 start=time.perf_counter();before=value(I,inc);assert not isinstance(before,str),before
 if not inc:return dict(solution=inc,value=before,status='empty',seconds=0,candidates=0)
 ops=[r['officeId'] for r in inc];by={r['officeId']:r for r in inc};owner={s:r['officeId'] for r in inc for s in r['sites']};joint=mode=='joint'
 if mode!='assigned':
  for o in ops:
   for p in I.column(o,by[o]['sites']).footprint:
    if p<I.n and I.servable[p]:assert p not in owner or owner[p]==o;owner[p]=o
 have={o:set(k for w in by[o]['workers'] for k in I.workers[w]) for o in ops}
 owner={s:o for s,o in owner.items() if joint or set(I.sites[s]['tasks'])<=have[o]}
 pool={o:[s for s,p in owner.items() if p==o] for o in ops};m=Model('conditional selection');m.hideOutput();m.setIntParam('parallel/maxnthreads',1);m.setRealParam('limits/gap',1e-9)
 x={s:m.addVar(vtype='B') for s in owner};z={o:m.addVar(vtype='B') for o in ops}
 u={(o,w):m.addVar(vtype='B') for o in ops for w in range(I.w)} if joint else {}
 if joint:
  for w in range(I.w):m.addCons(quicksum(u[o,w] for o in ops)<=1)
  for o in ops:
   for w in range(I.w):m.addCons(u[o,w]<=z[o])
 n={o:quicksum(x[s] for s in pool[o]) for o in ops};load={o:quicksum(int(I.tasks[s])*x[s] for s in pool[o]) for o in ops}
 for o in ops:
  m.addCons(n[o]>=z[o]);m.addCons(n[o]<=int(I.cap[o])*z[o])
  for s in pool[o]:
   m.addCons(x[s]<=z[o])
   if joint:
    for k in set(I.sites[s]['tasks']):m.addCons(x[s]<=quicksum(u[o,w] for w in I.have[k]))
  for p in ops:
   if o!=p:m.addCons(n[o]-n[p]<=I.a+int(I.cap[o])*(2-z[o]-z[p]))
 T=max(1,max(sum(int(I.tasks[s]) for s in pool[o]) for o in ops));hi=m.addVar(lb=0,ub=T);lo=m.addVar(lb=0,ub=T);m.addCons(lo<=hi)
 for o in ops:m.addCons(load[o]<=hi);m.addCons(lo<=load[o]+T*(1-z[o]))
 m.setObjective(quicksum(float(I.profit[o,s])*x[s] for s,o in owner.items())-quicksum(float(I.cost[o])*z[o] for o in ops)-I.alpha*(hi-lo),'maximize')

 def checkpoint():
  best=m.getBestSol()
  if best is None:return
  candidate=[]
  for o in ops:
   ss=[s for s in pool[o] if m.getSolVal(best,x[s])>.5]
   if ss:candidate.append(dict(officeId=o,sites=ss,workers=[w for w in range(I.w) if m.getSolVal(best,u[o,w])>.5] if joint else by[o]['workers']))
  score=value(I,candidate)
  if not isinstance(score,str) and score>=before-1e-7:
   dest=Path(checkpoint_path);tmp=dest.with_suffix('.tmp');tmp.write_text(json.dumps(dict(solution=candidate,value=score,before=before,status='checkpoint',seconds=time.perf_counter()-start,candidates=len(owner),mode=mode,rejected=None)));tmp.replace(dest)
 class BestEvent(Eventhdlr):
  def eventinit(self):self.model.catchEvent(SCIP_EVENTTYPE.BESTSOLFOUND,self)
  def eventexit(self):self.model.dropEvent(SCIP_EVENTTYPE.BESTSOLFOUND,self)
  def eventexec(self,event):checkpoint()
 if checkpoint_path:m.includeEventhdlr(BestEvent(),'save_best','validated offline checkpoint')
 warm=m.createSol();assigned={s for r in inc for s in r['sites']}
 for s in owner:m.setSolVal(warm,x[s],int(s in assigned))
 for o in ops:
  m.setSolVal(warm,z[o],1)
  if joint:
   for w in range(I.w):m.setSolVal(warm,u[o,w],int(w in by[o]['workers']))
 loads=[sum(int(I.tasks[s]) for s in r['sites']) for r in inc];m.setSolVal(warm,hi,max(loads));m.setSolVal(warm,lo,min(loads));m.addSol(warm)
 prep=time.perf_counter()-start;m.setRealParam('limits/time',max(.001,seconds-prep));m.optimize();best=m.getBestSol();answer=inc;rejected=None
 if best is not None:
  candidate=[]
  for o in ops:
   ss=[s for s in pool[o] if m.getSolVal(best,x[s])>.5]
   if ss:candidate.append(dict(officeId=o,sites=ss,workers=[w for w in range(I.w) if m.getSolVal(best,u[o,w])>.5] if joint else by[o]['workers']))
  score=value(I,candidate)
  if isinstance(score,str):rejected=score
  elif score>=before-1e-7:answer=candidate
 return dict(solution=answer,value=value(I,answer),before=before,status=str(m.getStatus()),seconds=time.perf_counter()-start,prep_seconds=prep,candidates=len(owner),variables=m.getNVars(),nodes=m.getNNodes(),bound=float(m.getDualbound()),gap=float(m.getGap()),rejected=rejected,mode=mode)
