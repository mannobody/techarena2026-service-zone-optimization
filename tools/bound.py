#!/usr/bin/env python3
"""Верхние оценки без геометрии.

1. mip_bound (CLI): MIP всей задачи, кроме оболочек, — HiGHS через scipy.optimize.milp.
   Офисы, рабочие (по типам навыков, целые), сайты — переменные; ёмкость, maxDifference,
   навыки и α·(max − min задач) — точно. Двойственная граница MIP — верная оценка сверху
   для любого числа офисов; если MIP решён до конца, это оптимум задачи без геометрии.
   Зазор «наше / оценка» = цена геометрии + недоработка решателя.

2. bound(path, U): лагранжева оценка для фиксированного набора офисов U (без навыков и A):
   alpha*(max L - min L) = max_{pi in Pi} sum_o pi_o * L_o,
   Pi = { pi : sum_o pi_o = 0, sum_o max(pi_o,0) <= alpha };
   UB(pi) = max_x sum_{o,s} (p_os - pi_o * t_s) x_os - sum_{o in U} c_o,
   sum_o x_os <= 1, sum_s x_os <= maxSize_o — транспортная задача, LP целочислен.

  python3 tools/bound.py inst2 thin5 small0 [--tl 120]   # наше (results/best.csv, suite_best.csv) против оценки
  python3 tools/bound.py path/to/instance.json            # только оценка
"""
import argparse, csv, json
from pathlib import Path
import numpy as np
from scipy.optimize import Bounds, LinearConstraint, linprog, milp
from scipy.sparse import coo_matrix

ROOT = Path(__file__).resolve().parent.parent


def inner(P, cap, pi, t):
    """max sum (P[o,s] - pi_o t_s) x, sum_o x[:,s] <= 1, sum_s x[o,:] <= cap_o."""
    K, n = P.shape
    W = P - pi[:, None] * t[None, :]
    c = -W.ravel()
    rows, cols, vals = [], [], []
    for s in range(n):
        for o in range(K):
            rows.append(s); cols.append(o * n + s); vals.append(1.0)
    for o in range(K):
        for s in range(n):
            rows.append(n + o); cols.append(o * n + s); vals.append(1.0)
    A = coo_matrix((vals, (rows, cols)), shape=(n + K, K * n))
    b = np.concatenate([np.ones(n), np.asarray(cap, dtype=float)])
    r = linprog(c, A_ub=A, b_ub=b, bounds=(0, 1), method='highs')
    x = r.x.reshape(K, n)
    val = float((W * x).sum())
    load = (x * t[None, :]).sum(axis=1)
    return val, load, x


def serviceable(I):
    """Сайты, все задачи которых есть хоть у одного рабочего."""
    have = set(k for w in I['workers'] for k in w)
    return [s for s, S in enumerate(I['sites']) if set(S['tasks']) <= have]


def bound(path, U, lb=0.0, iters=80, verbose=False):
    I = json.load(open(path))
    S, O, D = I['sites'], I['offices'], I['distances']
    alpha = I['balanceCoefficient']
    K = len(U)
    idx = serviceable(I)
    t = np.array([len(S[s]['tasks']) for s in idx], dtype=float)
    P = np.array([[S[s]['reward'] - D[o][s] for s in idx] for o in U])
    cap = [O[o]['maxSize'] for o in U]
    C = sum(O[o]['cost'] for o in U)
    pi = np.zeros(K)
    best = float('inf')
    v0 = None
    theta = 1.6
    for it in range(iters):
        val, load, _ = inner(P, cap, pi, t)
        ub = val - C
        if v0 is None:
            v0 = ub
        best = min(best, ub)
        if alpha <= 0 or K < 2:
            break
        g = load - load.mean()                      # субградиент UB по pi (со знаком минус)
        nrm2 = float(g @ g)
        if nrm2 < 1e-18:
            break
        # шаг Полякa: целимся в известное снизу значение lb
        step = theta * max(1e-12, ub - lb) / nrm2
        pi = pi + step * g
        pi -= pi.mean()                             # проекция: sum pi = 0
        pos = pi[pi > 0].sum()
        if pos > alpha:
            pi *= alpha / pos                       # проекция: sum pi+ <= alpha
        if verbose and it % 10 == 0:
            print(f"    it{it}: ub={ub:.2f} spread={load.max() - load.min():.1f}")
        if it > 10 and it % 15 == 0:
            theta *= 0.7
    return v0, best


def mip_bound(path, tl=60.0, out=None):
    """MIP без геометрии. Возвращает (оценка сверху, лучшее найденное без геометрии, решён ли до конца).
    out — записать найденное решение (без проверки оболочек) в формате solution.json."""
    I = json.load(open(path))
    S, O, D = I['sites'], I['offices'], I['distances']
    alpha, A = float(I['balanceCoefficient']), I['maxDifference']
    idx = serviceable(I)
    n, K = len(idx), len(O)
    types = {}                                       # тип рабочего (набор навыков) -> число рабочих
    for w in I['workers']:
        m = frozenset(w)
        types[m] = types.get(m, 0) + 1
    G = list(types)
    need = sorted({k for s in idx for k in S[s]['tasks']})
    t = [len(S[s]['tasks']) for s in idx]
    cap = [min(O[o]['maxSize'], n) for o in range(K)]
    M = max(cap + [1])
    T = float(sum(t)) + 1.0
    # переменные: x[o,s] | open[o] | y[g,o] | Lmax, Lmin, m
    X, OP, Y = 0, K * n, K * n + K
    LX, LN, MM = Y + len(G) * K, Y + len(G) * K + 1, Y + len(G) * K + 2
    nv = MM + 1
    xi = lambda o, j: X + o * n + j
    c = np.zeros(nv)
    for o in range(K):
        for j, s in enumerate(idx):
            c[xi(o, j)] = -(S[s]['reward'] - D[o][s])
        c[OP + o] = O[o]['cost']
    c[LX], c[LN] = alpha, -alpha
    rows, cols, vals, lo, hi = [], [], [], [], []
    r = 0

    def row(coef, l, h):
        nonlocal r
        for col, v in coef:
            rows.append(r); cols.append(col); vals.append(v)
        lo.append(l); hi.append(h)
        r += 1

    inf = np.inf
    for j in range(n):                                               # сайт — не больше одного офиса
        row([(xi(o, j), 1.0) for o in range(K)], -inf, 1.0)
    for o in range(K):
        sz = [(xi(o, j), 1.0) for j in range(n)]
        row(sz + [(OP + o, -cap[o])], -inf, 0.0)                     # ёмкость, только открытый
        row(sz + [(OP + o, -1.0)], 0.0, inf)                         # открытый не пуст
        row(sz + [(MM, -1.0), (OP + o, M)], -inf, A + M)             # size_o <= m + A
        row(sz + [(MM, -1.0), (OP + o, -M)], -M, inf)                # size_o >= m
        tk = [(xi(o, j), float(t[j])) for j in range(n)]
        row(tk + [(LX, -1.0)], -inf, 0.0)                            # Lmax >= L_o
        row(tk + [(LN, -1.0), (OP + o, -T)], -T, inf)                # Lmin <= L_o для открытых
        for j in range(n):
            row([(xi(o, j), 1.0), (OP + o, -1.0)], -inf, 0.0)        # x <= open (усиление LP)
        for k in need:                                               # навык k в офисе o
            wk = [(Y + g * K + o, -1.0) for g, m in enumerate(G) if k in m]
            for j, s in enumerate(idx):
                if k in S[s]['tasks']:
                    row([(xi(o, j), 1.0)] + wk, -inf, 0.0)
    for g, m in enumerate(G):                                        # рабочих типа g не больше, чем есть
        row([(Y + g * K + o, 1.0) for o in range(K)], -inf, types[m])
    row([(LN, 1.0), (LX, -1.0)], -inf, 0.0)
    Acon = coo_matrix((vals, (rows, cols)), shape=(r, nv)).tocsr()
    lb, ub = np.zeros(nv), np.ones(nv)
    for g, m in enumerate(G):
        ub[Y + g * K: Y + (g + 1) * K] = types[m]
    ub[LX] = ub[LN] = T
    ub[MM] = M
    integ = np.ones(nv)
    integ[LX] = integ[LN] = integ[MM] = 0
    res = milp(c, constraints=LinearConstraint(Acon, lo, hi), integrality=integ, bounds=Bounds(lb, ub),
               options={'time_limit': tl, 'mip_rel_gap': 1e-6, 'disp': False})
    db = getattr(res, 'mip_dual_bound', None)
    up = -db if db is not None and np.isfinite(db) else inf
    found = -res.fun if res.x is not None else None
    if res.status == 0 and found is not None:
        up = found
    if out and res.x is not None:
        x = np.round(res.x).astype(int)
        free = {m: [w for w, ws in enumerate(I['workers']) if frozenset(ws) == m] for m in G}
        sol = []
        for o in range(K):
            if x[OP + o]:
                ws = [free[m].pop() for g, m in enumerate(G) for _ in range(x[Y + g * K + o])]
                sol.append({'officeId': o, 'sites': [s for j, s in enumerate(idx) if x[xi(o, j)]], 'workers': ws})
        json.dump(sol, open(out, 'w'))
    return up, found, res.status == 0


def known_best():
    best = {}
    f = ROOT / 'results/best.csv'
    if f.exists():
        best.update({f'inst{r["instance"]}': float(r['objective']) for r in csv.DictReader(f.open())})
    f = ROOT / 'results/local/suite_best.csv'
    if f.exists():
        best.update({r['instance']: float(r['objective']) for r in csv.DictReader(f.open())})
    return best


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('inst', nargs='+')
    ap.add_argument('--tl', type=float, default=60.0, help='лимит MIP на инстанс, с')
    ap.add_argument('--out', help='каталог: записать решение MIP <имя>.json (оболочки не проверены)')
    a = ap.parse_args()
    best = known_best()
    for x in a.inst:
        if x.endswith('.json'):
            name, path = Path(x).stem, x
        elif x.startswith('inst'):
            name, path = x, ROOT / f'task/instance{x[4:]}/instance.json'
        else:
            name, path = x, ROOT / f'results/local/suite/suite_{x}.json'
        cur = best.get(name)
        up, found, exact = mip_bound(path, a.tl, a.out and f'{a.out}/{name}.json')
        f = f'{found:.6g}' if found is not None else '—'
        print(f'{name}: оценка={up:.6g} {"(точно)" if exact else "(граница)"} без_геом={f}'
              + (f'  наше={cur:.6g}  доля={cur / up * 100:.1f}%' if cur else ''), flush=True)
