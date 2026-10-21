#!/usr/bin/env python3
"""Инстансы «как у жюри» по образцу inst3 (anti: d ≈ C − 0.9·E + шум, офисы по периметру, 1–15 задач на сайт,
α ≈ 0.18·reward, A ≈ 2·ns/no) и inst4 (L1, кластеры, дефицит рабочих: 2·no рабочих на 5 навыков, A ≈ 0.6·ns/no).
Во всех официальных инстансах награда постоянна, рабочие однонавыковые.
  python3 tools/offgen.py OUTDIR   — off3_<seed>.json, off4_<seed>.json, seed 1..4"""
import json, sys, random, math
from pathlib import Path


def like3(seed):
    r = random.Random(seed)
    ns = r.choice([250, 330, 400]); no = r.choice([8, 10, 12])
    W = 1000.0
    sites = [(r.uniform(0, W), r.uniform(0, W * 0.99)) for _ in range(ns)]
    offs = []
    for _ in range(no):
        if r.random() < 0.6:                      # периметр (с выносом наружу)
            side = r.randrange(4); t = r.uniform(0, W); m = r.uniform(-100, 100)
            p = [(t, -abs(m)), (t, W + abs(m)), (-abs(m), t), (W + abs(m), t)][side]
        else:
            p = (r.uniform(0, W), r.uniform(0, W))
        offs.append(p)
    C = r.uniform(1150, 1350); k = r.uniform(0.8, 1.0); sd = r.uniform(100, 150)
    D = [[max(10.0, C - k * math.dist(o, s) + r.gauss(0, sd)) for s in sites] for o in offs]
    md = sum(map(sum, D)) / (ns * no)
    reward = md * r.uniform(1.6, 1.9)
    K = 3
    wts = [0.2, 0.39, 0.41]
    tasks = []
    for _ in range(ns):
        n = max(1, min(15, int(round(r.gauss(6.8, 3.2)))))
        tasks.append(sorted(r.choices(range(K), wts, k=n)))
    nw = 20
    workers = [[0]] * 5 + [[1]] * 6 + [[2]] * 9
    r.shuffle(workers)
    cost = [reward * r.uniform(0.3, 0.75) for _ in range(no)]
    base = ns / no
    maxs = [int(base * r.uniform(2.0, 3.9)) for _ in range(no)]
    A = int(round(2 * base))
    alpha = reward * r.uniform(0.12, 0.25)
    return ns, sites, offs, D, reward, tasks, workers, cost, maxs, A, alpha


def like4(seed):
    r = random.Random(seed)
    ns = r.choice([150, 200, 250]); no = r.choice([4, 5, 6])
    W = 140.0
    nc = r.randint(14, 24)
    cent = [(r.uniform(5, W - 5), r.uniform(5, W - 5)) for _ in range(nc)]
    sites = []
    for _ in range(ns):
        c = r.choice(cent)
        sites.append((min(W, max(0, c[0] + r.gauss(0, 4))), min(W, max(0, c[1] + r.gauss(0, 4)))))
    offs = [(r.uniform(0, W), r.uniform(0, W)) for _ in range(no)]
    D = [[abs(o[0] - s[0]) + abs(o[1] - s[1]) for s in sites] for o in offs]
    md = sum(map(sum, D)) / (ns * no)
    reward = md * r.uniform(1.7, 2.1)
    K = 5
    wts = [r.uniform(0.3, 1.5) for _ in range(K)]
    tasks = []
    for _ in range(ns):
        n = r.choices([1, 2, 3], [0.75, 0.2, 0.05])[0]
        tasks.append(sorted(set(r.choices(range(K), wts, k=n))))
    nw = 2 * no
    per = [1] * K
    for _ in range(nw - K):
        per[r.randrange(K)] += 1
    workers = [[k] for k in range(K) for _ in range(per[k])]
    cost = [reward * r.uniform(0.55, 0.95) for _ in range(no)]
    base = ns / no
    maxs = [int(base * r.uniform(1.05, 1.5)) for _ in range(no)]
    A = int(round(base * r.uniform(0.5, 0.75)))
    alpha = reward * 0.0006
    return ns, sites, offs, D, reward, tasks, workers, cost, maxs, A, alpha


def dump(path, ns, sites, offs, D, reward, tasks, workers, cost, maxs, A, alpha):
    I = {'sites': [{'x': x, 'y': y, 'reward': reward, 'tasks': t} for (x, y), t in zip(sites, tasks)],
         'offices': [{'x': x, 'y': y, 'cost': c, 'maxSize': m} for (x, y), c, m in zip(offs, cost, maxs)],
         'workers': workers, 'distances': D, 'maxDifference': A, 'balanceCoefficient': alpha}
    json.dump(I, open(path, 'w'))


if __name__ == '__main__':
    out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
    for seed in range(1, 5):
        dump(out / f'off3_{seed}.json', *like3(seed))
        dump(out / f'off4_{seed}.json', *like4(seed))
    print('ok')
