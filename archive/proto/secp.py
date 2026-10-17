"""
SECP (Service Engineer Clustering Problem) по статье Davydov et al., MOTOR 2024.

Модель (раздел 3 статьи):
  I — кандидаты в офисы, J — сайты, d_ij — расстояние (у нас евклидово, метры),
  y_i ∈ [0, Rmax_i] — инженеры в офисе, sum y_i = p, офис открыт <=> y_i > 0;
  v_jw — нагрузка сайта по метрике w; коридор [Vlb*y_i, Vub*y_i] на офис;
  u_w = максимальное нарушение коридора по метрике w среди офисов (мягкое);
  F = sum d_ij x_ij + omega * sum_w u_w;
  предпочтения: I_j = {i : d_ij < D}; если в I_j есть открытый офис, сайт обязан
  обслуживаться из I_j;
  геометрия: free / convex (оболочки зон не пересекаются) / star.

Ключевая идея (наша): ограничение (9) статьи для convex — это ровно power diagram:
сайт j идёт в офис argmin_i (d_ij^2 - h_i). Значит вместо поиска по назначениям
ищем K весов h_i: любая точка этого пространства выпукла по построению, а если
офис лежит в своей ячейке, то и звёздна.

Запуск: python3 secp.py [seed] [n_sites] [n_offices] [p] [seconds]
"""
import math
import sys
import time

import numpy as np

SEED = int(sys.argv[1]) if len(sys.argv) > 1 else 1
N = int(sys.argv[2]) if len(sys.argv) > 2 else 1000
M = int(sys.argv[3]) if len(sys.argv) > 3 else 15
P = int(sys.argv[4]) if len(sys.argv) > 4 else 18
SECONDS = float(sys.argv[5]) if len(sys.argv) > 5 else 30
OMEGA = 1000.0
NW = 2  # число метрик нагрузки
rng = np.random.default_rng(SEED)


# ---------------------------------------------------------------- инстанс
def make_instance():
    # Сайты: смесь «городов» (гауссовы кластеры) и равномерного фона, поле 100x100 км.
    centers = rng.uniform(10_000, 90_000, size=(8, 2))
    k = rng.integers(0, 8, size=int(N * 0.7))
    city = centers[k] + rng.normal(0, 6_000, size=(len(k), 2))
    bg = rng.uniform(0, 100_000, size=(N - len(k), 2))
    S = np.clip(np.vstack([city, bg]), 0, 100_000)
    O = np.vstack([centers, rng.uniform(5_000, 95_000, size=(M - 8, 2))])[:M]
    v = rng.integers(1, 6, size=(N, NW)).astype(float)
    v[:, 1] = rng.integers(0, 3, size=N)  # вторая метрика разреженная
    rmax = rng.integers(2, 5, size=M)
    return S, O, v, rmax


S, O, v, RMAX = make_instance()
D = np.linalg.norm(S[:, None, :] - O[None, :, :], axis=2)  # N x M
D2 = D ** 2
AVG = v.sum(0) / P
VLB, VUB = 0.8 * AVG, 1.2 * AVG
DPREF = float(sys.argv[6]) if len(sys.argv) > 6 and sys.argv[6] else np.quantile(D.min(1), 0.5) * 1.5  # порог D для предпочтений (наше допущение)
PREF = D < DPREF  # N x M
SCALE2 = float(np.median(D.min(1))) ** 2  # масштаб шага для весов h


# ------------------------------------------------------------ оценка
def allowed_mask(y):
    open_ = y > 0
    has_pref = (PREF & open_[None, :]).any(1)
    return np.where(has_pref[:, None], PREF & open_[None, :], open_[None, :])


def penalty(assign, y):
    loads = np.zeros((M, NW))
    np.add.at(loads, assign, v)
    viol = np.maximum(VLB[None, :] * y[:, None] - loads, loads - VUB[None, :] * y[:, None])
    viol[y == 0] = 0
    return np.maximum(viol, 0).max(0).sum()


def F(assign, y):
    return D[np.arange(N), assign].sum() + OMEGA * penalty(assign, y)


def F_search(assign, y):
    # Суррогат для поиска: штраф статьи берёт максимум по офисам, у него плато.
    # Добавляем малую долю суммы нарушений, чтобы ходы «чинили» и не-максимальные офисы.
    loads = np.zeros((M, NW))
    np.add.at(loads, assign, v)
    viol = np.maximum(VLB[None, :] * y[:, None] - loads, loads - VUB[None, :] * y[:, None])
    viol[y == 0] = 0
    viol = np.maximum(viol, 0)
    return D[np.arange(N), assign].sum() + OMEGA * (viol.max(0).sum() + 0.2 * viol.sum())


def power_assign(h, mask):
    score = np.where(mask, D2 - h[None, :], np.inf)
    return score.argmin(1)


# ------------------------------------------------- проверки геометрии
def cross(o, a, b):
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def hull(pts):
    pts = sorted(map(tuple, pts))
    if len(pts) <= 2:
        return pts
    lo, up = [], []
    for p_ in pts:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p_) <= 0:
            lo.pop()
        lo.append(p_)
    for p_ in reversed(pts):
        while len(up) >= 2 and cross(up[-2], up[-1], p_) <= 0:
            up.pop()
        up.append(p_)
    return lo[:-1] + up[:-1]


def separable(h1, h2):
    # Разделяющая ось для двух выпуклых многоугольников (SAT).
    for poly in (h1, h2):
        n = len(poly)
        for i in range(n if n > 1 else 0):
            a, b = np.array(poly[i]), np.array(poly[(i + 1) % n])
            ax = np.array([a[1] - b[1], b[0] - a[0]])
            p1 = np.array(h1) @ ax
            p2 = np.array(h2) @ ax
            if p1.max() < p2.min() - 1e-6 or p2.max() < p1.min() - 1e-6:
                return True
    return len(h1) < 3 and len(h2) < 3


def convex_violations(assign, y):
    # Зона = сайты + сам офис (как на рис. 1 статьи).
    H = {i: hull(np.vstack([S[assign == i], O[i:i + 1]])) for i in np.flatnonzero(y)}
    ks = list(H)
    return sum(1 for a in range(len(ks)) for b in range(a + 1, len(ks)) if not separable(H[ks[a]], H[ks[b]]))


def office_in_own_cell(h, y):
    # Если офис лежит в своей power-ячейке, ячейка звёздна относительно офиса.
    op = np.flatnonzero(y)
    d2 = ((O[op][:, None, :] - O[op][None, :, :]) ** 2).sum(2)
    sc = d2 - h[op][None, :]
    return int((sc.argmin(1) != np.arange(len(op))).sum())


# ------------------------------------------ нижний уровень: поиск весов h
def optimize_weights(y, iters=300, h0=None):
    mask = allowed_mask(y)
    h = np.zeros(M) if h0 is None else h0.copy()
    a = power_assign(h, mask)
    best = F_search(a, y)
    step = np.full(M, SCALE2)
    op = np.flatnonzero(y)
    order = []
    for _ in range(iters):
        if not order:
            order = list(rng.permutation(op))
        i = order.pop()
        moved = False
        for sgn in (1, -1):
            h[i] += sgn * step[i]
            a2 = power_assign(h, mask)
            f2 = F_search(a2, y)
            if f2 < best - 1e-9:
                best, a, moved = f2, a2, True
                step[i] *= 1.5
                break
            h[i] -= sgn * step[i]
        if not moved:
            step[i] *= 0.6
    return F(a, y), a, h


# ---------------- нижний уровень, как в статье: стохастический flip-поиск
def flip_search(a, y, iters=40, frac=0.1):
    mask = allowed_mask(y)
    a = a.copy()
    loads = np.zeros((M, NW))
    np.add.at(loads, a, v)
    cur = F_search(a, y)
    for _ in range(iters):
        improved = False
        for j in rng.choice(N, size=int(N * frac), replace=False):
            src = a[j]
            for dst in np.flatnonzero(mask[j]):
                if dst == src:
                    continue
                a[j] = dst
                f2 = F_search(a, y)
                if f2 < cur - 1e-9:
                    cur, improved = f2, True
                    break
                a[j] = src
        if not improved:
            break
    return F(a, y), a


# ---------------------------------- старт: жадная p-медиана + раздача штата
def greedy_start():
    y = np.zeros(M, int)
    p1 = min(P, M)
    opened = []
    for _ in range(p1):
        best = None
        for i in range(M):
            if i in opened:
                continue
            c = D[:, opened + [i]].min(1).sum()
            if best is None or c < best[0]:
                best = (c, i)
        opened.append(best[1])
    y[opened] = 1
    # остаток раздаём пропорционально «ближайшей» нагрузке с учётом Rmax
    while y.sum() < P:
        a = np.where(y[None, :] > 0, D, np.inf).argmin(1)
        load = np.bincount(a, weights=v[:, 0], minlength=M)
        ratio = np.where((y > 0) & (y < RMAX), load / np.maximum(y, 1), -1)
        y[ratio.argmax()] += 1
    return y


# ------------------------------- верхний уровень: tabu по распределению SE
def tabu_upper(y, seconds, tenure=5):
    t_end = time.time() + seconds
    best_f, best_a, best_h = optimize_weights(y)
    best_y = y.copy()
    cur_y, cur_h = y.copy(), best_h
    tabu = {}
    it = 0
    while time.time() < t_end:
        it += 1
        cand = []
        src_list = np.flatnonzero(cur_y > 0)
        for _ in range(8):  # стохастическая выборка окрестности move
            s = rng.choice(src_list)
            d = rng.integers(M)
            if d == s or cur_y[d] >= RMAX[d] or tabu.get(d, 0) > it:
                continue
            ny = cur_y.copy()
            ny[s] -= 1
            ny[d] += 1
            f, a, h = optimize_weights(ny, iters=120, h0=cur_h)
            cand.append((f, ny, a, h, d))
        if not cand:
            continue
        f, ny, a, h, d = min(cand, key=lambda c: c[0])
        cur_y, cur_h = ny, h
        tabu[d] = it + tenure
        if f < best_f:
            best_f, best_a, best_y, best_h = f, a, ny.copy(), h.copy()
            best_f, best_a, best_h = optimize_weights(best_y, iters=400, h0=best_h)
    return best_f, best_a, best_y, best_h, it


def report(name, a, y, t, h=None):
    dist = D[np.arange(N), a].sum()
    extra = f" office_outside_cell={office_in_own_cell(h, y)}" if h is not None else ""
    print(f"{name:38s} F={F(a, y):14,.0f} dist={dist:12,.0f} pen={penalty(a, y):7.1f} "
          f"open={int((y > 0).sum()):2d} convex_viol={convex_violations(a, y):2d}{extra} t={t:5.1f}s")


if __name__ == "__main__":
    print(f"seed={SEED} sites={N} offices={M} p={P} Rmax={RMAX.tolist()} omega={OMEGA}")
    t = time.time(); y0 = greedy_start()
    a0 = np.where(allowed_mask(y0), D, np.inf).argmin(1)
    report("0) greedy + nearest office", a0, y0, time.time() - t)
    t = time.time(); f1, a1 = flip_search(a0, y0)
    report("1) + flip search (as in paper, free)", a1, y0, time.time() - t)
    t = time.time(); f2, a2, h2 = optimize_weights(y0, iters=600)
    report("2) power weights, fixed staff", a2, y0, time.time() - t, h2)
    t = time.time(); f3, a3, y3, h3, it = tabu_upper(y0, SECONDS)
    report(f"3) power weights + tabu on staff ({it} it)", a3, y3, time.time() - t, h3)
    np.savez(f"/tmp/secp_{SEED}_{N}.npz", S=S, O=O, v=v, RMAX=RMAX, a=a3, y=y3)
