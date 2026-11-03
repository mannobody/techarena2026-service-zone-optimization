#!/usr/bin/env python3
"""Research oracle: joint selection/staff/closure inside incumbent convex hulls.

Every new hull is a subset of its incumbent hull, so no shared input point
can be introduced. This is exact for this restricted territory family, not
for the full optimization problem. The second mode drops geometry and
relaxes integrality with the opened-office set fixed: its optimum is only
a bound conditional on that office set.
"""
import argparse, collections, hashlib, json, math, sys, time
from pathlib import Path
import numpy as np
import shapely
from shapely import MultiPoint

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'experiments/v4_local_search'))
from repair_mip import Linear, Backend, score

def build(data, inc, relaxed=False):
    sites, offices, workers = data['sites'], data['offices'], data['workers']
    n = len(sites); ops = [r['officeId'] for r in inc]
    by = {r['officeId']:r for r in inc}
    old = {s:r['officeId'] for r in inc for s in r['sites']}
    profiles = collections.defaultdict(list)
    for w, ks in enumerate(workers):
        if ks: profiles[tuple(sorted(set(ks)))].append(w)
    xy = [(s['x'],s['y']) for s in sites]
    points = shapely.points(xy)
    pools = {}
    available = set(k for pr in profiles for k in pr)
    for o in ops:
        if relaxed: pool = range(n)
        else:
            h = MultiPoint([(offices[o]['x'],offices[o]['y'])]+[xy[s] for s in by[o]['sites']]).convex_hull
            pool = np.flatnonzero(shapely.covers(h, points)).tolist()
        pools[o] = [s for s in pool if set(sites[s]['tasks']) <= available]
    L = Linear()
    integer = not relaxed
    y = {o:L.var(c=offices[o]['cost'],lb=1 if relaxed else 0,integer=integer,w=1) for o in ops}
    x = {(o,s):L.var(c=data['distances'][o][s]-sites[s]['reward'],integer=integer,w=old.get(s)==o)
         for o in ops for s in pools[o]}
    u = {(o,pr):L.var(integer=integer,w=any(w in by[o]['workers'] for w in ws))
         for o in ops for pr,ws in profiles.items()}
    for pr,ws in profiles.items(): L.row([(u[o,pr],1) for o in ops],ub=len(ws))
    for (o,pr),j in u.items(): L.row([(j,1),(y[o],-1)],ub=0)
    assignments = collections.defaultdict(list)
    for (o,s),j in x.items():
        assignments[s].append((j,1))
        L.row([(j,1),(y[o],-1)],ub=0)
        for k in set(sites[s]['tasks']):
            L.row([(j,1)]+[(u[o,pr],-1) for pr in profiles if k in pr],ub=0)
    for terms in assignments.values(): L.row(terms,ub=1)
    tasks = [len(s['tasks']) for s in sites]
    T = max(1,sum(tasks)); alpha=data['balanceCoefficient']
    oldloads=[sum(tasks[s] for s in by[o]['sites']) for o in ops]
    oldcounts=[len(by[o]['sites']) for o in ops]
    hi=L.var(c=alpha,ub=T,integer=False,w=max(oldloads,default=0))
    lo=L.var(c=-alpha,ub=T,integer=False,w=min(oldloads,default=0))
    ch=L.var(ub=n,integer=False,w=max(oldcounts,default=0))
    cl=L.var(ub=n,integer=False,w=min(oldcounts,default=0))
    for o in ops:
        cnt=[(x[o,s],1) for s in pools[o]]
        load=[(x[o,s],tasks[s]) for s in pools[o]]
        L.row(cnt+[(y[o],-offices[o]['maxSize'])],ub=0)
        if not relaxed: L.row(cnt+[(y[o],-1)],lb=0)
        L.row(cnt+[(ch,-1)],ub=0)
        L.row([(j,-a) for j,a in cnt]+[(cl,1),(y[o],n)],ub=n)
        L.row(load+[(hi,-1)],ub=0)
        L.row([(j,-a) for j,a in load]+[(lo,1),(y[o],T)],ub=T)
    L.row([(lo,1),(hi,-1)],ub=0)
    L.row([(cl,1),(ch,-1)],ub=0)
    L.row([(ch,1),(cl,-1)],ub=data['maxDifference'])
    return L,(ops,profiles,y,x,u,pools)

def solve(data, inc, seconds, backend, relaxed=False):
    start=time.perf_counter(); before=score(data,inc)
    assert not isinstance(before,str),before
    L,meta=build(data,inc,relaxed)
    ops,profiles,y,x,u,pools=meta
    B=Backend(L,backend)
    prep=time.perf_counter()-start
    values,status,bound,nodes,optimal=B.solve(max(.001,seconds-prep))
    result={'before':before,'status':status,'optimal_in_restricted_family':optimal,
        'seconds':time.perf_counter()-start,'prep':prep,'nodes':nodes,'backend':backend,
        'relaxed':relaxed,'variables':len(L.cost),'rows':len(L.rows),
        'pool_sizes':{o:len(v) for o,v in pools.items()}}
    if relaxed:
        # Backend's generic mip_dual_bound is not the LP bound. Only an optimal
        # LP objective can certify the conditional relaxation bound here.
        result['fixed_offices_relaxation_bound']=(-sum(c*v for c,v in zip(L.cost,values))) if optimal and values is not None else None
        return result
    result['restricted_upper_bound']=bound
    result['gain']=0.;result['solution']=inc
    if values is not None:
        assert all(abs(values[j]-round(values[j]))<1e-5 for j,z in enumerate(L.integer) if z)
        active=[o for o in ops if values[y[o]]>.5]
        staff={o:[] for o in active}
        for pr,ws in profiles.items():
            need=[o for o in active if values[u[o,pr]]>.5]
            assert len(need)<=len(ws)
            for o,w in zip(need,ws):staff[o].append(w)
        sol=[{'officeId':o,'sites':[s for s in pools[o] if values[x[o,s]]>.5],'workers':staff[o]} for o in active]
        value=score(data,sol);result['validation']=value
        if isinstance(value,str):result['invalid_candidate']=sol
        elif value>before+1e-7:
            result['gain']=value-before;result['solution']=sol
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('instance');p.add_argument('incumbent');p.add_argument('output')
    p.add_argument('--seconds',type=float,default=30);p.add_argument('--backend',choices=['highs','scip'],default='highs')
    p.add_argument('--relaxed',action='store_true');a=p.parse_args()
    data=json.loads(Path(a.instance).read_text());inc=json.loads(Path(a.incumbent).read_text())
    result=solve(data,inc,a.seconds,a.backend,a.relaxed)
    result['inputs_sha256']={str(p):hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in [a.instance,a.incumbent,__file__]}
    Path(a.output).write_text(json.dumps(result,indent=2))
    print(json.dumps({k:v for k,v in result.items() if k not in ('solution','inputs_sha256')}))
