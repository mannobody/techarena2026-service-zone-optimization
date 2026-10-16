#!/usr/bin/env python3
"""Генератор синтетических инстансов под скрытые тесты.

Режимы повторяют характер открытых: евклид, манхэттен, дорожные расстояния,
антикоррелированные с геометрией, офисы в углу, дефицит навыков.
"""
import json, math, random, sys


def gen(seed, ns, no, nw, nsk, mode, alpha_mode, A_mode, out):
    rnd = random.Random(seed)
    span = rnd.choice([1.0, 100.0, 1000.0])
    sites_xy = [(rnd.uniform(0, span), rnd.uniform(0, span)) for _ in range(ns)]
    if mode == 'corner':
        off_xy = [(-0.05 * span - rnd.random() * 0.02 * span, -0.05 * span - rnd.random() * 0.02 * span)
                  for _ in range(no)]
    elif mode == 'perimeter':
        off_xy = []
        for i in range(no):
            t = i / no * 4
            s = t % 1
            if t < 1: off_xy.append((s * span, -0.07 * span))
            elif t < 2: off_xy.append((span * 1.07, s * span))
            elif t < 3: off_xy.append(((1 - s) * span, span * 1.07))
            else: off_xy.append((-0.07 * span, (1 - s) * span))
    else:
        off_xy = [(rnd.uniform(0, span), rnd.uniform(0, span)) for _ in range(no)]

    # число задач на сайт
    tmax = rnd.choice([1, 2, 3, 6, 12])
    tasks = []
    for _ in range(ns):
        n = rnd.randint(0, tmax)
        tasks.append([rnd.randrange(nsk) for _ in range(n)])
    # навыки рабочих: обычно по одному
    workers = [[rnd.randrange(nsk)] for _ in range(nw)]
    if rnd.random() < 0.2:
        workers = [[rnd.randrange(nsk) for _ in range(rnd.randint(1, 2))] for _ in range(nw)]

    def eu(a, b):
        return math.dist(a, b)

    D = []
    for o in range(no):
        row = []
        for s in range(ns):
            if mode == 'manhattan':
                d = abs(off_xy[o][0] - sites_xy[s][0]) + abs(off_xy[o][1] - sites_xy[s][1])
            elif mode == 'road':
                d = eu(off_xy[o], sites_xy[s]) * rnd.uniform(0.3, 3.0)
            elif mode == 'anti':
                d = (span * 1.6 - eu(off_xy[o], sites_xy[s])) * rnd.uniform(0.8, 1.2)
            else:
                d = eu(off_xy[o], sites_xy[s])
            row.append(max(0.0, d))
        D.append(row)
    mean_d = sum(sum(r) for r in D) / (no * ns)
    reward = mean_d * rnd.uniform(0.7, 2.2)
    cost = [mean_d * ns / no * rnd.uniform(0.002, 0.05) for _ in range(no)]
    cap = [rnd.randint(max(1, ns // (no * 3)), max(2, ns // max(1, no - 1))) for _ in range(no)]
    total_tasks = sum(len(t) for t in tasks)
    alpha = {'zero': 0.0, 'small': reward * 0.01, 'big': reward * max(1.0, ns / 50.0)}[alpha_mode]
    A = {'free': ns, 'tight': max(1, ns // (no * 6)), 'mid': max(1, ns // (no * 2))}[A_mode]
    inst = {
        'sites': [{'x': sites_xy[s][0], 'y': sites_xy[s][1], 'reward': reward, 'tasks': tasks[s]}
                  for s in range(ns)],
        'offices': [{'x': off_xy[o][0], 'y': off_xy[o][1], 'cost': cost[o], 'maxSize': cap[o]}
                    for o in range(no)],
        'workers': workers,
        'distances': D,
        'maxDifference': A,
        'balanceCoefficient': alpha,
    }
    json.dump(inst, open(out, 'w'))
    return dict(ns=ns, no=no, nw=nw, nsk=nsk, mode=mode, alpha=alpha_mode, A=A_mode,
                tasks=total_tasks, cap=sum(cap))


if __name__ == '__main__':
    outdir = sys.argv[1]
    cfgs = []
    rnd = random.Random(7)
    modes = ['euclid', 'manhattan', 'road', 'anti', 'corner', 'perimeter']
    for i in range(int(sys.argv[2]) if len(sys.argv) > 2 else 12):
        ns = rnd.choice([30, 100, 200, 400, 800, 2000, 5000])
        no = rnd.choice([2, 3, 5, 8, 12, 20])
        nsk = rnd.choice([1, 2, 3, 5, 8])
        nw = rnd.choice([max(1, nsk), nsk * 2, nsk * 3, no * 2])
        info = gen(1000 + i, ns, no, nw, nsk, rnd.choice(modes),
                   rnd.choice(['zero', 'small', 'big']),
                   rnd.choice(['free', 'tight', 'mid']),
                   f'{outdir}/gen{i}.json')
        cfgs.append((i, info))
        print(i, info)
