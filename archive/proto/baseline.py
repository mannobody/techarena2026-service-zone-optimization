"""
Кейс 3 — прототип-бейзлайн на синтетических данных (условия кейса пока неизвестны).

Допущения модели:
  * объекты и офисы стоят в вершинах дорожного графа (координаты x,y известны);
  * у объекта есть нагрузка w_i (трудозатраты), у задачи — общий штат S;
  * стоимость = sum_i w_i * d_road(office(i), i)  (взвешенный путь по дорогам);
  * баланс: нагрузка на одного сотрудника в каждой зоне в пределах (1 +- EPS) от средней;
  * выпуклость/непересечение = выпуклые оболочки зон попарно не пересекаются;
  * связность = индуцированный дорожный подграф зоны связен.

Сравниваются:
  A) MIP по дорожным расстояниям с ограничениями баланса (без геометрии);
  B) "power diagram": MIP с квадратом евклидова расстояния -> зоны почти всегда
     разделимы прямыми (выпуклые и непересекающиеся по построению LP-двойственности);
  C) B + локальный поиск: перенос граничных объектов, улучшающий дорожную стоимость,
     только если сохраняются баланс, непересечение оболочек и связность.
"""
import math
import random
import sys
import time

import networkx as nx
import numpy as np
from ortools.linear_solver import pywraplp
from shapely.geometry import MultiPoint

SEED = int(sys.argv[1]) if len(sys.argv) > 1 else 1
N_OBJ, K, STAFF, EPS = 400, 8, 40, 0.10
rng = random.Random(SEED)
np.random.seed(SEED)


# ---------------------------------------------------------------- инстанс
def make_instance():
    # Возмущённая решётка 30x30 + "река" по x≈0.5 с тремя мостами: дорожное
    # расстояние заметно отличается от евклидова, как в реальных данных.
    n = 30
    G = nx.Graph()
    pos = {}
    for i in range(n):
        for j in range(n):
            v = i * n + j
            pos[v] = (i / (n - 1) + rng.uniform(-0.01, 0.01), j / (n - 1) + rng.uniform(-0.01, 0.01))
            G.add_node(v)
    bridges = {4, 15, 26}
    for i in range(n):
        for j in range(n):
            v = i * n + j
            for di, dj in ((1, 0), (0, 1)):
                a, b = i + di, j + dj
                if a >= n or b >= n:
                    continue
                if di == 1 and i == n // 2 - 1 and j not in bridges:
                    continue  # река
                if rng.random() < 0.08:
                    continue  # случайно выкинутые дороги
                u = a * n + b
                G.add_edge(v, u, weight=math.dist(pos[v], pos[u]) * rng.uniform(1.0, 1.4))
    G = G.subgraph(max(nx.connected_components(G), key=len)).copy()
    nodes = list(G.nodes)
    objs = rng.sample(nodes, N_OBJ)
    rest = [v for v in nodes if v not in set(objs)]
    offices = rng.sample(rest, K)
    w = {o: rng.choice([1, 1, 2, 2, 3, 5]) for o in objs}
    return G, pos, objs, offices, w


G, pos, objs, offices, w = make_instance()
t0 = time.time()
dist = {k: nx.single_source_dijkstra_path_length(G, k, weight="weight") for k in offices}
W = sum(w.values())


# ---------------------------------------------------- распределение штата
def staff_split():
    # Нагрузка «по ближайшему офису» -> штат пропорционально (метод наибольших остатков).
    load = {k: 0 for k in offices}
    for o in objs:
        load[min(offices, key=lambda k: dist[k][o])] += w[o]
    quota = {k: STAFF * load[k] / W for k in offices}
    s = {k: max(1, int(quota[k])) for k in offices}
    for k in sorted(offices, key=lambda k: quota[k] - int(quota[k]), reverse=True):
        if sum(s.values()) >= STAFF:
            break
        s[k] += 1
    return s


staff = staff_split()
per_worker = W / STAFF
cap_lo = {k: staff[k] * per_worker * (1 - EPS) for k in offices}
cap_hi = {k: staff[k] * per_worker * (1 + EPS) for k in offices}


# -------------------------------------------------------- MIP назначения
def solve_assignment(cost, time_limit=30):
    s = pywraplp.Solver.CreateSolver("SCIP")
    s.SetTimeLimit(time_limit * 1000)
    x = {(o, k): s.BoolVar("") for o in objs for k in offices}
    for o in objs:
        s.Add(sum(x[o, k] for k in offices) == 1)
    for k in offices:
        load = sum(w[o] * x[o, k] for o in objs)
        s.Add(load >= cap_lo[k])
        s.Add(load <= cap_hi[k])
    s.Minimize(sum(w[o] * cost(o, k) * x[o, k] for o in objs for k in offices))
    st = s.Solve()
    assert st in (pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE), st
    return {o: next(k for k in offices if x[o, k].solution_value() > 0.5) for o in objs}


def road_cost(o, k):
    return dist[k][o]


def sq_euclid(o, k):
    return math.dist(pos[o], pos[k]) ** 2


# ------------------------------------------------------------- метрики
def zone_members(a):
    z = {k: [k] for k in offices}  # офис входит в свою зону
    for o, k in a.items():
        z[k].append(o)
    return z


def hulls(a):
    return {k: MultiPoint([pos[v] for v in m]).convex_hull for k, m in zone_members(a).items()}


def overlaps(H):
    ks = list(H)
    return sum(1 for i in range(len(ks)) for j in range(i + 1, len(ks))
               if H[ks[i]].intersection(H[ks[j]]).area > 1e-12)


def disconnected(a):
    # Связность через кратчайшие пути офис->объект: зона связна, если путь
    # проходит только через вершины, не принадлежащие чужим объектам.
    bad = 0
    for k, m in zone_members(a).items():
        sub = G.subgraph(set(m) | {v for v in G if v not in a}).copy()  # «нейтральные» вершины допустимы
        comp = nx.node_connected_component(sub, k)
        bad += sum(1 for v in m if v not in comp)
    return bad


def total_cost(a):
    return sum(w[o] * dist[k][o] for o, k in a.items())


def imbalance(a):
    load = {k: 0 for k in offices}
    for o, k in a.items():
        load[k] += w[o]
    return max(abs(load[k] / staff[k] / per_worker - 1) for k in offices)


def report(name, a, t):
    H = hulls(a)
    print(f"{name:34s} cost={total_cost(a):8.2f}  overlaps={overlaps(H):2d}  "
          f"disconnected_objs={disconnected(a):3d}  max_imb={imbalance(a):.3f}  t={t:.1f}s")


# ------------------------------------------------- локальный поиск (C)
def local_search(a, iters=20000):
    a = dict(a)
    load = {k: 0 for k in offices}
    for o, k in a.items():
        load[k] += w[o]
    H = hulls(a)
    improved = True
    rounds = 0
    while improved and rounds < 30:
        improved = False
        rounds += 1
        # кандидаты: объекты, для которых другой офис дешевле по дорогам
        cand = sorted(objs, key=lambda o: min(dist[k][o] for k in offices) - dist[a[o]][o])
        for o in cand:
            src = a[o]
            for dst in sorted(offices, key=lambda k: dist[k][o]):
                if dist[dst][o] >= dist[src][o]:
                    break
                if load[src] - w[o] < cap_lo[src] or load[dst] + w[o] > cap_hi[dst]:
                    continue
                a[o] = dst
                m = zone_members(a)
                hs = MultiPoint([pos[v] for v in m[src]]).convex_hull
                hd = MultiPoint([pos[v] for v in m[dst]]).convex_hull
                ok = all(hd.intersection(H[k]).area <= 1e-12 for k in offices if k not in (src, dst)) \
                    and hd.intersection(hs).area <= 1e-12
                if ok:
                    H[src], H[dst] = hs, hd
                    load[src] -= w[o]
                    load[dst] += w[o]
                    improved = True
                    break
                a[o] = src
    return a


print(f"seed={SEED} objs={N_OBJ} offices={K} staff={staff} graph=|V|{G.number_of_nodes()} |E|{G.number_of_edges()}")
t = time.time(); A = solve_assignment(road_cost); report("A) MIP road-dist (no geometry)", A, time.time() - t)
t = time.time(); B = solve_assignment(sq_euclid); report("B) MIP sq-euclid (power diagram)", B, time.time() - t)
t = time.time(); C = local_search(B); report("C) B + local search (keep hulls)", C, time.time() - t)

