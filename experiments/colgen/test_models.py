"""Exhaustive correctness tests and mathematical counterexamples, not score tests."""
import argparse
import importlib.util
from itertools import combinations
import json
from pathlib import Path
import random
import time

import numpy as np

from model import Instance, Master, cg_enumerated, reference_optimum

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('official_validator', ROOT/'task/validate_solution.py')
validator = importlib.util.module_from_spec(spec); spec.loader.exec_module(validator)


def assert_valid(data, solution, expected):
    r = validator.validate_solution(validator.Instance.model_validate(data),
                                   [validator.OpenedOffice.model_validate(s) for s in solution])
    assert not isinstance(r, str), r
    assert abs(r-expected) < 1e-5*max(1., abs(expected)), (r, expected)


def tiny(seed, n=7, m=3, mode='normal'):
    r = random.Random(seed)
    xy = [(r.random(), r.random()) for _ in range(n+m)]
    if mode == 'duplicates':
        xy = [(r.randrange(3)/2., r.randrange(3)/2.) for _ in xy]
    elif mode == 'collinear':
        xy = [(r.random(), 0.) for _ in xy]
    workers = [[0], [1], [2], [0, 1], [1, 2]] if mode == 'multiskill' else [[0], [0], [1], [1], [2]]
    if mode == 'missing':
        workers = [[0], [1]]
    sites = [dict(x=xy[i][0], y=xy[i][1], reward=r.uniform(2, 8),
                  tasks=[r.randrange(3) for _ in range(r.randrange(4))]) for i in range(n)]
    scale = 1e5 if mode == 'scale' else 3.
    for s in sites:
        if mode == 'scale':
            s['reward'] *= 1e5
    offices = [dict(x=xy[n+o][0], y=xy[n+o][1], cost=r.uniform(.1, 2.)*(1e5 if mode == 'scale' else 1.),
                    maxSize=0 if mode == 'zero_capacity' else r.randint(2, max(2, n))) for o in range(m)]
    distances = [[(1.5-np.linalg.norm(np.array(xy[n+o])-xy[i]) if mode == 'anti'
                   else np.linalg.norm(np.array(xy[n+o])-xy[i]))*scale for i in range(n)] for o in range(m)]
    return dict(sites=sites, offices=offices, workers=workers, distances=distances,
                maxDifference=0 if mode == 'A0' else n if mode == 'freeA' else 2,
                balanceCoefficient=0. if mode == 'alpha0' else 1e6 if mode == 'alpha_huge' else .7)


def witnesses():
    result = {}
    # Crossing segments share no input point: polygon disjointness is too strict.
    data = dict(sites=[dict(x=1., y=1., reward=10., tasks=[]), dict(x=1., y=-1., reward=10., tasks=[])],
                offices=[dict(x=-1., y=-1., cost=0., maxSize=1), dict(x=-1., y=1., cost=0., maxSize=1)],
                workers=[], distances=[[0., 20.], [20., 0.]], maxDifference=2, balanceCoefficient=0.)
    I = Instance(data); pool = [I.column(0, [0]), I.column(1, [1])]
    ip = Master(I).solve(pool, integer=True)
    assert abs(ip['value']-20.) < 1e-7
    assert_valid(data, ip['solution'], ip['value'])
    assert set(pool[0].footprint).isdisjoint(pool[1].footprint)
    result['crossing_segments'] = dict(ip=ip['value'], footprints=[c.footprint for c in pool])

    # Three pairwise conflicts, each at a different triangle vertex.
    data = dict(sites=[dict(x=0., y=0., reward=1., tasks=[]), dict(x=2., y=0., reward=1., tasks=[]),
                       dict(x=1., y=2., reward=1., tasks=[])],
                offices=[dict(x=1., y=0., cost=0., maxSize=2), dict(x=1.5, y=1., cost=0., maxSize=2),
                         dict(x=.5, y=1., cost=0., maxSize=2)],
                workers=[], distances=[[0.]*3 for _ in range(3)], maxDifference=3, balanceCoefficient=0.)
    I = Instance(data); pool = [I.column(o, ss) for o, ss in enumerate([(0,1),(1,2),(2,0)])]
    lp = Master(I).solve(pool); ip = Master(I).solve(pool, integer=True)
    cut = Master(I, cliques=[{c.key for c in pool}]).solve(pool)
    assert abs(lp['value']-3.) < 1e-7 and abs(ip['value']-2.) < 1e-7 and abs(cut['value']-2.) < 1e-7
    result['clique_no_common_point'] = dict(point_lp=lp['value'], clique_lp=cut['value'], ip=ip['value'])

    # Point cliques dominate pairwise edge rows for three zones at one point.
    data['offices'] = [dict(x=1., y=1., cost=0., maxSize=2) for _ in range(3)]
    I = Instance(data); pool = [I.column(o, [0]) for o in range(3)]
    lp = Master(I).solve(pool); pair = Master(I, geometry='pair').solve(pool)
    assert abs(lp['value']-1.) < 1e-7 and abs(pair['value']-1.5) < 1e-7
    result['point_clique_vs_edges'] = dict(point_lp=lp['value'], edge_lp=pair['value'])

    # One multiskill worker cannot serve two offices simultaneously.
    data = dict(sites=[dict(x=0., y=0., reward=10., tasks=[0]), dict(x=10., y=0., reward=10., tasks=[1])],
                offices=[dict(x=0., y=1., cost=0., maxSize=1), dict(x=10., y=1., cost=0., maxSize=1)],
                workers=[[0,1]], distances=[[0.,20.],[20.,0.]], maxDifference=2, balanceCoefficient=0.)
    I = Instance(data); pool = [I.column(0,[0]), I.column(1,[1])]
    worker = Master(I).solve(pool, integer=True)
    count = Master(I, skill_mode='counts').solve(pool, integer=True)
    assert abs(worker['value']-10.) < 1e-7 and abs(count['value']-20.) < 1e-7
    result['multiskill_count_error'] = dict(exact_workers=worker['value'], counts_only=count['value'])

    # Compact worker LP is weaker than convexifying feasible teams in columns.
    data = dict(sites=[dict(x=0.,y=0.,reward=1.,tasks=[0,1,2]),dict(x=10.,y=0.,reward=1.,tasks=[0,1,2])],
                offices=[dict(x=0.,y=1.,cost=0.,maxSize=1),dict(x=10.,y=1.,cost=0.,maxSize=1)],
                workers=[[0,1],[1,2],[0,2]],distances=[[0.,10.],[10.,0.]],
                maxDifference=2,balanceCoefficient=0.)
    I=Instance(data); pool=[I.column(0,[0]),I.column(1,[1])]
    weak=Master(I).solve(pool); ip=Master(I).solve(pool,integer=True)
    from pyscipopt import Model, quicksum
    team=Model('team columns'); team.hideOutput(); team.setIntParam('parallel/maxnthreads',1)
    teams=list(combinations(range(3),2))
    v={(o,t):team.addVar(vtype='C',lb=0.,obj=1.) for o in range(2) for t in range(3)}
    for o in range(2): team.addCons(quicksum(v[o,t] for t in range(3))<=1.)
    for w in range(3): team.addCons(quicksum(v[o,t] for o in range(2) for t in range(3) if w in teams[t])<=1.)
    team.setMaximize(); team.optimize(); strong=team.getObjVal()
    cut=Master(I,worker_cuts=True).solve(pool)
    assert abs(weak['value']-2.)<1e-7 and abs(strong-1.5)<1e-7 and abs(ip['value']-1.)<1e-7 and abs(cut['value']-1.5)<1e-7
    result['worker_lp_vs_team_columns']=dict(compact_worker_lp=weak['value'],team_column_lp=strong,
                                             cheap_cover_cut_lp=cut['value'],ip=ip['value'])

    # A covered site need not be served: island=served set is an invalid assumption.
    data = dict(sites=[dict(x=2., y=0., reward=10., tasks=[]), dict(x=1., y=0., reward=0., tasks=[99])],
                offices=[dict(x=0., y=0., cost=0., maxSize=1)], workers=[], distances=[[0.,0.]],
                maxDifference=0, balanceCoefficient=0.)
    I = Instance(data); c = I.column(0,[0]); ip = Master(I).solve([c], integer=True)
    assert 1 in c.footprint and 1 not in c.sites and abs(ip['value']-10.) < 1e-7
    assert_valid(data, ip['solution'], ip['value'])
    result['unserved_interior_missing_skill'] = dict(ip=ip['value'], footprint=c.footprint, served=c.sites)

    # Negative raw profit may be essential to equalize task loads. This also
    # exposes why pruning x[o,s] by reward-distance>0 is unsafe for an upper bound.
    data = dict(sites=[dict(x=-3.,y=0.,reward=100.,tasks=[0,0,0]),
                       dict(x=3.,y=0.,reward=30.,tasks=[0]),
                       dict(x=2.,y=1.,reward=1.,tasks=[0,0])],
                offices=[dict(x=-2.,y=0.,cost=0.,maxSize=1),dict(x=2.,y=0.,cost=0.,maxSize=2)],
                workers=[[0],[0]],distances=[[0.,1e6,1e6],[1e6,0.,6.]],
                maxDifference=1,balanceCoefficient=100.)
    I=Instance(data); cols=I.enumerate_columns()
    ip=Master(I).solve(cols,integer=True)
    pos=Master(I).solve([c for c in cols if all(I.profit[c.office,s]>0 for s in c.sites)],integer=True)
    assert abs(ip['value']-125.)<1e-6 and abs(pos['value']-100.)<1e-6
    assert_valid(data,ip['solution'],ip['value'])
    result['negative_profit_needed'] = dict(exact_ip=ip['value'],positive_profit_only_ip=pos['value'],
                                           loads=[3,3],site_profits=[100.,30.,-5.])

    empty=[]
    for n,m in ((0,1),(1,0),(0,0)):
        data=dict(sites=[dict(x=0.,y=0.,reward=1.,tasks=[])]*n,
                  offices=[dict(x=1.,y=0.,cost=0.,maxSize=1)]*m,workers=[],
                  distances=[[0.]*n for _ in range(m)],maxDifference=0,balanceCoefficient=1.)
        I=Instance(data); ip=Master(I).solve(I.enumerate_columns(),integer=True)
        assert ip['value']==0.; assert_valid(data,ip['solution'],0.)
        empty.append(dict(n=n,offices=m,value=ip['value']))
    result['empty_inputs']=empty
    return result


def run(out):
    start = time.perf_counter()
    rows = []
    modes = ['normal', 'multiskill', 'missing', 'A0', 'freeA', 'alpha0', 'alpha_huge',
             'zero_capacity', 'duplicates', 'collinear', 'scale', 'anti']
    for j, mode in enumerate(modes):
        data = tiny(12000+j, mode=mode)
        I = Instance(data); cols = I.enumerate_columns(); M = Master(I)
        t0 = time.perf_counter(); exact, nodes = reference_optimum(I, cols)
        refsec = time.perf_counter()-t0
        ip = M.solve(cols, integer=True, seconds=10.)
        assert abs(ip['value']-exact) < 1e-5*max(1., abs(exact)), (mode, ip['value'], exact, ip['status'])
        assert_valid(data, ip['solution'], ip['value'])
        lp = M.solve(cols)
        no_geo = Master(I, geometry='none').solve(cols)
        assert lp['value'] >= exact-1e-6*max(1.,abs(exact))
        assert no_geo['value'] >= lp['value']-1e-6*max(1.,abs(exact))
        cg = cg_enumerated(M, cols, seconds=15., batch=2)
        assert cg['converged'], mode
        assert abs(cg['result']['value']-lp['value']) < 1e-5*max(1.,abs(exact)), mode
        for entry in cg['trace']:
            assert entry['exact_certificate'] >= lp['value']-1e-6*max(1.,abs(exact))
            assert entry['cheap_certificate'] >= lp['value']-1e-6*max(1.,abs(exact))
        # Test the cheap certificate under arbitrary nonnegative dual prices too.
        rnd = np.random.default_rng(j)
        for _ in range(3):
            y = rnd.exponential(2., len(M.rows))
            for o in range(I.m):
                upper = M.relaxed_pricing_bound(o, y)
                assert all(M.rc(c, y) <= upper + 1e-6 for c in cols if c.office == o), mode
        restricted_ip = M.solve(cg['pool'], integer=True, seconds=5.)
        scip = M.solve(cols, integer=True, seconds=10., engine='scip')
        assert abs(scip['value']-exact) < 1e-5*max(1., abs(exact)), (mode, 'scip')
        row = dict(mode=mode, seed=12000+j, n=I.n, offices=I.m, columns=len(cols),
                   exact=exact, full_lp=lp['value'], no_geometry_lp=no_geo['value'],
                   cg_lp=cg['result']['value'], cg_columns=len(cg['pool']), cg_rounds=len(cg['trace']),
                   restricted_ip=restricted_ip['value'], highs_ip_seconds=ip['seconds'],
                   scip_ip_seconds=scip['seconds'], reference_seconds=refsec, reference_nodes=nodes,
                   cg_seconds=cg['seconds'], trace=cg['trace'])
        rows.append(row)
        print(json.dumps({k:v for k,v in row.items() if k != 'trace'}), flush=True)

    # Exhaust all task and count windows on a small general multiskill instance.
    data = tiny(13000, n=5, m=2, mode='multiskill'); I = Instance(data); cols = I.enumerate_columns()
    exact, _ = reference_optimum(I, cols)
    levels = sorted({c.load for c in cols}); best_ip = best_lp = 0.; window_count = 0
    t0 = time.perf_counter()
    for b in range(1, max(I.cap)+1):
        for i, lo in enumerate(levels):
            for hi in levels[i:]:
                M = Master(I, window=(b,lo,hi)); subset = [c for c in cols if M.accepts(c)]
                if not subset:
                    continue
                lp = M.solve(subset); ip = M.solve(subset, integer=True)
                best_lp, best_ip = max(best_lp, lp['value']), max(best_ip, ip['value'])
                window_count += 1
    assert abs(best_ip-exact) < 1e-6
    window = dict(seed=13000, n=I.n, offices=I.m, windows=window_count, exact=exact,
                  window_ip=best_ip, window_lp=best_lp, compact_lp=Master(I).solve(cols)['value'],
                  seconds=time.perf_counter()-t0)
    result = dict(tiny=rows, witnesses=witnesses(), window=window, total_seconds=time.perf_counter()-start)
    out.parent.mkdir(parents=True, exist_ok=True); out.write_text(json.dumps(result, indent=2))
    print(json.dumps(dict(window=window, witnesses=result['witnesses'], total_seconds=result['total_seconds'])), flush=True)


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--out', type=Path, default=Path(__file__).parent/'logs/correctness.json')
    run(ap.parse_args().out)
