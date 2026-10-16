"""
TechArena, кейс 3 — решатель (Python + numpy).

Читает instance.json, пишет solution.json в текущем каталоге.
Отладка: python3 solve.py [instance.json] [solution.json] [секунды]

Схема:
  внешний уровень  — локальный поиск по множеству открытых офисов (add/drop/swap);
  внутренний       — старт по диаграмме Вороного офисов (геометрически допустим
                     по построению) + локальный поиск по сайтам (добавить/
                     перенести/снять) с точной проверкой геометрии, ёмкостей,
                     баланса числа сайтов и навыков, и точной целевой функцией.

Геометрия как у валидатора: зона = выпуклая оболочка (сайты зоны + офис);
недопустимо, если какая-либо точка (любой сайт или офис) покрыта двумя оболочками.
Снятие сайта только сжимает оболочку, поэтому всегда допустимо.
"""
import json
import math
import os
import random
import sys
import time

import numpy as np

T0 = time.time()


# ------------------------------------------------------------------ геометрия
def hull_of(pts):
    """Монотонная цепь; возвращает вершины CCW без коллинеарных (1, 2 или >=3 точки)."""
    pts = sorted(set(map(tuple, pts)))
    if len(pts) <= 2:
        return pts

    def cr(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lo, up = [], []
    for p in pts:
        while len(lo) >= 2 and cr(lo[-2], lo[-1], p) <= 0:
            lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(up) >= 2 and cr(up[-2], up[-1], p) <= 0:
            up.pop()
        up.append(p)
    h = lo[:-1] + up[:-1]
    return h if len(h) >= 1 else pts[:1]


class Geo:
    def __init__(self, P):
        self.P = P  # (n_points, 2): сначала сайты, потом офисы
        ext = float(np.ptp(P, axis=0).max()) or 1.0
        self.eps_len = 1e-9 * ext
        self.eps_cr = 1e-9 * ext * ext

    def covers(self, h):
        """Маска точек, покрытых оболочкой h (с допуском в сторону «покрыто»)."""
        P, X, Y = self.P, self.P[:, 0], self.P[:, 1]
        if len(h) == 1:
            return np.hypot(X - h[0][0], Y - h[0][1]) <= self.eps_len
        if len(h) == 2:
            (ax, ay), (bx, by) = h
            dx, dy = bx - ax, by - ay
            L2 = dx * dx + dy * dy
            cr = dx * (Y - ay) - dy * (X - ax)
            dt = dx * (X - ax) + dy * (Y - ay)
            L = math.sqrt(L2)
            return (np.abs(cr) <= self.eps_cr + self.eps_len * L) & (dt >= -self.eps_len * L) & (dt <= L2 + self.eps_len * L)
        m = np.ones(len(P), bool)
        n = len(h)
        for i in range(n):
            ax, ay = h[i]
            bx, by = h[(i + 1) % n]
            m &= (bx - ax) * (Y - ay) - (by - ay) * (X - ax) >= -self.eps_cr - self.eps_len * math.hypot(bx - ax, by - ay)
        return m


# ----------------------------------------------------------------- инстанс
class Inst:
    def __init__(self, data):
        S, O = data["sites"], data["offices"]
        self.ns, self.no = len(S), len(O)
        self.reward = np.array([s["reward"] for s in S], float)
        self.tasks = [list(s["tasks"]) for s in S]
        self.ntask = np.array([len(t) for t in self.tasks], float)
        self.skillset = [frozenset(t) for t in self.tasks]
        self.cost = np.array([o["cost"] for o in O], float)
        self.maxsize = np.array([o["maxSize"] for o in O], int)
        self.workers = [frozenset(w) for w in data["workers"]]
        self.D = np.array(data["distances"], float)  # no x ns
        self.A = int(data["maxDifference"])
        self.alpha = float(data["balanceCoefficient"])
        P = np.array([[s["x"], s["y"]] for s in S] + [[o["x"], o["y"]] for o in O], float)
        self.geo = Geo(P)
        self.profit = self.reward[None, :] - self.D  # no x ns
        # навыки, которых нет ни у одного рабочего: такие сайты не обслужить
        allsk = set().union(*self.workers) if self.workers else set()
        self.servable = np.array([ss <= allsk for ss in self.skillset])


# ---------------------------------------------------------------- решение
class Sol:
    """Изменяемое состояние для фиксированного множества открытых офисов."""

    def __init__(self, I, opened):
        self.I = I
        self.opened = list(opened)
        self.isopen = np.zeros(I.no, bool)
        self.isopen[self.opened] = True
        self.asg = np.full(I.ns, -1, int)
        self.members = {o: set() for o in self.opened}
        self.size = np.zeros(I.no, int)
        self.load = np.zeros(I.no, float)
        self.need = {o: {} for o in self.opened}  # o -> skill -> число сайтов
        self.wof = [-1] * len(I.workers)  # рабочий -> офис
        npt = I.ns + I.no
        self.cov = np.zeros(npt, int)
        self.inhull = {}
        self.hull = {}
        for o in self.opened:
            self._set_hull(o, [tuple(I.geo.P[I.ns + o])])

    # --- геометрия
    def _set_hull(self, o, h):
        I = self.I
        if o in self.inhull:
            self.cov -= self.inhull[o]
        m = I.geo.covers(h)
        self.inhull[o] = m.astype(int)
        self.cov += self.inhull[o]
        self.hull[o] = h

    def _rebuild_hull(self, o):
        I = self.I
        pts = [tuple(I.geo.P[s]) for s in self.members[o]] + [tuple(I.geo.P[I.ns + o])]
        self._set_hull(o, hull_of(pts))

    def can_add_geo(self, s, o):
        """Возвращает (ok, новая оболочка или None если не меняется)."""
        if self.inhull[o][s]:
            return True, None
        I = self.I
        h = hull_of(list(self.hull[o]) + [tuple(I.geo.P[s])])
        m = I.geo.covers(h)
        newly = m & (self.inhull[o] == 0)
        if (self.cov[newly] > 0).any():
            return False, None
        return True, h

    # --- навыки
    def office_skills(self, o):
        sk = set()
        for w, oo in enumerate(self.wof):
            if oo == o:
                sk |= self.I.workers[w]
        return sk

    def plan_skills(self, s, o):
        """Список рабочих, которых нужно добавить в o для сайта s; None если нельзя."""
        need = set(self.I.skillset[s]) - self.office_skills(o)
        if not need:
            return []
        add = []
        for sk in sorted(need):
            if any(sk in self.I.workers[w] for w in add):
                continue
            best = None
            for w, oo in enumerate(self.wof):
                if oo == -1 and sk in self.I.workers[w] and w not in add:
                    if best is None or len(self.I.workers[w]) < len(self.I.workers[best]):
                        best = w
            if best is None:
                return None
            add.append(best)
        return add

    def release_workers(self, o):
        """Освободить рабочих офиса o, без которых покрытие навыков сохраняется."""
        needed = {k for k, c in self.need[o].items() if c > 0}
        ws = [w for w, oo in enumerate(self.wof) if oo == o]
        for w in sorted(ws, key=lambda w: len(self.I.workers[w])):
            rest = set()
            for w2 in ws:
                if w2 != w and self.wof[w2] == o:
                    rest |= self.I.workers[w2]
            if needed <= rest:
                self.wof[w] = -1

    # --- целевая
    def balance_pen(self, load=None, isopen=None):
        load = self.load if load is None else load
        L = load[self.opened]
        return self.I.alpha * (L.max() - L.min()) if len(L) else 0.0

    def objective(self):
        I = self.I
        a = self.asg >= 0
        prof = I.profit[self.asg[a], np.flatnonzero(a)].sum()
        return prof - I.cost[self.opened].sum() - self.balance_pen()

    def sizes_ok(self, size):
        S = size[self.opened]
        return S.max() - S.min() <= self.I.A and (size <= self.I.maxsize).all()

    # --- ходы
    def remove(self, s):
        o = self.asg[s]
        I = self.I
        self.asg[s] = -1
        self.members[o].discard(s)
        self.size[o] -= 1
        self.load[o] -= I.ntask[s]
        for k in I.skillset[s]:
            self.need[o][k] -= 1
        if tuple(I.geo.P[s]) in self.hull[o]:
            self._rebuild_hull(o)
        self.release_workers(o)

    def add(self, s, o, h, workers):
        I = self.I
        self.asg[s] = o
        self.members[o].add(s)
        self.size[o] += 1
        self.load[o] += I.ntask[s]
        for k in I.skillset[s]:
            self.need[o][k] = self.need[o].get(k, 0) + 1
        for w in workers:
            self.wof[w] = o
        if h is not None:
            self._set_hull(o, h)

    def delta_move(self, s, o_new):
        """Изменение цели при переводе s в o_new (-1 = снять). Без проверок допустимости."""
        I = self.I
        o_old = self.asg[s]
        d = 0.0
        load = self.load.copy()
        if o_old >= 0:
            d -= I.profit[o_old, s]
            load[o_old] -= I.ntask[s]
        if o_new >= 0:
            d += I.profit[o_new, s]
            load[o_new] += I.ntask[s]
        return d - (self.balance_pen(load) - self.balance_pen())

    def force_move(self, s, o_new):
        """Применяет ход, если он допустим (размеры, геометрия, навыки)."""
        o_old = self.asg[s]
        if o_new == o_old:
            return False
        size = self.size.copy()
        if o_old >= 0:
            size[o_old] -= 1
        if o_new >= 0:
            size[o_new] += 1
        if not self.sizes_ok(size):
            return False
        if o_new >= 0:
            # проверяем добавление до снятия: при переносе старая оболочка не мешает
            # только если сайт был в ней; для простоты снимаем и пробуем
            pass
        if o_old >= 0:
            self.remove(s)
        if o_new < 0:
            return True
        ok, h = self.can_add_geo(s, o_new)
        wk = self.plan_skills(s, o_new) if ok else None
        if not ok or wk is None:
            if o_old >= 0:
                ok2, h2 = self.can_add_geo(s, o_old)
                self.add(s, o_old, h2, self.plan_skills(s, o_old) or [])
            return False
        self.add(s, o_new, h, wk)
        return True

    def snapshot(self):
        return self.asg.copy(), list(self.wof)

    @classmethod
    def from_state(cls, I, opened, state):
        asg, wof = state
        sol = cls(I, opened)
        sol.asg = asg.copy()
        sol.wof = list(wof)
        for s in np.flatnonzero(asg >= 0):
            o = asg[s]
            sol.members[o].add(s)
            sol.size[o] += 1
            sol.load[o] += I.ntask[s]
            for k in I.skillset[s]:
                sol.need[o][k] = sol.need[o].get(k, 0) + 1
        for o in opened:
            sol._rebuild_hull(o)
        return sol

    def try_move(self, s, o_new, min_gain=1e-9):
        """Пробует ход; применяет, если допустим и улучшает цель на min_gain."""
        I = self.I
        o_old = self.asg[s]
        if o_new == o_old:
            return False
        size = self.size.copy()
        if o_old >= 0:
            size[o_old] -= 1
        if o_new >= 0:
            size[o_new] += 1
        if not self.sizes_ok(size):
            return False
        g = self.delta_move(s, o_new)
        if g < min_gain:
            return False
        if o_new < 0:
            self.remove(s)
            return True
        if o_old >= 0:
            self.remove(s)
        ok, h = self.can_add_geo(s, o_new)
        wk = self.plan_skills(s, o_new) if ok else None
        if not ok or wk is None:
            if o_old >= 0:  # откат
                ok2, h2 = self.can_add_geo(s, o_old)
                self.add(s, o_old, h2, self.plan_skills(s, o_old) or [])
            return False
        self.add(s, o_new, h, wk)
        return True


# ---------------------------------------------------------------- алгоритм
def construct(I, opened, rng):
    """Вороной по евклиду среди открытых офисов, затем добавление по выгоде."""
    sol = Sol(I, opened)
    P = I.geo.P
    OP = P[I.ns + np.array(opened)]
    d2 = ((P[:I.ns, None, :] - OP[None, :, :]) ** 2).sum(2)
    cell = np.array(opened)[d2.argmin(1)]
    order = np.argsort(-I.profit[cell, np.arange(I.ns)])
    for s in order:
        o = cell[s]
        if I.servable[s] and I.profit[o, s] > 0:
            sol.try_move(s, o, min_gain=-1e18 if I.alpha == 0 else -1e18)
    return sol


def repair_sizes(sol):
    """Снимает наименее выгодные сайты, пока не выполнены maxSize и баланс A."""
    I = sol.I
    while True:
        S = sol.size[sol.opened]
        over = [o for o in sol.opened if sol.size[o] > I.maxsize[o]]
        if not over and S.max() - S.min() <= I.A:
            return
        o = over[0] if over else sol.opened[int(S.argmax())]
        s = min(sol.members[o], key=lambda s: I.profit[o, s])
        sol.remove(s)


def local_search(sol, rng, t_end):
    I = sol.I
    near = np.argsort(I.D, axis=0)  # для каждого сайта офисы по расстоянию
    opened = set(sol.opened)
    improved = True
    while improved and time.time() < t_end:
        improved = False
        for s in rng.permutation(I.ns):
            if time.time() > t_end:
                break
            if not I.servable[s]:
                continue
            cands = [o for o in near[:, s] if o in opened][:4] + [-1]
            best = None
            for o in cands:
                if o == sol.asg[s]:
                    continue
                g = sol.delta_move(s, o)
                if g > 1e-9 and (best is None or g > best[0]):
                    best = (g, o)
            if best is not None:
                for o in sorted(cands, key=lambda o: -sol.delta_move(s, o) if o != sol.asg[s] else 1e18):
                    if o != sol.asg[s] and sol.try_move(s, o):
                        improved = True
                        break
    return sol


def balance_search(sol, rng, t_end):
    """Добивка баланса задач: снимаем сайты с задачами у самого загруженного офиса,
    если штраф падает сильнее, чем теряется выгода (и наоборот добавляем к наименее)."""
    I = sol.I
    if I.alpha <= 0:
        return sol
    changed = True
    while changed and time.time() < t_end:
        changed = False
        L = sol.load[sol.opened]
        omax = sol.opened[int(L.argmax())]
        for s in sorted(sol.members[omax], key=lambda s: I.profit[omax, s] / max(I.ntask[s], 1e-9)):
            if I.ntask[s] > 0 and sol.try_move(s, -1):
                changed = True
                break
    return sol


def sur_pen(I, load, opened, lam):
    L = load[opened]
    return I.alpha * (L.max() - L.min()) + lam * np.abs(L - L.mean()).sum()


def anneal(sol, rng, t_end, lam_frac=0.2):
    """Имитация отжига по ходам «сайт -> офис / снять» с суррогатом баланса."""
    I = sol.I
    opened = np.array(sol.opened)
    lam = I.alpha * lam_frac
    cand_s = np.flatnonzero(I.servable)
    if len(cand_s) == 0:
        return sol
    nearest = {s: [o for o in np.argsort(I.D[:, s]) if sol.isopen[o]][:5] for s in cand_s}
    prof_scale = np.abs(I.profit[opened][:, cand_s]).mean() + 1e-9
    T_hi, T_lo = 0.3 * prof_scale, 1e-4 * prof_scale
    best_f, best_state = sol.objective(), sol.snapshot()
    t_start = time.time()
    dur = max(1e-3, t_end - t_start)
    it = 0
    T = T_hi
    while True:
        it += 1
        if it % 64 == 0:
            now = time.time()
            if now >= t_end:
                break
            T = T_hi * (T_lo / T_hi) ** ((now - t_start) / dur)
        s = cand_s[rng.integers(len(cand_s))]
        near = nearest[s]
        o_old = sol.asg[s]
        o_new = -1 if (o_old >= 0 and rng.random() < 0.25) else near[rng.integers(len(near))]
        if o_new == o_old:
            continue
        load = sol.load.copy()
        d = 0.0
        if o_old >= 0:
            d -= I.profit[o_old, s]
            load[o_old] -= I.ntask[s]
        if o_new >= 0:
            d += I.profit[o_new, s]
            load[o_new] += I.ntask[s]
        d -= sur_pen(I, load, opened, lam) - sur_pen(I, sol.load, opened, lam)
        if d < 0 and rng.random() >= math.exp(d / T):
            continue
        if sol.force_move(s, o_new):
            f = sol.objective()
            if f > best_f + 1e-9:
                best_f, best_state = f, sol.snapshot()
    return Sol.from_state(I, sol.opened, best_state)


def solve_open(I, opened, rng, t_budget):
    t_end = time.time() + t_budget
    sol = construct(I, opened, rng)
    repair_sizes(sol)
    sol = anneal(sol, rng, time.time() + 0.85 * (t_end - time.time()))
    local_search(sol, rng, t_end)
    return sol.objective(), sol


# ------------------------------------------------ быстрая оценка через power diagram
class Fast:
    """Оценка множества офисов без явной геометрии: сайты делятся по power diagram
    (евклид, веса h), ячейки выпуклы и не пересекаются, значит оболочки зон тоже.
    Затем: выгодные и обслуживаемые по навыкам сайты, обрезка по maxSize и A,
    выбор уровня нагрузки под штраф баланса."""

    def __init__(self, I):
        self.I = I
        self.SP = I.geo.P[:I.ns]
        self.OP = I.geo.P[I.ns:]
        self.d2 = ((self.SP[:, None, :] - self.OP[None, :, :]) ** 2).sum(2)  # ns x no
        self.od2 = ((self.OP[:, None, :] - self.OP[None, :, :]) ** 2).sum(2)
        sk = sorted(set().union(*I.skillset) if I.ns else set())
        self.skills = sk
        self.req = np.array([[k in ss for k in sk] for ss in I.skillset], bool).reshape(I.ns, len(sk))
        self.wcnt = np.array([sum(k in w for w in I.workers) for k in sk], int)
        self.scale2 = float(np.median(self.d2.min(1))) + 1e-12

    def assign(self, opened, h, G=None):
        """Power diagram с генераторами G (по умолчанию — сами офисы) и весами h."""
        I = self.I
        op = np.array(opened)
        hh = h[op]
        if G is None:
            sc = self.od2[np.ix_(op, op)] - hh[None, :]
            ps = self.d2[:, op] - hh[None, :]
        else:
            g = G[op]
            sc = ((self.OP[op][:, None, :] - g[None, :, :]) ** 2).sum(2) - hh[None, :]
            ps = ((self.SP[:, None, :] - g[None, :, :]) ** 2).sum(2) - hh[None, :]
        # офис обязан лежать в своей ячейке
        if (sc.argmin(1) != np.arange(len(op))).any():
            return None
        c = op[ps.argmin(1)]
        prof = I.profit[c, np.arange(I.ns)]
        ok = (prof > 0) & I.servable
        # навыки: для дефицитных навыков разрешаем только лучшие офисы
        allow = np.ones((I.no, len(self.skills)), bool)
        for j in range(len(self.skills)):
            if self.wcnt[j] >= len(op):
                continue
            val = np.array([prof[ok & (c == o) & self.req[:, j]].sum() for o in op])
            keep = set(op[np.argsort(-val)[:self.wcnt[j]]].tolist())
            for o in op:
                if o not in keep:
                    allow[o, j] = False
        bad = (self.req & ~allow[c]).any(1)
        ok &= ~bad
        return c, prof, ok

    def evaluate(self, opened, h, want_asg=False, G=None):
        I = self.I
        r = self.assign(opened, h, G)
        if r is None:
            return -1e300, None
        c, prof, ok = r
        op = list(opened)
        members = {}
        for o in op:
            idx = np.flatnonzero(ok & (c == o))
            idx = idx[np.argsort(-prof[idx])][: I.maxsize[o]]
            members[o] = idx
        # баланс числа сайтов A: обрезаем крупные до min+A
        smin = min(len(members[o]) for o in op)
        for o in op:
            members[o] = members[o][: smin + I.A]
        base_cost = I.cost[op].sum()
        if I.alpha <= 0:
            total = sum(prof[members[o]].sum() for o in op) - base_cost
            return total, (members if want_asg else None)
        # уровень нагрузки t: в каждом офисе снимаем самые «дешёвые за задачу» сайты
        rem = {}
        for o in op:
            m = members[o]
            m = m[I.ntask[m] > 0]
            order = np.argsort(prof[m] / I.ntask[m])
            m = m[order]
            rem[o] = (m, np.cumsum(I.ntask[m]), np.cumsum(prof[m]))
        L = {o: I.ntask[members[o]].sum() for o in op}
        P0 = sum(prof[members[o]].sum() for o in op)
        lo, hi = min(L.values()), max(L.values())
        levels = np.unique(np.concatenate([[hi], np.linspace(lo, hi, 40), list(L.values())]))
        best = (-1e300, None)
        for t in levels:
            cost = 0.0
            newL = []
            cut = {}
            sizes = []
            for o in op:
                ex = L[o] - t
                m, ct, cp = rem[o]
                if ex <= 0 or len(m) == 0:
                    newL.append(L[o]); cut[o] = 0; sizes.append(len(members[o]))
                    continue
                k = int(np.searchsorted(ct, ex - 1e-9)) + 1
                k = min(k, len(m))
                cost += cp[k - 1]
                newL.append(L[o] - ct[k - 1]); cut[o] = k; sizes.append(len(members[o]) - k)
            if max(sizes) - min(sizes) > I.A:
                continue
            f = P0 - cost - base_cost - I.alpha * (max(newL) - min(newL))
            if f > best[0]:
                best = (f, cut)
        f, cut = best
        if not want_asg or cut is None:
            return f, None
        out = {}
        for o in op:
            m, _, _ = rem[o]
            drop = set(m[: cut[o]].tolist())
            out[o] = np.array([s for s in members[o] if s not in drop], int)
        return f, out

    def search_h(self, opened, iters=150, h0=None, deadline=None, G0=None):
        """Координатный поиск по весам h и положениям генераторов G (power diagram)."""
        I = self.I
        h = np.zeros(I.no) if h0 is None else h0.copy()
        G = self.OP.copy() if G0 is None else G0.copy()
        best, _ = self.evaluate(opened, h, G=G)
        ext = float(np.ptp(I.geo.P, axis=0).max()) or 1.0
        step = {}
        for o in opened:
            step[o, 0] = 0.5 * self.scale2
            step[o, 1] = step[o, 2] = 0.05 * ext
        keys = list(step)
        for it in range(iters):
            if deadline is not None and time.time() > deadline:
                break
            improved = False
            for (o, p) in keys:
                for sg in (1.0, -1.0):
                    d = sg * step[o, p]
                    if p == 0:
                        h[o] += d
                    else:
                        G[o, p - 1] += d
                    f, _ = self.evaluate(opened, h, G=G)
                    if f > best + 1e-9:
                        best, improved = f, True
                        step[o, p] *= 1.6
                        break
                    if p == 0:
                        h[o] -= d
                    else:
                        G[o, p - 1] -= d
                else:
                    step[o, p] *= 0.5
            if not improved and all(step[k] < 1e-6 * (self.scale2 if k[1] == 0 else ext) for k in keys):
                break
        return best, (h, G)

def build_sol(I, opened, members):
    """Переносит назначение в Sol с точными проверками (недопустимые сайты пропускаются)."""
    sol = Sol(I, opened)
    order = sorted(((s, o) for o in opened for s in members[o]), key=lambda x: -I.profit[x[1], x[0]])
    for s, o in order:
        size = sol.size.copy()
        size[o] += 1
        if (size <= I.maxsize).all():
            ok, h = sol.can_add_geo(s, o)
            wk = sol.plan_skills(s, o) if ok else None
            if ok and wk is not None:
                sol.add(s, o, h, wk)
    repair_sizes(sol)
    return sol


def drop_empty(sol):
    return [o for o in sol.opened if sol.size[o] > 0]


def to_json(sol):
    out = []
    for o in sol.opened:
        if sol.size[o] == 0:
            continue
        out.append({"officeId": int(o),
                    "sites": sorted(int(s) for s in sol.members[o]),
                    "workers": sorted(w for w, oo in enumerate(sol.wof) if oo == o)})
    return out


def main():
    inp = sys.argv[1] if len(sys.argv) > 1 else "instance.json"
    outp = sys.argv[2] if len(sys.argv) > 2 else "solution.json"
    limit = float(sys.argv[3]) if len(sys.argv) > 3 else float(os.environ.get("TL", 270))
    with open(inp, encoding="utf-8-sig") as f:
        I = Inst(json.load(f))
    rng = np.random.default_rng(12345)
    t_end = T0 + limit
    best = [0.0, None]  # пустое решение даёт 0

    def write(sol):
        with open(outp, "w", encoding="utf-8") as f:
            json.dump(to_json(sol) if sol is not None else [], f)

    def offer(sol):
        f = sol.objective()
        if f > best[0] + 1e-9:
            best[0], best[1] = f, sol
            write(sol)

    write(None)
    if I.ns == 0 or I.no == 0:
        return
    F = Fast(I)
    cache = {}
    t_outer = T0 + 0.45 * limit

    def ev(opened, iters=60):
        key = tuple(sorted(opened))
        if not key:
            return 0.0
        if key not in cache:
            cache[key] = F.search_h(list(key), iters=iters, deadline=t_outer)
        return cache[key][0]

    # 1) жадное добавление офисов по быстрой оценке
    cur, cur_f = [], 0.0
    while time.time() < t_outer:
        cand = [(ev(cur + [o]), o) for o in range(I.no) if o not in cur and time.time() < t_outer]
        if not cand:
            break
        f, o = max(cand)
        if f <= cur_f + 1e-9:
            break
        cur, cur_f = cur + [o], f
    # 2) локальный поиск add / drop / swap
    improved = True
    while improved and time.time() < t_outer:
        improved = False
        moves = [[x for x in cur if x != o] for o in cur] + [cur + [n] for n in range(I.no) if n not in cur]
        moves += [[x for x in cur if x != o] + [n] for o in cur for n in range(I.no) if n not in cur]
        rng.shuffle(moves)
        for m in moves:
            if time.time() > t_outer:
                break
            f = ev(m)
            if f > cur_f + 1e-9:
                cur, cur_f, improved = m, f, True
                break
    # 3) лучшие множества: перенос в точную модель и отжиг
    top = sorted(cache.items(), key=lambda kv: -kv[1][0])[:3]
    if cur:
        top = [(tuple(sorted(cur)), cache[tuple(sorted(cur))])] + [t for t in top if t[0] != tuple(sorted(cur))][:2]
    for idx, (key, (f, h)) in enumerate(top):
        left = t_end - time.time()
        if left <= 0.5:
            break
        share = left * (0.6 if idx == 0 else 0.5)
        opened = list(key)
        f2, (h2, G2) = F.search_h(opened, iters=300, h0=h[0], G0=h[1], deadline=time.time() + 0.3 * share)
        _, members = F.evaluate(opened, h2, want_asg=True, G=G2)
        if members is None:
            continue
        sol = build_sol(I, opened, members)
        offer(sol)
        sol = anneal(sol, rng, time.time() + 0.85 * share)
        local_search(sol, rng, time.time() + 0.15 * share)
        offer(sol)
    print(f"objective={best[0]:.3f} opened={drop_empty(best[1]) if best[1] else []} "
          f"fast_best={cur_f:.3f} evals={len(cache)} t={time.time()-T0:.1f}s", file=sys.stderr)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # лучшее решение уже записано; не падаем с RE
        print(f"error: {e!r}", file=sys.stderr)
    sys.exit(0)
