#!/usr/bin/env python3
"""Почему необслуженные сайты нельзя добавить: навыки, ёмкость или геометрия."""
import json, sys
from shapely import MultiPoint, Point

inst = json.load(open(sys.argv[1])); sol = json.load(open(sys.argv[2]))
S, O, W, D = inst['sites'], inst['offices'], inst['workers'], inst['distances']
n, K = len(S), len(O)
Nk = {}
for w in W:
    for k in set(w): Nk[k] = Nk.get(k, 0) + 1
asg = {s: o['officeId'] for o in sol for s in o['sites']}
opened = [o['officeId'] for o in sol]
mem = {o['officeId']: list(o['sites']) for o in sol}
pts = [Point(s['x'], s['y']) for s in S] + [Point(o['x'], o['y']) for o in O]
hulls = {}
for o in opened:
    hulls[o] = MultiPoint([pts[s] for s in mem[o]] + [pts[n + o]]).convex_hull
cov = [sum(1 for o in opened if hulls[o].covers(p)) for p in pts]
# какие навыки зона уже использует и сколько зон на навык
zsk = {o: {k for s in mem[o] for k in S[s]['tasks']} for o in opened}
used = {k: sum(1 for o in opened if k in zsk[o]) for k in Nk}

reasons = {'навыки': 0, 'ёмкость': 0, 'геометрия': 0, 'можно добавить': 0, 'невыполнимы': 0}
pot = dict(reasons)
for s in range(n):
    if s in asg: continue
    best = max((S[s]['reward'] - D[o][s] for o in range(K)), default=0)
    if best <= 0: continue
    if any(Nk.get(k, 0) == 0 for k in S[s]['tasks']):
        reasons['невыполнимы'] += 1; pot['невыполнимы'] += best; continue
    why = set()
    ok = False
    for o in opened:
        if S[s]['reward'] - D[o][s] <= 0: continue
        if any(k not in zsk[o] and used.get(k, 0) >= Nk.get(k, 0) for k in S[s]['tasks']):
            why.add('навыки'); continue
        if len(mem[o]) >= O[o]['maxSize']:
            why.add('ёмкость'); continue
        h = MultiPoint([pts[x] for x in mem[o]] + [pts[n + o], pts[s]]).convex_hull
        bad = any(cov[i] - (1 if hulls[o].covers(pts[i]) else 0) > 0 and h.covers(pts[i])
                  for i in range(len(pts)))
        if bad: why.add('геометрия'); continue
        ok = True; break
    if ok: reasons['можно добавить'] += 1; pot['можно добавить'] += best
    else:
        r = 'геометрия' if 'геометрия' in why else ('ёмкость' if 'ёмкость' in why else
            ('навыки' if 'навыки' in why else 'геометрия'))
        reasons[r] += 1; pot[r] += best
print(f"  необслуженные с положительным потенциалом — по причинам:")
for k in reasons:
    if reasons[k]: print(f"    {k:16} {reasons[k]:5} шт, потенциал {pot[k]:12.1f}")
