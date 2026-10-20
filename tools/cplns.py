#!/usr/bin/env python3
"""CP-SAT-LNS из готового решения: свободны k соседних офисов (открытых и закрытых), остальные зоны фиксированы;
подзадача решается точно (геометрия — «лестницы» из exact_cpsat.py, рабочие, A и α — вместе с фиксированными).
Искатель многозонных улучшений: где наш LNS (ходы по 2 зонам) застрял. Только однонавыковые рабочие.

  python3 -m venv /tmp/ov && /tmp/ov/bin/pip install ortools numpy shapely   # ortools нет в .venv
  /tmp/ov/bin/python tools/cplns.py task/instance3/instance.json sol.json --k 3 --tl 30 --total 600 --out better.json
"""
import json, sys, time, argparse, random, math
import numpy as np
import shapely
from shapely import MultiPoint
from ortools.sat.python import cp_model

sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parent))
from exact_cpsat import objective, workers_for, hint_asg, orient


def solve_sub(I, xy, D, asg, opn, F, tl, workers, seed):
    S, O, W = I['sites'], I['offices'], I['workers']
    ns, no = len(S), len(O)
    alpha, A = I['balanceCoefficient'], I['maxDifference']
    t = [len(s['tasks']) for s in S]
    fixed = [o for o in range(no) if opn[o] and o not in F]
    allpts = shapely.points(xy)
    blocked = np.zeros(ns + no, bool)          # покрыты фиксированной зоной
    for o in fixed:
        mem = [s for s in range(ns) if asg[s] == o] + [ns + o]
        h = MultiPoint([tuple(xy[i]) for i in mem]).convex_hull
        shapely.prepare(h)
        blocked |= shapely.covers(h, allpts)
    have = set(k for w in W for k in w)
    # кандидаты: сайты свободных зон + свободные сайты, не заблокированные
    cand = [s for s in range(ns) if not blocked[s] and (asg[s] < 0 or asg[s] in F)
            and all(k in have for k in S[s]['tasks'])]
    Fl = [o for o in sorted(F) if O[o]['maxSize'] > 0 and not blocked[ns + o]]
    if not Fl:
        return None
    m = cp_model.CpModel()
    y = {o: m.NewBoolVar('') for o in Fl}
    x = {(s, o): m.NewBoolVar('') for s in cand for o in Fl}
    for s in cand:
        m.AddAtMostOne([x[s, o] for o in Fl])
    # рабочие: однонавыковые — остаток после фиксированных зон
    single = all(len(w) <= 1 for w in W)
    skills = sorted(set(k for s in S for k in s['tasks']) | have)
    if single:
        used = {k: 0 for k in skills}
        for o in fixed:
            need = set(k for s in range(ns) if asg[s] == o for k in S[s]['tasks'])
            for k in need: used[k] += 1
        N = {k: sum(1 for w in W if w and w[0] == k) - used[k] for k in skills}
        z = {(o, k): m.NewBoolVar('') for o in Fl for k in skills}
        for k in skills:
            m.Add(sum(z[o, k] for o in Fl) <= max(0, N[k]))
    else:
        return None   # многопрофильные — не поддержано в диагностике
    for (s, o), v in x.items():
        m.AddImplication(v, y[o])
        for k in set(S[s]['tasks']):
            m.AddImplication(v, z[o, k])
    # размеры и баланс вместе с фиксированными
    fsz = [sum(1 for s in range(ns) if asg[s] == o) for o in fixed]
    fT = [sum(t[s] for s in range(ns) if asg[s] == o) for o in fixed]
    big = len(cand) + max(fsz + [0]) + 1
    U = m.NewIntVar(0, big, ''); L = m.NewIntVar(0, big, '')
    TT = sum(t) + 1
    Tmax = m.NewIntVar(0, TT, ''); Tmin = m.NewIntVar(0, TT, '')
    for v in fsz:
        m.Add(U >= v); m.Add(L <= v)
    for v in fT:
        m.Add(Tmax >= v); m.Add(Tmin <= v)
    for o in Fl:
        n_o = sum(x[s, o] for s in cand)
        T_o = sum(t[s] * x[s, o] for s in cand)
        m.Add(n_o <= O[o]['maxSize'] * y[o])
        m.Add(n_o >= 1).OnlyEnforceIf(y[o])
        m.Add(n_o <= U)
        m.Add(n_o >= L).OnlyEnforceIf(y[o])
        m.Add(T_o <= Tmax)
        m.Add(T_o >= Tmin).OnlyEnforceIf(y[o])
    m.Add(U - L <= A)
    m.Add(Tmin <= Tmax)
    obj = sum((S[s]['reward'] - D[o][s]) * x[s, o] for (s, o) in x) - sum(O[o]['cost'] * y[o] for o in Fl) \
        - alpha * (Tmax - Tmin)
    m.Maximize(obj)
    # геометрия: точки в области кандидатов
    region = MultiPoint([tuple(xy[s]) for s in cand] + [tuple(xy[ns + o]) for o in Fl]).convex_hull
    shapely.prepare(region)
    inreg = shapely.covers(region, allpts)
    c = {}
    for q in range(ns + no):
        if not inreg[q]:
            continue
        qx, qy = xy[q]
        cq = []
        for o in Fl:
            cv = m.NewBoolVar('')
            px, py = xy[ns + o]
            if q == ns + o or (qx == px and qy == py):
                m.AddImplication(y[o], cv)
            else:
                th = math.atan2(py - qy, px - qx)
                up, lo = [], []
                for s in cand:
                    v = x[s, o]
                    sx, sy = xy[s]
                    if s == q or (sx == qx and sy == qy):
                        m.AddImplication(v, cv); continue
                    cr = orient(qx, qy, px, py, sx, sy)
                    if cr == 0:
                        if (px - qx) * (sx - qx) + (py - qy) * (sy - qy) < 0:
                            m.AddImplication(v, cv)
                        continue
                    a = math.atan2(sy - qy, sx - qx) - th
                    while a <= -math.pi: a += 2 * math.pi
                    while a > math.pi: a -= 2 * math.pi
                    (up if cr > 0 else lo).append((a, v))
                if up and lo:
                    up.sort(key=lambda e: -e[0])
                    u = []
                    for kk, (a, v) in enumerate(up):
                        uk = m.NewBoolVar('')
                        m.AddImplication(v, uk)
                        if kk: m.AddImplication(u[-1], uk)
                        u.append(uk)
                    al = [e[0] for e in up]
                    for b, vb in lo:
                        need = math.pi + b
                        lo_k, hi_k, kk = 0, len(al) - 1, -1
                        while lo_k <= hi_k:
                            mid = (lo_k + hi_k) // 2
                            if al[mid] >= need - 1e-12: kk = mid; lo_k = mid + 1
                            else: hi_k = mid - 1
                        if kk >= 0:
                            m.AddBoolOr([u[kk].Not(), vb.Not(), cv])
            cq.append(cv)
        if blocked[q] or (q < ns and asg[q] >= 0 and asg[q] not in F) or (q >= ns and opn[q - ns] and (q - ns) not in F):
            for cv in cq: m.Add(cv == 0)        # точка уже под фиксированной зоной
        elif len(cq) > 1:
            m.AddAtMostOne(cq)
    for (s, o), v in x.items():
        m.AddHint(v, 1 if asg[s] == o else 0)
    for o in Fl:
        m.AddHint(y[o], opn[o])
    sv = cp_model.CpSolver()
    sv.parameters.num_workers = workers
    sv.parameters.max_time_in_seconds = tl
    sv.parameters.random_seed = seed
    st = sv.Solve(m)
    if st not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return None
    na = list(asg)
    for s in range(ns):
        if asg[s] in F: na[s] = -1
    for (s, o), v in x.items():
        if sv.Value(v): na[s] = o
    nopn = list(opn)
    for o in F: nopn[o] = 0
    for o in Fl: nopn[o] = sv.Value(y[o])
    return na, nopn, sv.StatusName(st)


def valid_geom(xy, ns, no, asg, opn):
    allpts = shapely.points(xy)
    cnt = np.zeros(ns + no, int)
    for o in range(no):
        if not opn[o]: continue
        mem = [s for s in range(ns) if asg[s] == o] + [ns + o]
        h = MultiPoint([tuple(xy[i]) for i in mem]).convex_hull
        shapely.prepare(h)
        cnt += shapely.covers(h, allpts)
    return int((cnt > 1).sum())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('inst'); ap.add_argument('start')
    ap.add_argument('--k', type=int, default=3)
    ap.add_argument('--tl', type=float, default=20)
    ap.add_argument('--total', type=float, default=600)
    ap.add_argument('--workers', type=int, default=8)
    ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--out')
    a = ap.parse_args()
    rnd = random.Random(a.seed)
    I = json.load(open(a.inst))
    S, O = I['sites'], I['offices']
    ns, no = len(S), len(O)
    xy = np.array([[s['x'], s['y']] for s in S] + [[o['x'], o['y']] for o in O])
    D = I['distances']
    asg, opn = hint_asg(json.load(open(a.start)), ns, no)
    cur = objective(I, asg, opn)
    t0 = time.time()
    print(f'start {cur:.6f}', flush=True)
    oxy = xy[ns:]
    it = 0
    tried = set()
    skips = 0
    while time.time() - t0 < a.total and skips < 20000:
        it += 1
        cidx = rnd.randrange(no)
        d = sorted(range(no), key=lambda o: math.hypot(*(oxy[o] - oxy[cidx])))
        k = min(no, a.k)
        # случайная выборка из 2k ближайших, чтобы не повторяться
        pool = d[:min(no, 2 * k)]
        F = frozenset([cidx] + rnd.sample([o for o in pool if o != cidx], k - 1))
        if (F, round(cur, 6)) in tried:
            skips += 1
            continue
        skips = 0
        tried.add((F, round(cur, 6)))
        r = solve_sub(I, xy, D, asg, opn, set(F), min(a.tl, a.total - (time.time() - t0)), a.workers, a.seed + it)
        if r is None:
            continue
        na, nopn, st = r
        val = objective(I, na, nopn)
        if val > cur + 1e-9 * max(1, abs(cur)):
            nv = valid_geom(xy, ns, no, na, nopn)
            if nv:
                print(f'  it{it} invalid geometry ({nv})', flush=True)
                continue
            cur, asg, opn = val, na, nopn
            print(f'it{it} t={time.time()-t0:.0f}s F={sorted(F)} {st} -> {cur:.6f} ops={[o for o in range(no) if opn[o]]}', flush=True)
            if a.out:
                wk = workers_for(I, asg, opn) or {}
                json.dump([{'officeId': o, 'sites': [s for s in range(ns) if asg[s] == o], 'workers': wk.get(o, [])}
                           for o in range(no) if opn[o]], open(a.out, 'w'))
    print(f'END {cur:.10g} iters={it}')


if __name__ == '__main__':
    main()
