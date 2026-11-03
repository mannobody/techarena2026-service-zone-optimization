"""SCIP pricing with lazy-in-an-outer-loop Caratheodory geometry cuts.

This is a research oracle, not a contest entry. Every relaxed MIP dual bound is
an upper bound on full pricing, even if separation/time limit has not finished.
"""
import math
import time
import numpy as np
from shapely import MultiPoint, Point, Polygon
from pyscipopt import Model, quicksum

from model import cg_enumerated


def support(I, o, sites, p):
    """Return <=3 selected sites/office whose closed convex hull covers p."""
    ids = [*sites, I.n+o]
    bycoord = {tuple(I.xy[i]): i for i in ids}
    hull = MultiPoint(I.xy[ids]).convex_hull
    target = Point(I.xy[p])
    if hull.geom_type == 'Point':
        witness = [bycoord[tuple(hull.coords[0])]]
    elif hull.geom_type == 'LineString':
        witness = [bycoord[tuple(q)] for q in hull.coords]
    else:
        xy = list(hull.exterior.coords)[:-1]
        witness = None
        for i in range(1, len(xy)-1):
            tri = [xy[0], xy[i], xy[i+1]]
            if Polygon(tri).covers(target):
                witness = [bycoord[tuple(q)] for q in tri]
                break
        if witness is None:
            # Numerical fallback: all selected points also give a valid cut.
            witness = ids
    return tuple(sorted(i for i in witness if i < I.n))


def price_scip(master, o, dual, seconds=1.):
    start = time.perf_counter()
    I = master.I
    eligible = [i for i in range(I.n) if I.servable[i]]
    if I.cap[o] == 0 or not eligible:
        return dict(column=None, columns=[], rc=-math.inf, bound=-math.inf, exact=True, cuts=0, solves=0, seconds=0.)
    constant, weights, skillprices, rho = master.pricing_parts(o, dual)
    s = Model('zone pricing'); s.hideOutput()
    s.setIntParam('parallel/maxnthreads', 1)
    s.setRealParam('limits/gap', 1e-9)
    x = {i: s.addVar(vtype='B', obj=float(weights[i])) for i in eligible}
    req = {k for i in eligible for k in I.sites[i]['tasks']}
    b = {k: s.addVar(vtype='B', obj=-skillprices[k]) for k in req}
    # Zero-priced footprint variables do not affect pricing; omit them completely.
    h = {p: s.addVar(vtype='B', obj=-float(v)) for p, v in enumerate(rho) if v > 1e-10}
    for i in eligible:
        if i in h:
            s.addCons(x[i] <= h[i])
        for k in set(I.sites[i]['tasks']):
            s.addCons(x[i] <= b[k])
    if I.n+o in h:
        s.addCons(h[I.n+o] == 1.)
    n = quicksum(x.values())
    s.addCons(n >= 1); s.addCons(n <= I.cap[o])
    if master.window:
        base, lo, hi = master.window
        s.addCons(n >= base); s.addCons(n <= base+I.a)
        t = quicksum(int(I.tasks[i])*x[i] for i in eligible)
        s.addCons(t >= lo); s.addCons(t <= hi)
    s.setObjective(s.getObjective()+constant, 'maximize')
    bestc, bestrc, bound = None, -math.inf, math.inf
    seen = {}
    cuts, solves, status, exact = set(), 0, 'not_started', False
    while time.perf_counter()-start < seconds:
        # Account for either an accumulated or restarted SCIP clock; the wall
        # deadline includes Python model construction and separation as well.
        s.setRealParam('limits/time', s.getSolvingTime()+max(.001, seconds-(time.perf_counter()-start)))
        s.optimize(); solves += 1
        status = str(s.getStatus())
        if status == 'infeasible':
            bound, exact = -math.inf, True
            break
        rawbound = float(s.getDualbound())
        if abs(rawbound) < 1e19:
            bound = min(bound, rawbound)
        sol = s.getBestSol()
        if sol is None:
            break
        ss = [i for i in eligible if s.getSolVal(sol, x[i]) > .5]
        c = I.column(o, ss)
        if c is None:
            break
        rc = master.rc(c, dual)
        seen[c.key] = c
        if rc > bestrc:
            bestc, bestrc = c, rc
        missing = [p for p in c.footprint if p in h and s.getSolVal(sol, h[p]) < .5]
        if not missing:
            exact = status == 'optimal'
            break
        todo = []
        for p in missing:
            w = support(I, o, ss, p)
            key = (p, w)
            if key not in cuts:
                cuts.add(key); todo.append(key)
        if not todo or time.perf_counter()-start >= seconds:
            break
        s.freeTransform()
        for p, w in todo:
            s.addCons(h[p] >= quicksum(x[i] for i in w) - len(w) + 1)
    cheap = master.relaxed_pricing_bound(o, dual)
    bound = min(bound, cheap)
    # Guard against minor floating-point discrepancies without hiding real errors.
    if bestc is not None and bound < bestrc-1e-5*max(1.,abs(bestrc)):
        raise AssertionError(('pricing bound below feasible reduced cost', bound, bestrc))
    return dict(column=bestc, columns=list(seen.values()), rc=bestrc, bound=max(bound, bestrc), exact=exact,
                cuts=len(cuts), solves=solves, seconds=time.perf_counter()-start, status=status)


def cg_scip(master, initial, seconds=15., price_seconds=.5):
    start = time.perf_counter()
    pool = list({c.key:c for c in initial if c is not None and master.accepts(c)}.values())
    keys = {c.key for c in pool}; trace = []
    converged, result = False, None
    price_cap = price_seconds
    while time.perf_counter()-start < seconds:
        result = master.solve(pool, seconds=max(.001, seconds-(time.perf_counter()-start)))
        if result['dual'] is None or result['status'] != 'Optimal':
            break
        dual = result['dual']
        correction = cuts = solves = added = 0
        exact = True; maxrc = -math.inf
        for o in range(master.I.m):
            left = seconds-(time.perf_counter()-start)
            if left <= 0:
                # Uncalled offices still need safe upper bounds for a certificate.
                correction += max(0., master.relaxed_pricing_bound(o, dual)); exact = False
                continue
            p = price_scip(master, o, dual, seconds=min(price_cap, left))
            correction += max(0., p['bound']); cuts += p['cuts']; solves += p['solves']
            exact = exact and p['exact']; maxrc = max(maxrc, p['rc'])
            for c in p['columns']:
                if master.rc(c,dual) > 1e-7 and c.key not in keys:
                    keys.add(c.key); pool.append(c); added += 1
        trace.append(dict(round=len(trace), rmp=result['value'], columns=len(result['columns']),
                          certificate=max(0.,result['dual_base']+correction), max_rc=maxrc, exact_pricing=exact,
                          added=added, cuts=cuts, mip_solves=solves, wall=time.perf_counter()-start,
                          price_cap=price_cap))
        if correction < 1e-6:
            converged = True
            break
        if not added:
            left = seconds-(time.perf_counter()-start)
            if left < .01:
                break
            # A failed short heuristic/exact attempt is not a convergence proof.
            # Retry with a larger pricing budget while any certificate gap remains.
            price_cap = min(2.*price_cap, left)
    return dict(result=result, pool=pool, trace=trace, converged=converged,
                upper_bound=min((r['certificate'] for r in trace),default=math.inf),
                seconds=time.perf_counter()-start)
