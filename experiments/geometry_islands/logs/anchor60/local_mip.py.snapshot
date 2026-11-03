"""Local assignment MIP with native SCIP lazy geometry; all other zones fixed.

Offline research, not a contest executable. Workers may be reassigned globally.
No relaxation is reported as the original instance's global upper bound.
"""
from collections import OrderedDict
from itertools import combinations
import json
import math
from pathlib import Path
import sys
import time

import numpy as np
from pyscipopt import Model,Conshdlr,SCIP_RESULT,quicksum

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'colgen'))
from model import Instance
from pricing import support
from test_models import validator


def objective(I,sol):
    return validator.validate_solution(validator.Instance.model_validate(I.data),
                                       [validator.OpenedOffice.model_validate(s) for s in sol])


class Geometry(Conshdlr):
    def __init__(self,I,offices,x,z,outside_covered):
        self.I,self.offices,self.x,self.z=I,offices,x,z
        self.outside=np.asarray(outside_covered,dtype=bool)
        self.cache=OrderedDict();self.added=set();self.checks=0;self.cuts=0;self.seconds=0.

    def violations(self,solution=None):
        start=time.perf_counter();self.checks+=1
        vals={k:self.model.getSolVal(solution,v) for k,v in self.x.items()}
        if any(abs(v-round(v))>1e-5 for v in vals.values()):return []
        ss={o:tuple(s for (p,s),v in vals.items() if p==o and v>.5) for o in self.offices}
        # SCIP may call checks on heuristic trials that still violate explicit
        # capacity rows; those are rejected by the linear handler, not geometry.
        if any(len(s)>self.I.cap[o] for o,s in ss.items()):return []
        signature=tuple(ss[o] for o in self.offices)
        if signature in self.cache:
            ans=self.cache[signature];self.cache.move_to_end(signature);return ans
        cols={o:self.I.column(o,s) for o,s in ss.items() if s}
        todo=[]
        def witness(o,p):
            w=support(self.I,o,ss[o],p)
            return tuple((o,s) for s in w) if w else ((o,-1),)
        for o,c in cols.items():
            bad=[p for p in c.footprint if self.outside[p]]
            if bad:
                for j in np.linspace(0,len(bad)-1,min(8,len(bad)),dtype=int):
                    todo.append(witness(o,bad[j]))
        for a,b in combinations(cols,2):
            bad=sorted(set(cols[a].footprint).intersection(cols[b].footprint))
            if bad:
                for j in np.linspace(0,len(bad)-1,min(8,len(bad)),dtype=int):
                    todo.append(tuple(sorted(witness(a,bad[j])+witness(b,bad[j]))))
        ans=list(dict.fromkeys(todo));self.cache[signature]=ans
        if len(self.cache)>4096:self.cache.popitem(last=False)
        self.seconds+=time.perf_counter()-start
        return ans

    def conscheck(self,constraints,solution,check_integrality,check_lp_rows,print_reason,completely,**kwargs):
        return {'result':SCIP_RESULT.INFEASIBLE if self.violations(solution) else SCIP_RESULT.FEASIBLE}

    def consenfolp(self,constraints,n_useful_conss,sol_infeasible):
        count=0
        for keys in self.violations():
            if keys not in self.added:
                self.added.add(keys);self.cuts+=1;count+=1
                self.model.addCons(quicksum(self.z[o] if s<0 else self.x[o,s] for o,s in keys)<=len(keys)-1)
        return {'result':SCIP_RESULT.CONSADDED if count else SCIP_RESULT.FEASIBLE}

    def conslock(self,constraint,locktype,nlockspos,nlocksneg):
        # Conservative locks prevent reductions/roundings that ignore geometry.
        for v in [*self.x.values(),*self.z.values()]:
            self.model.addVarLocksType(v,locktype,nlockspos+nlocksneg,nlockspos+nlocksneg)


def improve(I,incumbent,offices,seconds=1.,radius=None,extra=True):
    start=time.perf_counter();offices=sorted(set(offices));byo={s['officeId']:s for s in incumbent}
    fixed=[s for s in incumbent if s['officeId'] not in offices]
    covered=np.zeros(I.n+I.m,dtype=bool)
    for s in fixed:covered[list(I.column(s['officeId'],s['sites']).footprint)]=True
    offices=[o for o in offices if I.cap[o]>0 and not covered[I.n+o]]
    if not offices:return dict(solution=incumbent,value=objective(I,incumbent),seconds=time.perf_counter()-start,status='no_offices',cuts=0)
    old={s:o for o in offices for s in byo.get(o,{}).get('sites',[])}
    candidates=set(old)
    if extra:
        used={s for off in incumbent for s in off['sites']}
        free=[s for s in range(I.n) if s not in used and I.servable[s] and not covered[s]]
        best=sorted(free,key=lambda s:max(I.profit[o,s] for o in offices),reverse=True)
        candidates.update(best[:max(8,int(2*math.sqrt(max(1,len(old)))) )])
    candidates=sorted(s for s in candidates if I.servable[s] and not covered[s])
    m=Model('local service zones');m.hideOutput();m.setIntParam('parallel/maxnthreads',1)
    m.setIntParam('misc/usesymmetry',0)
    m.setBoolParam('misc/allowstrongdualreds',False);m.setBoolParam('misc/allowweakdualreds',False)
    m.setRealParam('limits/gap',1e-8)
    x={(o,s):m.addVar(vtype='B',name=f'x{o}_{s}') for o in offices for s in candidates}
    z={o:m.addVar(vtype='B',name=f'z{o}') for o in offices}
    alloff=sorted(set(offices)|{s['officeId'] for s in fixed})
    u={(o,w):m.addVar(vtype='B') for o in alloff for w in range(I.w)}
    for w in range(I.w):m.addCons(quicksum(u[o,w] for o in alloff)<=1)
    for o in offices:
        for w in range(I.w):m.addCons(u[o,w]<=z[o])
    for r in fixed:
        for k in set(k for s in r['sites'] for k in I.sites[s]['tasks']):
            m.addCons(quicksum(u[r['officeId'],w] for w in I.have[k])>=1)
    n={o:quicksum(x[o,s] for s in candidates) for o in offices}
    t={o:quicksum(int(I.tasks[s])*x[o,s] for s in candidates) for o in offices}
    for s in candidates:
        m.addCons(quicksum(x[o,s] for o in offices)<=1)
        for o in offices:
            m.addCons(x[o,s]<=z[o])
            for k in set(I.sites[s]['tasks']):m.addCons(x[o,s]<=quicksum(u[o,w] for w in I.have[k]))
    for o in offices:
        m.addCons(n[o]>=z[o]);m.addCons(n[o]<=I.cap[o]*z[o])
        for p in offices:
            if o!=p:m.addCons(n[o]-n[p]<=I.a+I.cap[o]*(2-z[o]-z[p]))
        for r in fixed:
            nf=len(r['sites'])
            m.addCons(n[o]-nf<=I.a+I.cap[o]*(1-z[o]))
            m.addCons(nf-n[o]<=I.a+nf*(1-z[o]))
    B=max(1,int(I.tasks.sum()))
    H=m.addVar(lb=0.,ub=B);L=m.addVar(lb=0.,ub=B);m.addCons(L<=H)
    for o in offices:m.addCons(t[o]<=H);m.addCons(L<=t[o]+B*(1-z[o]))
    for r in fixed:
        load=sum(int(I.tasks[s]) for s in r['sites']);m.addCons(H>=load);m.addCons(L<=load)
    if radius is not None:
        m.addCons(quicksum((1-x[o,s]) if old.get(s)==o else x[o,s] for o,s in x)<=radius)
    fixed_value=sum(float(I.profit[r['officeId'],r['sites']].sum()-I.cost[r['officeId']]) for r in fixed)
    m.setObjective(fixed_value+quicksum(float(I.profit[o,s])*v for (o,s),v in x.items())
                   -quicksum(float(I.cost[o])*z[o] for o in offices)-I.alpha*(H-L),'maximize')
    handler=Geometry(I,offices,x,z,covered)
    m.includeConshdlr(handler,'zone_geometry','input-point hull packing',chckpriority=-10,enfopriority=-10)
    cons=m.createCons(handler,'geometry');m.addPyCons(cons)
    warm=m.createSol()
    for (o,s),v in x.items():m.setSolVal(warm,v,int(old.get(s)==o))
    for o,v in z.items():m.setSolVal(warm,v,int(o in byo))
    for (o,w),v in u.items():m.setSolVal(warm,v,int(o in byo and w in byo[o]['workers']))
    loads=[sum(int(I.tasks[s]) for s in r['sites']) for r in incumbent]
    m.setSolVal(warm,H,max(loads,default=0));m.setSolVal(warm,L,min(loads,default=0))
    m.addSol(warm)
    m.setRealParam('limits/time',max(.001,seconds-(time.perf_counter()-start)))
    m.optimize();sol=m.getBestSol();answer=incumbent
    if sol is not None:
        answer=[dict(officeId=r['officeId'],sites=list(r['sites']),
                     workers=[w for w in range(I.w) if m.getSolVal(sol,u[r['officeId'],w])>.5]) for r in fixed]
        for o in offices:
            ss=[s for s in candidates if m.getSolVal(sol,x[o,s])>.5]
            if ss:answer.append(dict(officeId=o,sites=ss,workers=[w for w in range(I.w) if m.getSolVal(sol,u[o,w])>.5]))
    value=objective(I,answer)
    assert not isinstance(value,str),(value,offices)
    oldval=objective(I,incumbent)
    if value<oldval-1e-6:answer,value=incumbent,oldval
    return dict(solution=answer,value=value,seconds=time.perf_counter()-start,status=str(m.getStatus()),
                cuts=handler.cuts,checks=handler.checks,geometry_seconds=handler.seconds,
                candidates=len(candidates),offices=offices,variables=m.getNVars(),nodes=m.getNNodes())


if __name__=='__main__':
    from test_models import tiny
    from model import Master,reference_optimum
    rows=[]
    for j,mode in enumerate(['normal','multiskill','missing','A0','alpha_huge','duplicates','collinear','anti']):
        I=Instance(tiny(12000+j,mode=mode));cols=I.enumerate_columns();truth,_=reference_optimum(I,cols)
        r=improve(I,[],range(I.m),seconds=10.,radius=None)
        assert abs(r['value']-truth)<1e-5*max(1.,abs(truth)),(mode,r['value'],truth,r['status'])
        rows.append(dict(mode=mode,truth=truth,**{k:v for k,v in r.items() if k!='solution'}));print(json.dumps(rows[-1]),flush=True)
    (HERE/'logs/local_correctness.json').write_text(json.dumps(rows,indent=2))
