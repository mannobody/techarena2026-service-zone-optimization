#!/usr/bin/env python3
"""Точная модель всей задачи (CP-SAT): навыки, A, α и геометрия — точно (оболочки могут пересекаться без общих точек).
Нужен ortools (не в .venv): python3 -m venv /tmp/ov && /tmp/ov/bin/pip install ortools numpy shapely
  /tmp/ov/bin/python tools/exact_cpsat.py inst.json --full --hint best.json --tl 600 --total 600 --out opt.json
--full — все лестницы сразу (≤ ~200 сайтов), без него — лениво по нарушениям (медленно на ≥ 300 сайтов);
--ops 0,2,3 — фиксировать набор офисов; --first-out — решение без геометрии (1-я итерация).

Покрытие точки q оболочкой зоны o (офис p_o + её сайты): углы вокруг q от направления на p_o.
q ∈ conv ⇔ есть сайт a с углом α∈(0,π] и сайт b с углом β∈[−π,0) зоны, α−β ≥ π (или a на угле π — отрезок p_o–a).
Для пары (q,o): верхние точки по убыванию α, лестница u_k = OR(x первых k); для каждой нижней b:
x_b ∧ u_{k(b)} → c[q,o]. AtMostOne_o c[q,o]. Пары (q,o) добавляются лениво по нарушениям.
"""
import json, sys, math, time, argparse
import numpy as np
from ortools.sat.python import cp_model


def load(path):
    I = json.load(open(path))
    return I


def orient(ax, ay, bx, by, cx, cy):
    return (bx - ax) * (cy - ay) - (by - ay) * (cx - ax)


def hull_cover(pts_xy, members, allpts):
    """Индексы точек allpts, покрытых выпуклой оболочкой members (shapely covers)."""
    from shapely import MultiPoint, Point
    import shapely
    h = MultiPoint([pts_xy[i] for i in members]).convex_hull
    shapely.prepare(h)
    P = shapely.points(allpts)
    return np.nonzero(shapely.covers(h, P))[0]


class Model:
    def __init__(self, I, prune=None):
        self.I = I
        S, O, W = I['sites'], I['offices'], I['workers']
        self.ns, self.no = ns, no = len(S), len(O)
        self.D = np.array(I['distances'])
        self.alpha = I['balanceCoefficient']
        self.A = I['maxDifference']
        self.xy = np.array([[s['x'], s['y']] for s in S] + [[o['x'], o['y']] for o in O])
        have = set(k for w in W for k in w)
        self.serv = [all(k in have for k in s['tasks']) for s in S]
        self.single = all(len(w) <= 1 for w in W)
        m = self.m = cp_model.CpModel()
        self.y = [m.NewBoolVar(f'y{o}') for o in range(no)]
        self.x = {}
        for s in range(ns):
            if not self.serv[s]:
                continue
            for o in range(no):
                if O[o]['maxSize'] <= 0:
                    continue
                if prune is not None and not prune(s, o):
                    continue
                self.x[s, o] = m.NewBoolVar(f'x{s}_{o}')
        self.xs = {s: [] for s in range(ns)}
        self.xo = {o: [] for o in range(no)}
        for (s, o), v in self.x.items():
            self.xs[s].append(v); self.xo[o].append((s, v))
        for s in range(ns):
            if self.xs[s]:
                m.AddAtMostOne(self.xs[s])
        skills = sorted(set(k for s in S for k in s['tasks']) | have)
        # навыки
        if self.single:
            N = {k: sum(1 for w in W if w and w[0] == k) for k in skills}
            z = {(o, k): m.NewBoolVar('') for o in range(no) for k in skills if N[k] > 0}
            for k in skills:
                if N[k] > 0:
                    m.Add(sum(z[o, k] for o in range(no)) <= N[k])
            self.z = z
        else:
            w = {(j, o): m.NewBoolVar('') for j in range(len(W)) for o in range(no)}
            for j in range(len(W)):
                m.AddAtMostOne([w[j, o] for o in range(no)])
            z = {}
            for o in range(no):
                for k in skills:
                    js = [j for j in range(len(W)) if k in W[j]]
                    if js:
                        z[o, k] = m.NewBoolVar('')
                        m.AddBoolOr([w[j, o] for j in js]).OnlyEnforceIf(z[o, k])
            self.z = z; self.w = w
        for (s, o), v in self.x.items():
            m.AddImplication(v, self.y[o])
            for k in set(S[s]['tasks']):
                m.AddImplication(v, z[o, k])
        # размеры и баланс
        nmax = max(o['maxSize'] for o in O)
        U = m.NewIntVar(0, nmax, 'U'); L = m.NewIntVar(0, nmax, 'L')
        tsum = sum(len(s['tasks']) for s in S)
        Tmax = m.NewIntVar(0, tsum, 'Tmax'); Tmin = m.NewIntVar(0, tsum, 'Tmin')
        self.n = []
        self.T = []
        for o in range(no):
            n_o = sum(v for _, v in self.xo[o])
            T_o = sum(len(S[s]['tasks']) * v for s, v in self.xo[o])
            m.Add(n_o <= O[o]['maxSize'] * self.y[o])
            m.Add(n_o <= U)
            m.Add(n_o >= L).OnlyEnforceIf(self.y[o])
            m.Add(T_o <= Tmax)
            m.Add(T_o >= Tmin).OnlyEnforceIf(self.y[o])
            self.n.append(n_o)
        m.Add(U - L <= self.A)
        m.Add(Tmin <= Tmax)
        self.Tmax, self.Tmin = Tmax, Tmin
        # цель (вещественная)
        obj = []
        for (s, o), v in self.x.items():
            obj.append((S[s]['reward'] - self.D[o][s], v))
        for o in range(no):
            obj.append((-O[o]['cost'], self.y[o]))
        self.objterms = obj
        e = sum(c * v for c, v in obj) - self.alpha * (Tmax - Tmin)
        m.Maximize(e)
        # геометрия
        self.c = {}      # (q,o) -> bool
        self.amo = {}    # q -> set(o) уже в AtMostOne-групп
        self.staircase = set()
        self.ncuts = 0

    def cvar(self, q, o):
        if (q, o) not in self.c:
            v = self.m.NewBoolVar(f'c{q}_{o}')
            self.c[q, o] = v
            if q < self.ns and (q, o) in self.x:
                self.m.AddImplication(self.x[q, o], v)
            if q == self.ns + o:
                self.m.AddImplication(self.y[o], v)
        return self.c[q, o]

    def add_staircase(self, q, o):
        """Точное условие q ∈ conv({p_o} ∪ S_o) → c[q,o]."""
        if (q, o) in self.staircase:
            return
        self.staircase.add((q, o))
        m = self.m
        c = self.cvar(q, o)
        qx, qy = self.xy[q]
        px, py = self.xy[self.ns + o]
        if q == self.ns + o or (qx == px and qy == py):
            m.AddImplication(self.y[o], c)
            return
        th = math.atan2(py - qy, px - qx)
        up, lo = [], []
        for s, v in self.xo[o]:
            sx, sy = self.xy[s]
            if s == q or (sx == qx and sy == qy):
                m.AddImplication(v, c)    # совпадает с q
                continue
            cr = orient(qx, qy, px, py, sx, sy)   # >0: слева от q→p
            dot = (px - qx) * (sx - qx) + (py - qy) * (sy - qy)
            if cr == 0:
                if dot < 0:              # на продолжении за q: отрезок p_o–s содержит q
                    m.AddImplication(v, c)
                continue                 # на луче к офису — не помогает
            a = math.atan2(sy - qy, sx - qx) - th
            while a <= -math.pi: a += 2 * math.pi
            while a > math.pi: a -= 2 * math.pi
            (up if cr > 0 else lo).append((a, s, v))
        if not up or not lo:
            self.ncuts += 1
            return
        up.sort(key=lambda t: -t[0])         # по убыванию α
        # лестница: u[k] = OR(up[0..k])
        u = []
        for k, (a, s, v) in enumerate(up):
            uk = m.NewBoolVar('')
            m.AddImplication(v, uk)
            if k:
                m.AddImplication(u[-1], uk)
            u.append(uk)
        alphas = [t[0] for t in up]
        for b, sb, vb in lo:
            # нужен a с α ≥ π + β (с допуском — проверяем ориентацией точно)
            need = math.pi + b
            # последний k с alphas[k] >= need  (alphas убывают)
            lo_k, hi_k = 0, len(alphas) - 1
            kk = -1
            while lo_k <= hi_k:
                mid = (lo_k + hi_k) // 2
                if alphas[mid] >= need - 1e-12:
                    kk = mid; lo_k = mid + 1
                else:
                    hi_k = mid - 1
            if kk >= 0:
                m.AddBoolOr([u[kk].Not(), vb.Not(), c])
        self.ncuts += 1

    def add_point(self, q, zones):
        for o in zones:
            self.add_staircase(q, o)
        qs = self.amo.setdefault(q, set())
        new = set(zones) - qs
        if new:
            qs |= set(zones)
            self.m.AddAtMostOne([self.cvar(q, o) for o in sorted(qs)])

    def extract(self, solver):
        asg = [-1] * self.ns
        for (s, o), v in self.x.items():
            if solver.Value(v):
                asg[s] = o
        opn = [solver.Value(self.y[o]) for o in range(self.no)]
        return asg, opn

    def violations(self, asg, opn):
        zones = {o: [self.ns + o] for o in range(self.no) if opn[o]}
        for s, o in enumerate(asg):
            if o >= 0:
                zones[o].append(s)
        cov = {}
        allp = self.xy
        for o, mem in zones.items():
            for q in hull_cover(allp, mem, allp):
                cov.setdefault(int(q), []).append(o)
        return {q: os for q, os in cov.items() if len(os) > 1}


def workers_for(I, asg, opn):
    """Раздать рабочих: офису нужны навыки его сайтов (паросочетание, жадно + перебор)."""
    S, W = I['sites'], I['workers']
    need = {o: set() for o in range(len(opn)) if opn[o]}
    for s, o in enumerate(asg):
        if o >= 0:
            need[o] |= set(S[s]['tasks'])
    # двудольное покрытие (офис,навык) рабочими: max-flow простым DFS
    req = [(o, k) for o in need for k in sorted(need[o])]
    # каждому (o,k) нужен свой рабочий? нет: рабочий с несколькими навыками закрывает несколько (o,·)
    # Точно: рабочий → офис; покрыть все (o,k). Для однонавыковых — паросочетание.
    used = {}
    res = {o: [] for o in need}
    if all(len(w) <= 1 for w in W):
        pool = {}
        for j, w in enumerate(W):
            if w:
                pool.setdefault(w[0], []).append(j)
        for o, k in req:
            if not pool.get(k):
                return None
            res[o].append(pool[k].pop())
        return res
    # многопрофильные: CP-SAT
    m = cp_model.CpModel()
    wv = {(j, o): m.NewBoolVar('') for j in range(len(W)) for o in need}
    for j in range(len(W)):
        m.AddAtMostOne([wv[j, o] for o in need])
    for o, k in req:
        m.AddBoolOr([wv[j, o] for j in range(len(W)) if k in W[j]] or [m.NewConstant(0)])
    sv = cp_model.CpSolver(); sv.parameters.max_time_in_seconds = 10
    if sv.Solve(m) not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return None
    for (j, o), v in wv.items():
        if sv.Value(v):
            res[o].append(j)
    return res


def objective(I, asg, opn):
    S, O, D = I['sites'], I['offices'], I['distances']
    tot = 0.0
    T = {o: 0 for o in range(len(opn)) if opn[o]}
    for s, o in enumerate(asg):
        if o >= 0:
            tot += S[s]['reward'] - D[o][s]
            T[o] += len(S[s]['tasks'])
    tot -= sum(O[o]['cost'] for o in T)
    if T:
        tot -= I['balanceCoefficient'] * (max(T.values()) - min(T.values()))
    return tot


def hint_asg(sol, ns, no):
    asg = [-1] * ns; opn = [0] * no
    for e in sol:
        opn[e['officeId']] = 1
        for s in e['sites']:
            asg[s] = e['officeId']
    return asg, opn


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('inst')
    ap.add_argument('--tl', type=float, default=60, help='секунд на одно решение')
    ap.add_argument('--total', type=float, default=1800)
    ap.add_argument('--workers', type=int, default=16)
    ap.add_argument('--out')
    ap.add_argument('--hint', help='решение json для подсказки')
    ap.add_argument('--log', action='store_true')
    ap.add_argument('--first-out', help='сохранить решение 1-й итерации (без ленивой геометрии)')
    ap.add_argument('--ops', help='зафиксировать набор открытых офисов: 0,2,3')
    ap.add_argument('--near', type=float, default=0, help='лестницы заранее для q ближе F·(радиус зоны подсказки) к офису')
    ap.add_argument('--full', action='store_true', help='все лестницы (q,o) сразу — полная точная модель')
    a = ap.parse_args()
    I = load(a.inst)
    t0 = time.time()
    M = Model(I)
    if a.ops is not None:
        ops = set(int(v) for v in a.ops.split(',') if v != '')
        for o in range(M.no):
            M.m.Add(M.y[o] == (1 if o in ops else 0))
    if a.full:
        for q in range(M.ns + M.no):
            M.add_point(q, [o for o in range(M.no) if M.xo[o]])
    if a.near > 0 and a.hint:
        sol = json.load(open(a.hint))
        rad = {}
        for e in sol:
            o = e['officeId']; px, py = M.xy[M.ns + o]
            rad[o] = max([math.hypot(M.xy[s][0] - px, M.xy[s][1] - py) for s in e['sites']] + [0.0])
        for q in range(M.ns + M.no):
            zs = [o for o in rad if math.hypot(M.xy[q][0] - M.xy[M.ns + o][0], M.xy[q][1] - M.xy[M.ns + o][1]) <= a.near * rad[o]]
            if len(zs) >= 1:
                M.add_point(q, zs)
    print(f'ns={M.ns} no={M.no} x={len(M.x)} single={M.single} stairs={len(M.staircase)} t={time.time()-t0:.1f}', flush=True)
    sv = cp_model.CpSolver()
    sv.parameters.num_workers = a.workers
    sv.parameters.max_time_in_seconds = a.tl
    if a.log:
        sv.parameters.log_search_progress = True
    if a.hint:
        sol = json.load(open(a.hint))
        print('hint obj', objective(I, *hint_asg(sol, M.ns, M.no)), flush=True)
        for e in sol:
            o = e['officeId']
            M.m.AddHint(M.y[o], 1)
            for s in e['sites']:
                if (s, o) in M.x:
                    M.m.AddHint(M.x[s, o], 1)
    best = None
    it = 0
    while time.time() - t0 < a.total:
        it += 1
        sv.parameters.max_time_in_seconds = min(a.tl, a.total - (time.time() - t0))
        st = sv.Solve(M.m)
        if st not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            print('status', sv.StatusName(st)); break
        asg, opn = M.extract(sv)
        bnd = sv.BestObjectiveBound()
        val = objective(I, asg, opn)
        viol = M.violations(asg, opn)
        print(f'it{it} t={time.time()-t0:.0f}s {sv.StatusName(st)} obj={val:.6g} bound={bnd:.6g} viol={len(viol)} stairs={len(M.staircase)}', flush=True)
        if it == 1 and a.first_out:
            wk = workers_for(I, asg, opn) or {}
            json.dump([{'officeId': o, 'sites': [x for x in range(M.ns) if asg[x] == o], 'workers': wk.get(o, [])}
                       for o in range(M.no) if opn[o]], open(a.first_out, 'w'))
            if a.total <= 0: break
        if not viol:
            if best is None or val > best[0]:
                best = (val, asg, opn)
            if st == cp_model.OPTIMAL:
                print(f'OPTIMAL {val:.10g}')
                break
            # не доказано: продолжить с подсказкой
        for q, os in viol.items():
            M.add_point(q, os)
        # подсказка — текущее решение
        M.m.ClearHints()
        for (s, o), v in M.x.items():
            M.m.AddHint(v, 1 if asg[s] == o else 0)
        for o in range(M.no):
            M.m.AddHint(M.y[o], opn[o])
    if best and a.out:
        val, asg, opn = best
        wk = workers_for(I, asg, opn)
        out = []
        for o in range(M.no):
            if opn[o]:
                out.append({'officeId': o, 'sites': [s for s in range(M.ns) if asg[s] == o], 'workers': wk[o] if wk else []})
        json.dump(out, open(a.out, 'w'))
    if best:
        print(f'BEST {best[0]:.10g}')


if __name__ == '__main__':
    main()
