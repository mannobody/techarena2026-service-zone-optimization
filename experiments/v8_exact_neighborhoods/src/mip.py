"""Full-domain conditional assignment MIP. No polygon separation assumptions.

geometry: active office set fixed, joint worker reassignment, selected boundary sites.
structure: office set variable, includes empty selected cores and closed candidates.
External site assignments are fixed. All input points, including unused sites and
closed offices, are geometry witnesses. Correct monotone support cuts only.
Identical Linear rows and warm start for SCIP and HiGHS.
"""
import collections, itertools, json, math, sys, time
from pathlib import Path
import numpy as np
import shapely
from shapely import MultiPoint, Point
from legacy_mip import Linear, Backend, score, choose_peel

def improve(data, inc, selected, offices=None, kind='structure', backend='highs', seconds=2, export=None):
    t0=time.perf_counter(); before=score(data,inc)
    assert isinstance(before,(float,int)),before
    assert data['balanceCoefficient']>=0 and all(o['cost']>=0 for o in data['offices'])
    n=len(data['sites']); m=len(data['offices']); selected=sorted(set(selected)); chosen=set(selected)
    by={r['officeId']:r for r in inc}; old={s:r['officeId'] for r in inc for s in r['sites']}
    ops=set(range(m) if offices is None else offices)
    assert all(old.get(s,-1)<0 or old[s] in ops for s in selected)
    fixed={o:[s for s,q in old.items() if q==o and s not in chosen] for o in range(m)}
    xy=[(s['x'],s['y']) for s in data['sites']]+[(o['x'],o['y']) for o in data['offices']]
    points=shapely.points(xy); tasks=[len(s['tasks']) for s in data['sites']]
    alpha=data['balanceCoefficient']; A=data['maxDifference']; T=max(1,sum(tasks)); L=Linear()
    p=lambda o,s:data['sites'][s]['reward']-data['distances'][o][s]
    profiles=collections.defaultdict(list)
    for w,skills in enumerate(data['workers']):profiles[tuple(sorted(set(skills)))].append(w)
    y={}
    for o in range(m):
        variable=kind=='structure' and o in ops
        lb=int(bool(fixed[o])) if variable else int(o in by)
        ub=1 if variable else int(o in by)
        y[o]=L.var(c=data['offices'][o]['cost'],lb=lb,ub=ub,w=o in by)
    x={(s,o):L.var(c=-p(o,s),w=old.get(s)==o) for s in selected for o in sorted(ops)
       if kind=='structure' or o in by}
    for s in selected:L.row([(j,1) for (ss,o),j in x.items() if ss==s],ub=1)
    # A profile can be used at most once in each office: extra identical workers
    # provide no extra skill and tasks have no worker capacity. This is exact.
    u={(o,pr):L.var(w=any(w in by.get(o,{}).get('workers',[]) for w in ws))
       for o in range(m) for pr,ws in profiles.items() if pr}
    for pr,ws in profiles.items():
        if pr:L.row([(u[o,pr],1) for o in range(m)],ub=len(ws))
    for (o,pr),j in u.items():L.row([(j,1),(y[o],-1)],ub=0)
    for o in range(m):
        for k in {k for s in fixed[o] for k in data['sites'][s]['tasks']}:
            L.row([(u[o,pr],1) for pr in profiles if k in pr],lb=1)
        for (s,q),j in x.items():
            if q==o:
                for k in set(data['sites'][s]['tasks']):
                    L.row([(j,1)]+[(u[o,pr],-1) for pr in profiles if k in pr],ub=0)
    loads=[sum(tasks[s] for s in r['sites']) for r in inc]; counts=[len(r['sites']) for r in inc]
    hi=L.var(c=alpha,ub=T,integer=False,w=max(loads,default=0))
    lo=L.var(c=-alpha,ub=T,integer=False,w=min(loads,default=0))
    ch=L.var(ub=n,integer=False,w=max(counts,default=0)); cl=L.var(ub=n,integer=False,w=min(counts,default=0))
    for o in range(m):
        sz=len(fixed[o]); ld=sum(tasks[s] for s in fixed[o])
        cnt=[(j,1) for (s,q),j in x.items() if q==o]; load=[(j,tasks[s]) for (s,q),j in x.items() if q==o]
        L.row(cnt+[(y[o],-data['offices'][o]['maxSize'])],ub=-sz)
        L.row(cnt+[(y[o],-1)],lb=-sz) # empty open offices dominated for cost,alpha>=0
        L.row(cnt+[(ch,-1)],ub=-sz)
        L.row([(j,-a) for j,a in cnt]+[(cl,1),(y[o],n)],ub=n+sz)
        L.row(load+[(hi,-1)],ub=-ld)
        L.row([(j,-a) for j,a in load]+[(lo,1),(y[o],T)],ub=T+ld)
    L.row([(lo,1),(hi,-1)],ub=0); L.row([(cl,1),(ch,-1)],ub=0)
    L.row([(ch,1),(cl,-1)],ub=A)
    constant=sum(p(o,s) for o,ss in fixed.items() for s in ss)
    B=Backend(L,backend); build=time.perf_counter()-t0
    if export:
        ep=Path(export); ep.parent.mkdir(parents=True,exist_ok=True)
        if backend=='highs':B.solver.writeModel(str(ep.with_suffix('.lp')))
        else:B.solver.writeProblem(str(ep.with_suffix('.lp')),verbose=False)
        ep.with_suffix('.matrix.json').write_text(json.dumps(dict(cost=L.cost,lb=L.lb,ub=L.ub,
            integer=L.integer,warm=L.warm,rows=L.rows,constant=constant)))
    best=inc; bestvalue=before; cuts=set(); events=[]; solve_time=check_time=restore_time=0
    status='budget_in_build'; bound=math.inf; optimal=False; iterations=nodes=0
    while time.perf_counter()-t0<seconds:
        tick=time.perf_counter(); vals,status,ub,nn,opt=B.solve(seconds-(tick-t0)); solve_time+=time.perf_counter()-tick
        iterations+=1; nodes+=nn; bound=ub+constant
        if vals is None:break
        tick=time.perf_counter()
        if any(abs(vals[j]-round(vals[j]))>1e-5 for j,z in enumerate(L.integer) if z):status='fractional';break
        mem={o:fixed[o]+[s for (s,q),j in x.items() if q==o and vals[j]>.5] for o in range(m)}
        active=[o for o in range(m) if vals[y[o]]>.5]
        covered={o:np.flatnonzero(shapely.covers(MultiPoint([xy[n+o]]+[xy[s] for s in mem[o]]).convex_hull,points)) for o in active}
        owner={}; conflicts=[]
        for o in active:
            for q in covered[o]:
                if int(q) in owner:conflicts.append((owner[int(q)],o,int(q)))
                else:owner[int(q)]=o
        added=0
        if conflicts:
            for a,b,q in conflicts[:16]:
                support=[]
                for o in (a,b):
                    variable=[s for s in mem[o] if s in chosen]; core=[xy[n+o]]+[xy[s] for s in fixed[o]]
                    for s in list(variable):
                        trial=[z for z in variable if z!=s]
                        if MultiPoint(core+[xy[z] for z in trial]).convex_hull.covers(Point(xy[q])):variable=trial
                    support.extend(x[s,o] for s in variable);support.append(y[o])
                key=tuple(sorted(set(support))); assert key
                if key not in cuts:cuts.add(key);B.cut(key);added+=1
                if time.perf_counter()-t0>=seconds:break
            check_time+=time.perf_counter()-tick
            events.append(dict(iteration=iterations,conflicts=len(conflicts),cuts=added,bound=bound,seconds=time.perf_counter()-t0))
            if not added:status='cut_stall';break
            B.warm(L.warm);continue
        check_time+=time.perf_counter()-tick; tick=time.perf_counter();staff={o:[] for o in active}
        for pr,ws in profiles.items():
            if not pr:continue
            need=[o for o in active if vals[u[o,pr]]>.5]
            assert len(need)<=len(ws)
            for o,w in zip(need,ws):staff[o].append(w)
        sol=[dict(officeId=o,sites=sorted(mem[o]),workers=staff[o]) for o in active]
        v=score(data,sol); assert isinstance(v,(float,int)),v
        if v>=bestvalue-1e-7:best=sol;bestvalue=v
        restore_time+=time.perf_counter()-tick; optimal=opt;break
    total=time.perf_counter()-t0
    return dict(solution=best,before=before,value=bestvalue,gain=bestvalue-before,kind=kind,backend=backend,
        conditional_optimal=optimal,status=status,bound=bound,gap=max(0,bound-bestvalue)/max(1,abs(bestvalue)),
        build=build,solve=solve_time,check=check_time,restore=restore_time,seconds=total,
        gain_per_second=(bestvalue-before)/total,iterations=iterations,nodes=nodes,cuts=len(cuts),
        variables=len(L.cost),rows=len(L.rows),selected=selected,offices=sorted(ops),events=events)

if __name__=='__main__':
    import argparse
    a=argparse.ArgumentParser();a.add_argument('instance');a.add_argument('incumbent');a.add_argument('output')
    a.add_argument('--seconds',type=float,default=2);a.add_argument('--budget',type=int,default=12)
    a.add_argument('--backend',choices=['highs','scip'],default='highs');a.add_argument('--kind',choices=['geometry','structure'],default='structure')
    q=a.parse_args();d=json.loads(Path(q.instance).read_text());inc=json.loads(Path(q.incumbent).read_text())
    selected=choose_peel(d,inc,q.budget) if q.kind=='geometry' else list(range(min(len(d['sites']),q.budget)))
    r=improve(d,inc,selected,kind=q.kind,backend=q.backend,seconds=q.seconds,export=q.output)
    Path(q.output).write_text(json.dumps(r,indent=2));print(json.dumps({k:v for k,v in r.items() if k not in ('solution','events','selected')}))
