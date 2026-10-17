"""
MIP статьи (формулы 1–9) через OR-Tools SCIP — эталон для малых инстансов.
Запуск: python3 secp_mip.py seed n_sites n_offices p seconds [D] [convex=0/1]
Аргументы те же, что у secp.py (инстанс генерируется тем же кодом).
"""
import sys
import time

import numpy as np
from ortools.linear_solver import pywraplp

import secp as S_

BIGK = float(sys.argv[8]) if len(sys.argv) > 8 else 2.0  # в статье 3M: тогда (9) не работает
CONVEX = len(sys.argv) > 7 and sys.argv[7] == "1"
N, M, D, v, RMAX = S_.N, S_.M, S_.D, S_.v, S_.RMAX

s = pywraplp.Solver.CreateSolver("SCIP")
s.SetTimeLimit(int(S_.SECONDS * 1000))
x = [[s.BoolVar("") for i in range(M)] for j in range(N)]
z = [s.BoolVar("") for i in range(M)]
y = [s.IntVar(0, int(RMAX[i]), "") for i in range(M)]
u = [s.NumVar(0, s.infinity(), "") for w in range(S_.NW)]
for j in range(N):
    s.Add(sum(x[j]) == 1)                                   # (2)
    for i in range(M):
        s.Add(x[j][i] <= y[i])                              # (3)
for i in range(M):
    s.Add(y[i] <= int(RMAX[i]) * z[i])                       # (4)
    s.Add(y[i] >= z[i])                                     # открыт => есть инженер
s.Add(sum(y) == S_.P)                                       # (5)
for i in range(M):
    for w in range(S_.NW):
        load = sum(float(v[j, w]) * x[j][i] for j in range(N))
        s.Add(load + u[w] >= float(S_.VLB[w]) * y[i])       # (6)
        s.Add(load - u[w] <= float(S_.VUB[w]) * y[i])       # (7)
for j in range(N):                                          # (8) предпочтения
    Ij = np.flatnonzero(S_.PREF[j])
    for i in Ij:
        s.Add(sum(x[j][l] for l in Ij) >= z[i])
if CONVEX:                                                  # (9) = power diagram
    h = [s.NumVar(0, s.infinity(), "") for i in range(M)]
    BIG = float((D ** 2).max())
    for j in range(N):
        for i1 in range(M):
            for i2 in range(M):
                if i1 != i2:
                    s.Add(h[i2] - h[i1] + BIG * x[j][i1] + BIG * z[i2]
                          <= float(D[j, i2] ** 2 - D[j, i1] ** 2) + BIGK * BIG)
s.Minimize(sum(float(D[j, i]) * x[j][i] for j in range(N) for i in range(M)) + S_.OMEGA * sum(u))
t = time.time()
st = s.Solve()
a = np.array([max(range(M), key=lambda i: x[j][i].solution_value()) for j in range(N)])
yy = np.array([round(y[i].solution_value()) for i in range(M)])
print(f"MIP convex={CONVEX} status={st} obj={s.Objective().Value():,.0f} bound={s.Objective().BestBound():,.0f} t={time.time()-t:.1f}s")
S_.report("MIP solution (rechecked)", a, yy, time.time() - t)
