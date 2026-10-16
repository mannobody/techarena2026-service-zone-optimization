#!/usr/bin/env python3
"""Лагранжева верхняя оценка.

alpha*(max L - min L) = max_{pi in Pi} sum_o pi_o * L_o,  где
Pi = { pi : sum_o pi_o = 0, sum_o max(pi_o,0) <= alpha }.

Отсюда для любого pi из Pi и фиксированного набора открытых офисов U

  OPT_U <= UB(pi) = max_x sum_{o,s} (p_os - pi_o * t_s) x_os - sum_{o in U} c_o,
  при  sum_o x_os <= 1,  sum_s x_os <= maxSize_o,  x >= 0.

Внутренняя задача — транспортная, её LP целочислен. Геометрия и навыки
отброшены, поэтому оценка верна, но завышена; зазор до неё показывает,
сколько стоит геометрия.
"""
import json, sys
import numpy as np
from scipy.optimize import linprog
from scipy.sparse import coo_matrix


def inner(P, cap, pi, t):
    """max sum (P[o,s] - pi_o t_s) x, sum_o x[:,s] <= 1, sum_s x[o,:] <= cap_o."""
    K, n = P.shape
    W = P - pi[:, None] * t[None, :]
    keep = W > 0
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


def bound(path, U, lb=0.0, iters=80, verbose=False):
    I = json.load(open(path))
    S, O, D = I['sites'], I['offices'], I['distances']
    alpha = I['balanceCoefficient']
    n, K = len(S), len(U)
    Nk = {}
    for w in I['workers']:
        for k in set(w):
            Nk[k] = Nk.get(k, 0) + 1
    ok = [all(Nk.get(k, 0) > 0 for k in S[s]['tasks']) for s in range(n)]
    idx = [s for s in range(n) if ok[s]]          # необслуживаемые сайты исключаем
    t = np.array([len(S[s]['tasks']) for s in idx], dtype=float)
    r = np.array([S[s]['reward'] for s in idx], dtype=float)
    P = np.array([[r[j] - D[o][idx[j]] for j in range(len(idx))] for o in U])
    n = len(idx)
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


if __name__ == '__main__':
    for i in sys.argv[1:]:
        inst, sol = f'task/instance{i}/instance.json', f'/tmp/sol_s2_v7_{i}.json'
        try:
            U = sorted(o['officeId'] for o in json.load(open(sol)))
        except Exception:
            U = list(range(len(json.load(open(inst))['offices'])))
        cur = None
        try:
            import subprocess
            cur = float(subprocess.run(['python3', 'task/validate_solution.py', inst, sol],
                                       capture_output=True, text=True).stdout.strip().split()[-1])
        except Exception:
            pass
        v0, b = bound(inst, U, lb=cur or 0.0)
        print(f"inst{i}: U={U}  наше={cur}  UB(pi=0)={v0:.2f}  min UB(pi)={b:.2f}"
              + (f"  доля={cur / b * 100:.1f}%" if cur else ""))
