#!/usr/bin/env python3
"""Генератор синтетических инстансов под скрытые тесты.

    python3 tools/gen.py OUTDIR [N=12] [--edge]
    python3 tools/gen.py OUTDIR --suite

genK.json — случайные режимы (евклид, манхэттен, дороги, дороги против геометрии,
офисы в углу/по периметру, дефицит навыков, многопрофильные рабочие).
--edge добавляет edge_*.json: граничные случаи и самый крупный размер.
Набор детерминирован (фиксированные зёрна), его гоняет `bench.py --synth`.
--suite — только suite_<класс><i>.json: набор по классам закрытых тестов для оценки
качества (`bench.py --suite`), а не только валидности.
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


def gen2(seed, out, ns, no, nw, nsk, layout='uniform', offices='random', dist='euclid', span=None,
         dscale=1.0, tmax=3, wsk=1, deficit=0, af=0.01, A=None, capf=1.0, rnear=None, cf=(0.01, 0.1)):
    """Гибкий генератор для --suite. af — α в долях reward; A=None — ns/(2·no).
    rnear=(a, b) — reward = среднее расстояние до ближайшего офиса × U(a, b) (тонкая маржа);
    cf — стоимость офиса в долях reward·ns/no."""
    rnd = random.Random(seed)
    span = span or rnd.choice([1.0, 100.0, 1000.0])
    if layout == 'cluster':
        cs = [(rnd.uniform(0, span), rnd.uniform(0, span), span * rnd.uniform(0.03, 0.12))
              for _ in range(rnd.randint(3, 8))]
        pts = []
        for _ in range(ns):
            cx, cy, r = rnd.choice(cs)
            pts.append((rnd.gauss(cx, r), rnd.gauss(cy, r)))
    elif layout == 'grid':   # решётка: коллинеарные точки и дубликаты
        g = max(2, int(math.sqrt(ns * 0.7)))
        pts = [(span * rnd.randrange(g) / g, span * rnd.randrange(g) / g) for _ in range(ns)]
    else:
        pts = [(rnd.uniform(0, span), rnd.uniform(0, span)) for _ in range(ns)]
    if offices == 'perimeter':
        offs = []
        for i in range(no):
            t = (i + rnd.random() * 0.5) / no * 4
            q, f = int(t) % 4, t % 1
            offs.append([(f * span, -0.05 * span), (1.05 * span, f * span),
                         ((1 - f) * span, 1.05 * span), (-0.05 * span, (1 - f) * span)][q])
    elif offices == 'onsite':   # офисы в точках сайтов
        offs = [rnd.choice(pts) for _ in range(no)]
    else:
        offs = [(rnd.uniform(0, span), rnd.uniform(0, span)) for _ in range(no)]
    tasks = [[rnd.randrange(nsk) for _ in range(rnd.randint(0 if tmax > 1 else 1, tmax))] for _ in range(ns)]
    # навыки рабочих: wsk на рабочего; первые deficit навыков — 0 или 1 рабочий
    skills = list(range(nsk))
    workers = []
    for k in range(deficit):
        if k % 2:
            workers.append([k])
    rest = skills[deficit:] or skills
    while len(workers) < nw:
        workers.append(sorted(set(rnd.choice(rest) for _ in range(rnd.randint(1, wsk)))))
    D = []
    for o in range(no):
        row = []
        for x in range(ns):
            e = math.dist(offs[o], pts[x])
            if dist == 'manhattan':
                d = abs(offs[o][0] - pts[x][0]) + abs(offs[o][1] - pts[x][1])
            elif dist == 'road':
                d = e * rnd.uniform(0.8, 2.0)
            elif dist == 'anti':
                d = (span * 1.6 - e) * rnd.uniform(0.8, 1.2)
            else:
                d = e
            row.append(max(0.0, d) * dscale)
        D.append(row)
    mean_d = sum(map(sum, D)) / max(1, no * ns)
    if rnear:   # награда ≈ расстояние до ближайшего офиса: прибыль сайтов около нуля
        near = sum(min(D[o][x] for o in range(no)) for x in range(ns)) / max(1, ns)
        reward = near * rnd.uniform(*rnear)
    else:
        reward = mean_d * rnd.uniform(0.8, 2.0)
    cost = [reward * ns / no * rnd.uniform(*cf) for _ in range(no)]
    cap = [max(1, int(ns / no * capf * rnd.uniform(0.6, 1.4))) for _ in range(no)]
    json.dump({'sites': [{'x': p[0], 'y': p[1], 'reward': reward, 'tasks': t} for p, t in zip(pts, tasks)],
               'offices': [{'x': o[0], 'y': o[1], 'cost': c, 'maxSize': m} for o, c, m in zip(offs, cost, cap)],
               'workers': workers, 'distances': D,
               'maxDifference': max(0, ns // (2 * no)) if A is None else A,
               'balanceCoefficient': reward * af}, open(out, 'w'))


# класс -> (число инстансов, функция параметров от rnd); зёрна фиксированы
SUITE = {
    'small': (4, lambda r: dict(ns=r.choice([60, 100, 150]), no=r.choice([2, 3, 4]), nw=r.choice([3, 5, 6]),
                                nsk=3, tmax=2, dist=r.choice(['euclid', 'road']))),
    'medium': (4, lambda r: dict(ns=r.choice([200, 350, 600]), no=r.choice([5, 8, 10]), nw=20, nsk=4,
                                 dist=r.choice(['euclid', 'road', 'manhattan']))),
    'large': (4, lambda r: dict(ns=r.choice([2000, 3500, 5000]), no=r.choice([10, 15, 20]), nw=40, nsk=5,
                                dist=r.choice(['euclid', 'road']))),
    'huge': (2, lambda r: dict(ns=10000, no=r.choice([20, 25]), nw=50, nsk=5, dist='road')),
    'multiskill': (4, lambda r: dict(ns=r.choice([150, 400]), no=r.choice([4, 6, 8]), nw=r.choice([8, 12]),
                                     nsk=r.choice([4, 6, 8]), wsk=3, tmax=3)),
    'deficit': (4, lambda r: dict(ns=r.choice([150, 400]), no=r.choice([4, 6]), nw=r.choice([6, 10]),
                                  nsk=5, deficit=r.choice([2, 3]))),
    'alphazero': (4, lambda r: dict(ns=r.choice([200, 600]), no=r.choice([5, 10]), nw=20, nsk=4, af=0.0)),
    'alphabig': (4, lambda r: dict(ns=r.choice([300, 600]), no=r.choice([8, 15]), nw=30, nsk=4,
                                   span=1.0, dscale=1e5, af=r.choice([2.0, 5.0]), tmax=6)),
    'tightA': (4, lambda r: dict(ns=r.choice([150, 400]), no=r.choice([4, 8]), nw=16, nsk=4,
                                 A=r.choice([0, 1, 2]), capf=r.choice([0.5, 1.0]))),
    'cluster': (4, lambda r: dict(ns=r.choice([200, 600, 1500]), no=r.choice([5, 10]), nw=20, nsk=4,
                                  layout='cluster', offices=r.choice(['random', 'onsite']))),
    'anti': (4, lambda r: dict(ns=r.choice([150, 330, 600]), no=r.choice([5, 10]), nw=20, nsk=3,
                               dist='anti', offices=r.choice(['random', 'perimeter']))),
    'grid': (4, lambda r: dict(ns=r.choice([100, 300]), no=r.choice([3, 6]), nw=12, nsk=3,
                               layout='grid', offices='onsite')),
    # тонкая маржа (как открытый instance2: obj/Σreward ≈ 0.02): reward ≈ расстояние до ближайшего офиса,
    # офис стоит сопоставимо с целевой — малые ошибки в наборе офисов и сайтах дают десятки процентов
    'thin': (6, lambda r: dict(ns=r.choice([100, 400, 1500, 5000]), no=r.choice([3, 5, 10, 20]), nw=20, nsk=4,
                               dist=r.choice(['euclid', 'road']), rnear=(1.0, 1.3), cf=(0.03, 0.12),
                               af=r.choice([0.0, 0.01, 0.5]))),
}


def suite(outdir):
    for cls, (n, mk) in SUITE.items():
        for i in range(n):
            seed = 9000 + 100 * list(SUITE).index(cls) + i
            gen2(seed, f'{outdir}/suite_{cls}{i}.json', **mk(random.Random(seed)))


if __name__ == '__main__':
    outdir = sys.argv[1]
    if '--suite' in sys.argv:
        suite(outdir)
        sys.exit()
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
