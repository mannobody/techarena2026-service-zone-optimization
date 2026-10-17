"""Верхняя оценка: MIP без геометрии (размеры, A, навыки при однонавыковых рабочих, баланс).
python3 ub_mip.py instance.json [секунды]"""
import json
import sys

from ortools.linear_solver import pywraplp

I = json.load(open(sys.argv[1]))
TL = float(sys.argv[2]) if len(sys.argv) > 2 else 60
S, O, W, D = I["sites"], I["offices"], I["workers"], I["distances"]
A, al = I["maxDifference"], I["balanceCoefficient"]
ns, no = len(S), len(O)
skills = sorted({k for s in S for k in s["tasks"]})
wcnt = {k: sum(k in w for w in W) for k in skills}
m = pywraplp.Solver.CreateSolver("SCIP")
m.SetTimeLimit(int(TL * 1000))
z = [m.BoolVar("") for _ in range(no)]
sk = {(o, k): m.BoolVar("") for o in range(no) for k in skills}
x = {}
for o in range(no):
    for s in range(ns):
        if S[s]["reward"] - D[o][s] > 0 and all(wcnt[k] > 0 for k in S[s]["tasks"]):
            x[o, s] = m.BoolVar("")
            m.Add(x[o, s] <= z[o])
            for k in set(S[s]["tasks"]):
                m.Add(x[o, s] <= sk[o, k])
for k in skills:
    m.Add(sum(sk[o, k] for o in range(no)) <= wcnt[k])  # верно для однонавыковых рабочих
for s in range(ns):
    m.Add(sum(x[o, s] for o in range(no) if (o, s) in x) <= 1)
size = [sum(x[o, s] for s in range(ns) if (o, s) in x) for o in range(no)]
load = [sum(len(S[s]["tasks"]) * x[o, s] for s in range(ns) if (o, s) in x) for o in range(no)]
BIGS, BIGL = ns + 1, sum(len(s["tasks"]) for s in S) + 1
for o in range(no):
    m.Add(size[o] <= O[o]["maxSize"] * z[o])
    for p in range(no):
        if p != o:
            m.Add(size[o] - size[p] <= A + BIGS * (2 - z[o] - z[p]))
Lmax, Lmin = m.NumVar(0, BIGL, ""), m.NumVar(0, BIGL, "")
m.Add(Lmin <= Lmax)
for o in range(no):
    m.Add(Lmax >= load[o])
    m.Add(Lmin <= load[o] + BIGL * (1 - z[o]))
obj = sum((S[s]["reward"] - D[o][s]) * v for (o, s), v in x.items()) - sum(O[o]["cost"] * z[o] for o in range(no)) - al * (Lmax - Lmin)
m.Maximize(obj)
st = m.Solve()
print(f"status={st} best={m.Objective().Value():.3f} upper_bound={m.Objective().BestBound():.3f} "
      f"open={[o for o in range(no) if z[o].solution_value() > .5]}")

if len(sys.argv) > 3:
    out = []
    for o in range(no):
        if z[o].solution_value() > .5:
            out.append({"officeId": o, "sites": [s for s in range(ns) if (o, s) in x and x[o, s].solution_value() > .5],
                        "skills": [k for k in skills if sk[o, k].solution_value() > .5]})
    json.dump(out, open(sys.argv[3], "w"))
