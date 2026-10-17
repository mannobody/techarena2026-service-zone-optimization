#!/usr/bin/env python3
"""Генератор синтетических инстансов под скрытые тесты.

    python3 tools/gen.py OUTDIR [N=12] [--edge]

genK.json — случайные режимы (евклид, манхэттен, дороги, дороги против геометрии,
офисы в углу/по периметру, дефицит навыков, многопрофильные рабочие).
--edge добавляет edge_*.json: граничные случаи и самый крупный размер.
Набор детерминирован (фиксированные зёрна), его гоняет `bench.py --synth`.
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


def edge(outdir):
    """Граничные случаи из CLAUDE.md: решатель обязан выдать валидный ответ."""
    def inst(name, sites, offices, workers, D=None, A=1, alpha=1.0):
        if D is None:
            D = [[math.dist((o['x'], o['y']), (s['x'], s['y'])) for s in sites] for o in offices]
        json.dump({'sites': sites, 'offices': offices, 'workers': workers, 'distances': D,
                   'maxDifference': A, 'balanceCoefficient': alpha}, open(f'{outdir}/edge_{name}.json', 'w'))
    S = lambda x, y, r=10.0, t=(0,): {'x': x, 'y': y, 'reward': r, 'tasks': list(t)}
    O = lambda x, y, c=1.0, m=5: {'x': x, 'y': y, 'cost': c, 'maxSize': m}
    grid = [S(i % 7, i // 7) for i in range(40)]
    two = [O(-1, -1), O(8, 7)]
    inst('empty', [], [O(0, 0)], [[0]])
    inst('no_offices', grid[:5], [], [[0]])
    inst('one_site', [S(1, 1)], [O(0, 0)], [[0]])
    inst('no_workers', grid, two, [])
    inst('skill_missing', [S(i, 0, t=(1,)) for i in range(10)], two, [[0], [0]])
    inst('maxsize0', grid, [O(-1, -1, m=0), O(8, 7, m=0)], [[0], [0]])
    inst('same_point', [S(1, 1) for _ in range(20)] + [S(3, 3)], [O(1, 1), O(3, 3)], [[0], [0]])
    inst('collinear', [S(i, 0) for i in range(30)], [O(-1, 0), O(30, 0), O(15, 0)], [[0], [0], [0]])
    inst('alpha0', grid, two, [[0], [0]], alpha=0.0)
    inst('alpha_huge', grid, two, [[0], [0]], alpha=1e12)
    inst('A0', grid, two, [[0], [0]], A=0)
    inst('A_big', grid, two, [[0], [0]], A=10**6)
    inst('multiskill', [S(i % 9, i // 9, t=(i % 3, (i + 1) % 3)) for i in range(60)],
         [O(-1, -1, m=30), O(9, 7, m=30), O(4, -2, m=30)], [[0, 1], [1, 2], [2, 0]])
    inst('no_tasks', [S(i % 7, i // 7, t=()) for i in range(40)], two, [])
    inst('unit_coords_big_dist', [S(rx / 50, (rx * 7 % 50) / 50, r=5e4) for rx in range(50)],
         [O(0, 0, c=1e4, m=30), O(1, 1, c=1e4, m=30)], [[0], [0]],
         D=[[1e5 * math.dist((ox, oy), (rx / 50, (rx * 7 % 50) / 50)) for rx in range(50)] for ox, oy in ((0, 0), (1, 1))])
    gen(4242, 10000, 20, 40, 5, 'road', 'small', 'mid', f'{outdir}/edge_big10k.json')


if __name__ == '__main__':
    outdir = sys.argv[1]
    if '--edge' in sys.argv:
        sys.argv.remove('--edge')
        edge(outdir)
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
