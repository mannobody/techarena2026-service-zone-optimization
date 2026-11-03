"""Research models, deliberately separate from the contest executable.

Maximization convention throughout. Every column stores ALL covered input points,
including unserved sites and closed offices. Worker assignments stay in the master.
"""
from dataclasses import dataclass
from itertools import combinations, product
import json
import math
import time

import highspy
import numpy as np
from scipy.sparse import coo_matrix, csc_matrix
from shapely import MultiPoint, points, covers


@dataclass(frozen=True)
class Column:
    office: int
    sites: tuple
    footprint: tuple
    skills: tuple
    load: int
    value: float

    @property
    def key(self):
        return self.office, self.sites


class Instance:
    def __init__(self, data):
        self.data = data
        self.sites, self.offices, self.workers = (data[k] for k in ('sites', 'offices', 'workers'))
        self.n, self.m, self.w = len(self.sites), len(self.offices), len(self.workers)
        self.a, self.alpha = data['maxDifference'], data['balanceCoefficient']
        self.tasks = np.array([len(s['tasks']) for s in self.sites], dtype=np.int64)
        self.cap = [min(self.n, max(0, o['maxSize'])) for o in self.offices]
        self.cost = np.array([o['cost'] for o in self.offices], dtype=float)
        self.profit = np.array([[s['reward'] - data['distances'][o][i]
                                 for i, s in enumerate(self.sites)] for o in range(self.m)], dtype=float)
        self.skills = sorted({k for s in self.sites for k in s['tasks']} |
                             {k for w in self.workers for k in w})
        self.have = {k: [w for w, ss in enumerate(self.workers) if k in ss] for k in self.skills}
        self.servable = [all(self.have[k] for k in s['tasks']) for s in self.sites]
        self.xy = np.array([(p['x'], p['y']) for p in [*self.sites, *self.offices]], dtype=float).reshape(-1, 2)
        self.points = points(self.xy)
        self.maxload = max((sum(sorted(self.tasks, reverse=True)[:c]) for c in self.cap), default=0)
        self._cache = {}

    @classmethod
    def read(cls, path):
        with open(path) as f:
            return cls(json.load(f))

    def column(self, office, sites):
        ss = tuple(sorted(set(sites)))
        if not ss or len(ss) > self.cap[office] or any(not self.servable[s] for s in ss):
            return None
        key = (office, ss)
        if key not in self._cache:
            hull = MultiPoint(self.xy[[*ss, self.n + office]]).convex_hull
            footprint = tuple(np.flatnonzero(covers(hull, self.points)).tolist())
            req = tuple(sorted({k for s in ss for k in self.sites[s]['tasks']}))
            self._cache[key] = Column(office, ss, footprint, req, int(self.tasks[list(ss)].sum()),
                                      float(self.profit[office, list(ss)].sum() - self.cost[office]))
        return self._cache[key]

    def enumerate_columns(self):
        eligible = [s for s in range(self.n) if self.servable[s]]
        return [self.column(o, ss) for o in range(self.m)
                for k in range(1, min(self.cap[o], len(eligible)) + 1)
                for ss in combinations(eligible, k)]


class Master:
    """Sparse exact IP model; continuous relaxation exposes prices and certificates.

    Without windows: conditional count balance and task range use finite valid M.
    window=(min_count, lo_load, hi_load) filters columns, eliminates every big-M
    balance row and subtracts alpha*(hi-lo) from the objective (empty stays 0).
    geometry='point', 'pair', or 'none' is used only for controlled ablations.
    """
    def __init__(self, inst, window=None, geometry='point', skill_mode='workers', cliques=(), worker_cuts=False):
        self.I, self.window, self.geometry, self.skill_mode = inst, window, geometry, skill_mode
        self.cliques = list(cliques)
        self.rows, self.rhs = [], []
        self.office = [self.row(('office', o), 1) for o in range(inst.m)]
        self.point = [self.row(('point', p), 1) for p in range(inst.n + inst.m)] if geometry == 'point' else []
        self.req = {(o, k): self.row(('skill', o, k), 0) for o in range(inst.m) for k in inst.skills} if skill_mode == 'workers' else {}
        self.worker = [self.row(('worker', w), 1) for w in range(inst.w)] if skill_mode == 'workers' else []
        self.link = {(o, w): self.row(('link', o, w), 0) for o in range(inst.m) for w in range(inst.w)} if skill_mode == 'workers' else {}
        self.team_count = [self.row(('team_count',o),0) for o in range(inst.m)] if worker_cuts and skill_mode == 'workers' else []
        self.count_skill = {k: self.row(('skill_count', k), len(inst.have[k])) for k in inst.skills} if skill_mode == 'counts' else {}
        self.balance = {}
        self.upper, self.lower = [], []
        if window is None:
            self.balance = {(o, p): self.row(('balance', o, p), inst.a + 2 * inst.cap[o])
                            for o in range(inst.m) for p in range(inst.m) if o != p}
            self.upper = [self.row(('upper', o), 0) for o in range(inst.m)]
            self.lower = [self.row(('lower', o), inst.maxload) for o in range(inst.m)]
            self.order = self.row(('order',), 0)
        self.clique_rows = [self.row(('clique', i), 1) for i in range(len(self.cliques))]

    def row(self, name, rhs):
        r = len(self.rows)
        self.rows.append(name)
        self.rhs.append(float(rhs))
        return r

    def accepts(self, c):
        if self.window is None:
            return True
        b, lo, hi = self.window
        return b <= len(c.sites) <= b + self.I.a and lo <= c.load <= hi

    def coeff(self, c):
        I, o, n, t = self.I, c.office, len(c.sites), c.load
        d = {self.office[o]: 1.0}
        for p in c.footprint:
            if self.point:
                d[self.point[p]] = 1.0
        for k in c.skills:
            if self.req:
                d[self.req[o, k]] = 1.0
            if self.count_skill:
                d[self.count_skill[k]] = 1.0
        for w in range(I.w):
            if self.link:
                d[self.link[o, w]] = -1.0
        if self.team_count and c.skills:
            # Any worker covers at most 'width' of these distinct required skills.
            width = max(len(set(c.skills).intersection(w)) for w in I.workers)
            d[self.team_count[o]] = float(math.ceil(len(c.skills)/width))
        for (a, b), r in self.balance.items():
            if o == a:
                d[r] = float(n + I.cap[a])
            elif o == b:
                d[r] = float(-n + I.cap[a])
        if self.upper:
            d[self.upper[o]], d[self.lower[o]] = float(t), float(I.maxload - t)
        for clique, r in zip(self.cliques, self.clique_rows):
            if c.key in clique:
                d[r] = 1.0
        return d

    def matrix(self, columns):
        I = self.I
        coeffs = [self.coeff(c) for c in columns]
        obj = [c.value for c in columns]
        names = [('column', c.key) for c in columns]
        if self.skill_mode == 'workers':
            for o in range(I.m):
                for w, skills in enumerate(I.workers):
                    d = {self.worker[w]: 1.0, self.link[o, w]: 1.0}
                    for k in set(skills):
                        d[self.req[o, k]] = -1.0
                    if self.team_count:
                        d[self.team_count[o]] = -1.0
                    coeffs.append(d)
                    obj.append(0.)
                    names.append(('worker', o, w))
        if self.window is None:
            coeffs.append({**{r: -1. for r in self.upper}, self.order: -1.})
            coeffs.append({**{r: 1. for r in self.lower}, self.order: 1.})
            obj += [-I.alpha, I.alpha]
            names += [('H',), ('L',)]
        rr, cc, vv = [], [], []
        for j, dd in enumerate(coeffs):
            for r, v in dd.items():
                if v:
                    rr.append(r); cc.append(j); vv.append(v)
        nr, rhs = len(self.rows), list(self.rhs)
        if self.geometry == 'pair':
            for i, c in enumerate(columns):
                fs = set(c.footprint)
                for j in range(i):
                    if c.office != columns[j].office and fs.intersection(columns[j].footprint):
                        rr += [nr, nr]; cc += [i, j]; vv += [1., 1.]
                        nr += 1; rhs.append(1.)
        mat = coo_matrix((vv, (rr, cc)), shape=(nr, len(obj))).tocsc()
        return mat, np.array(rhs), np.array(obj), names

    def solve(self, columns, integer=False, seconds=10., engine='highs', incumbent=None):
        start = time.perf_counter()
        I = self.I
        columns = [c for c in columns if self.accepts(c)]
        A, b, obj, names = self.matrix(columns)
        if engine == 'scip' and integer:
            from pyscipopt import Model, quicksum
            s = Model('zone master'); s.hideOutput()
            s.setRealParam('limits/time', max(.001, seconds))
            s.setIntParam('parallel/maxnthreads', 1)
            xs = [s.addVar(vtype='C' if n[0] in ('H', 'L') else 'B', lb=0.,
                           ub=None if n[0] in ('H', 'L') else 1., obj=float(v))
                  for n, v in zip(names, obj)]
            R = A.tocsr()
            for r in range(A.shape[0]):
                lo, hi = R.indptr[r:r+2]
                s.addCons(quicksum(float(R.data[k]) * xs[R.indices[k]] for k in range(lo, hi)) <= float(b[r]))
            if incumbent:
                z = s.createSol()
                byoffice = {r['officeId']: r for r in incumbent}
                loads = [sum(int(I.tasks[i]) for i in r['sites']) for r in incumbent]
                for j, name in enumerate(names):
                    v = 0.
                    if name[0] == 'column':
                        o, ss = name[1]
                        v = float(o in byoffice and tuple(sorted(byoffice[o]['sites'])) == ss)
                    elif name[0] == 'worker':
                        v = float(name[1] in byoffice and name[2] in byoffice[name[1]]['workers'])
                    elif name[0] == 'H':
                        v = max(loads, default=0)
                    elif name[0] == 'L':
                        v = min(loads, default=0)
                    s.setSolVal(z, xs[j], v)
                s.addSol(z)
            s.setMaximize(); s.optimize()
            sol = s.getBestSol()
            x = np.array([s.getSolVal(sol, v) for v in xs]) if sol is not None else np.zeros(len(xs))
            value = float(obj @ x)
            status = str(s.getStatus())
            bound = float(s.getDualbound())
            dual = None
            iterations = int(s.getNLPIterations())
        else:
            s = highspy.Highs()
            s.setOptionValue('output_flag', False)
            s.setOptionValue('threads', 1)
            s.setOptionValue('time_limit', max(.001, seconds))
            s.setOptionValue('mip_rel_gap', 1e-8)
            s.setOptionValue('primal_feasibility_tolerance', 1e-8)
            s.setOptionValue('dual_feasibility_tolerance', 1e-8)
            lp = highspy.HighsLp()
            lp.num_col_, lp.num_row_ = A.shape[1], A.shape[0]
            lp.col_cost_ = -obj
            lp.col_lower_ = np.zeros(len(obj))
            # Column and worker upper bounds are implied by rows: no hidden bound duals.
            lp.col_upper_ = np.full(len(obj), highspy.kHighsInf)
            lp.row_lower_, lp.row_upper_ = np.full(len(b), -highspy.kHighsInf), b
            lp.a_matrix_.format_ = highspy.MatrixFormat.kColwise
            lp.a_matrix_.start_, lp.a_matrix_.index_, lp.a_matrix_.value_ = A.indptr, A.indices, A.data
            if integer:
                lp.integrality_ = [highspy.HighsVarType.kContinuous if n[0] in ('H', 'L') else highspy.HighsVarType.kInteger for n in names]
            s.passModel(lp); s.run()
            sol, info = s.getSolution(), s.getInfo()
            x = np.array(sol.col_value)
            status = s.modelStatusToString(s.getModelStatus())
            value = float(obj @ x)
            bound = -float(info.mip_dual_bound) if integer else value
            dual = -np.array(sol.row_dual) if sol.dual_valid and not integer else None
            iterations = int(info.simplex_iteration_count)
        penalty = self.I.alpha * (self.window[2] - self.window[1]) if self.window else 0.
        dual_base = None
        if dual is not None:
            # Repair numerical dual sign/stationarity errors explicitly. All
            # nonpriced variables have valid bounds: workers <=1, H,L <=maxload
            # for at least one optimum (H can always be clipped downward).
            dual = np.maximum(dual, 0.)
            slack = obj - np.asarray(A.T @ dual).ravel()
            correction = sum(max(0.,float(slack[j])) * (I.maxload if names[j][0] in ('H','L') else 1.)
                             for j in range(len(columns),len(names)))
            dual_base = float(b @ dual) + correction - penalty
        value, bound = max(0., value - penalty), max(0., bound - penalty)
        solution = []
        if integer:
            for j, c in enumerate(columns):
                if x[j] > .5:
                    workers = [names[k][2] for k in range(len(names))
                               if names[k][0] == 'worker' and names[k][1] == c.office and x[k] > .5]
                    solution.append(dict(officeId=c.office, sites=list(c.sites), workers=workers))
            if penalty and not solution:
                value = 0.
        return dict(value=value, bound=bound, status=status, dual=dual, dual_base=dual_base, x=x,
                    columns=columns, solution=solution, seconds=time.perf_counter()-start,
                    rows=A.shape[0], variables=A.shape[1], nnz=A.nnz, iterations=iterations)

    def rc(self, c, dual):
        return c.value - sum(dual[r] * v for r, v in self.coeff(c).items())

    def pricing_parts(self, o, dual):
        """constant + sum weights*x - sum skill_prices*b - sum point_prices*h.

        This identity is exact when there are no arbitrary finite-pool clique cuts.
        Synthetic columns below extract the affine size/load terms of coeff().
        """
        if self.cliques or self.team_count:
            raise ValueError('Clique/team-cover penalties need an additional pricing term; only enumerated pricing supports these cuts')
        I = self.I
        c0 = Column(o, (), (), (), 0, -float(I.cost[o]))
        c1 = Column(o, (0,), (), (), 0, -float(I.cost[o]))
        ct = Column(o, (), (), (), 1, -float(I.cost[o]))
        d0, d1, dt = self.coeff(c0), self.coeff(c1), self.coeff(ct)
        price0 = sum(dual[r]*v for r, v in d0.items())
        nprice = sum(dual[r]*v for r, v in d1.items()) - price0
        tprice = sum(dual[r]*v for r, v in dt.items()) - price0
        skill = {k: float(dual[self.req[o,k]]) if self.req else float(dual[self.count_skill[k]])
                 if self.count_skill else 0. for k in I.skills}
        rho = dual[self.point] if self.point else np.zeros(I.n+I.m)
        return -float(I.cost[o])-price0, I.profit[o]-nprice-tprice*I.tasks, skill, rho

    def relaxed_pricing_bound(self, o, dual):
        """Certified cheap upper bound on ANY zone's reduced cost for office o.

        Replace footprint by {own office} U assigned sites, drop nonnegative skill
        and clique penalties, drop lower count/task-window constraints. Top-C
        positive marginal profits solves the remaining relaxation exactly.
        """
        I = self.I
        const = -I.cost[o] - dual[self.office[o]]
        if self.point:
            const -= dual[self.point[I.n + o]]
        if self.link:
            const += sum(dual[self.link[o, w]] for w in range(I.w))
        nprice, tprice = 0., 0.
        for (a, b), r in self.balance.items():
            if o == a:
                const -= I.cap[a] * dual[r]; nprice += dual[r]
            elif o == b:
                const -= I.cap[a] * dual[r]; nprice -= dual[r]
        if self.upper:
            const -= I.maxload * dual[self.lower[o]]
            tprice = dual[self.upper[o]] - dual[self.lower[o]]
        w = I.profit[o] - nprice - tprice * I.tasks
        if self.point:
            w = w - dual[self.point[:I.n]]
        w = np.array([v for v, ok in zip(w, I.servable) if ok and v > 0])
        if len(w) > I.cap[o]:
            w = np.partition(w, len(w)-I.cap[o])[len(w)-I.cap[o]:] if I.cap[o] else w[:0]
        return float(const + w.sum()) if I.cap[o] else -math.inf


def dedup(columns):
    return list({c.key: c for c in columns if c is not None}.values())


def cg_enumerated(master, universe, seconds=20., batch=1):
    """Exact pricing by full enumeration, ONLY a tiny-instance correctness oracle."""
    start = time.perf_counter()
    universe = [c for c in universe if master.accepts(c)]
    pool = [c for c in universe if len(c.sites) == 1]
    if not pool:
        pool = universe[:1]
    keys = {c.key for c in pool}
    trace = []
    result = None
    converged = False
    while time.perf_counter() - start < seconds:
        result = master.solve(pool, seconds=max(.001, seconds-(time.perf_counter()-start)))
        if result['dual'] is None or result['status'] != 'Optimal':
            break
        byoffice = [[] for _ in range(master.I.m)]
        for c in universe:
            byoffice[c.office].append((master.rc(c, result['dual']), c))
        correction = sum(max(0., max((v for v, _ in cs), default=0.)) for cs in byoffice)
        cheap = sum(max(0., master.relaxed_pricing_bound(o, result['dual'])) for o in range(master.I.m))
        trace.append(dict(round=len(trace), columns=len(pool), rmp=result['value'],
                          exact_certificate=max(0.,result['dual_base']+correction),
                          cheap_certificate=max(0.,result['dual_base']+cheap),
                          max_rc=max((v for cs in byoffice for v, _ in cs), default=0.)))
        if correction < 1e-7:
            converged = True
            break
        added = 0
        for cs in byoffice:
            for rc, c in sorted(cs, key=lambda p:p[0], reverse=True)[:batch]:
                if rc > 1e-8 and c.key not in keys:
                    keys.add(c.key); pool.append(c); added += 1
        if not added:
            break
    return dict(result=result, pool=pool, trace=trace, converged=converged,
                seconds=time.perf_counter()-start)


def reference_optimum(I, columns):
    """Independent exhaustive integer reference, including exact worker teams."""
    teams = {}
    for req in {c.skills for c in columns}:
        good = []
        for mask in range(1 << I.w):
            covered = {k for w in range(I.w) if mask >> w & 1 for k in I.workers[w]}
            if set(req) <= covered and not any((g & mask) == g for g in good):
                good.append(mask)
        teams[req] = good
    peroffice = [[c for c in columns if c.office == o] for o in range(I.m)]
    best, nodes = 0., 0

    def walk(o, occupied, usedworkers, ns, loads, value):
        nonlocal best, nodes
        nodes += 1
        if o == I.m:
            score = value - (I.alpha*(max(loads)-min(loads)) if loads else 0.)
            best = max(best, score)
            return
        walk(o+1, occupied, usedworkers, ns, loads, value)
        for c in peroffice[o]:
            fs = sum(1 << p for p in c.footprint)
            n = len(c.sites)
            if fs & occupied or (ns and max(max(ns), n)-min(min(ns), n) > I.a):
                continue
            for team in teams[c.skills]:
                if not team & usedworkers:
                    walk(o+1, occupied | fs, usedworkers | team, ns+[n], loads+[c.load], value+c.value)
    walk(0, 0, 0, [], [], 0.)
    return best, nodes
