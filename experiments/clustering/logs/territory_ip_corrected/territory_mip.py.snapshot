"""Exact selection within incumbent hulls, with global binary worker reassignment.

No geometric callbacks: every selected site stays inside its old valid territory.
Conditional optimality/bounds refer only to these territories, not the instance.
"""
import time
import numpy as np
from pyscipopt import Model,quicksum
from embeddings import Instance,validator


def value(I,solution):
    return validator.validate_solution(validator.Instance.model_validate(I.data),
                                      [validator.OpenedOffice.model_validate(s) for s in solution])


def improve(I,incumbent,seconds=2.):
    start=time.perf_counter();before=value(I,incumbent);assert not isinstance(before,str)
    if not incumbent:return dict(solution=incumbent,value=before,seconds=time.perf_counter()-start,status='empty',candidates=0)
    ops=sorted(r['officeId'] for r in incumbent);by={r['officeId']:r for r in incumbent}
    owner=np.full(I.n,-1,dtype=int)
    for o in ops:
        col=I.column(o,by[o]['sites'])
        for p in col.footprint:
            if p>=I.n:continue
            assert owner[p] in (-1,o)
            owner[p]=o
    candidates=[s for s in range(I.n) if owner[s]>=0 and I.servable[s]]
    m=Model('fixed convex territories');m.hideOutput();m.setIntParam('parallel/maxnthreads',1)
    m.setRealParam('limits/gap',1e-8)
    x={s:m.addVar(vtype='B',name=f'x{s}') for s in candidates}
    z={o:m.addVar(vtype='B',name=f'z{o}') for o in ops}
    u={(o,w):m.addVar(vtype='B') for o in ops for w in range(I.w)}
    for w in range(I.w):m.addCons(quicksum(u[o,w] for o in ops)<=1)
    for o in ops:
        for w in range(I.w):m.addCons(u[o,w]<=z[o])
    n={};load={}
    for o in ops:
        ss=[s for s in candidates if owner[s]==o]
        n[o]=quicksum(x[s] for s in ss);load[o]=quicksum(int(I.tasks[s])*x[s] for s in ss)
        m.addCons(n[o]>=z[o]);m.addCons(n[o]<=I.cap[o]*z[o])
        for s in ss:
            m.addCons(x[s]<=z[o])
            for k in set(I.sites[s]['tasks']):m.addCons(x[s]<=quicksum(u[o,w] for w in I.have[k]))
    for o in ops:
        for p in ops:
            if o!=p:m.addCons(n[o]-n[p]<=I.a+I.cap[o]*(2-z[o]-z[p]))
    T=max(1,int(I.tasks.sum()));H=m.addVar(lb=0.,ub=T);L=m.addVar(lb=0.,ub=T);m.addCons(L<=H)
    for o in ops:
        m.addCons(load[o]<=H);m.addCons(L<=load[o]+T*(1-z[o]))
    m.setObjective(quicksum(float(I.profit[owner[s],s])*x[s] for s in candidates)
                   -quicksum(float(I.cost[o])*z[o] for o in ops)-I.alpha*(H-L),'maximize')
    warm=m.createSol();assigned={s:r['officeId'] for r in incumbent for s in r['sites']}
    for s,v in x.items():m.setSolVal(warm,v,int(s in assigned))
    for o,v in z.items():m.setSolVal(warm,v,1)
    for (o,w),v in u.items():m.setSolVal(warm,v,int(w in by[o]['workers']))
    loads=[sum(int(I.tasks[s]) for s in r['sites']) for r in incumbent]
    m.setSolVal(warm,H,max(loads));m.setSolVal(warm,L,min(loads));m.addSol(warm)
    m.setRealParam('limits/time',max(.001,seconds-(time.perf_counter()-start)))
    m.optimize();sol=m.getBestSol();answer=incumbent
    if sol is not None:
        answer=[]
        for o in ops:
            ss=[s for s in candidates if owner[s]==o and m.getSolVal(sol,x[s])>.5]
            if ss:answer.append(dict(officeId=o,sites=ss,workers=[w for w in range(I.w) if m.getSolVal(sol,u[o,w])>.5]))
    score=value(I,answer);assert not isinstance(score,str),score
    if score<before-1e-6:answer,score=incumbent,before
    return dict(solution=answer,value=score,seconds=time.perf_counter()-start,status=str(m.getStatus()),
                candidates=len(candidates),variables=m.getNVars(),nodes=m.getNNodes(),local_bound=float(m.getDualbound()))
