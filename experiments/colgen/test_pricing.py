import argparse
import json
from pathlib import Path
import time

import numpy as np

from model import Instance, Master
from pricing import price_scip, cg_scip
from test_models import tiny


def run(out):
    start = time.perf_counter(); cases = []
    for j, mode in enumerate(['normal','multiskill','A0','duplicates','collinear','missing','anti']):
        I = Instance(tiny(14000+j, mode=mode)); universe = I.enumerate_columns(); M = Master(I)
        init = [c for c in universe if len(c.sites) == 1]
        lp = M.solve(universe)
        initial = M.solve(init)
        y = initial['dual']
        samples = []
        for o in range(I.m):
            truth = max((M.rc(c,y) for c in universe if c.office == o), default=-np.inf)
            priced = price_scip(M, o, y, seconds=1.)
            assert priced['bound'] >= truth-1e-5, (mode,o,truth,priced)
            if priced['exact']:
                assert abs(priced['rc']-truth) < 1e-5, (mode,o,truth,priced)
            samples.append({k:v for k,v in priced.items() if k not in ('column','columns')} | dict(office=o, enumerated_rc=truth))
        # Point-penalty-heavy arbitrary prices exercise interior footprint cuts.
        rng = np.random.default_rng(j)
        y = rng.uniform(0.,1.,len(M.rows))
        for p in M.point:
            y[p] = rng.uniform(.5,4.)
        for o in range(I.m):
            truth = max((M.rc(c,y) for c in universe if c.office == o), default=-np.inf)
            priced = price_scip(M,o,y,seconds=1.)
            assert priced['bound'] >= truth-1e-5, (mode,'arbitrary',o,truth,priced)
            if priced['exact']:
                assert abs(priced['rc']-truth) < 1e-5, (mode,'arbitrary',o,truth,priced)
            samples.append({k:v for k,v in priced.items() if k not in ('column','columns')} | dict(office=o, enumerated_rc=truth, arbitrary=True))
        cg = cg_scip(M, init, seconds=12., price_seconds=.5)
        for r in cg['trace']:
            assert r['certificate'] >= lp['value']-1e-5, (mode, r, lp['value'])
        if cg['converged']:
            assert abs(cg['result']['value']-lp['value']) < 1e-5
        row = dict(mode=mode, seed=14000+j, n=I.n, columns=len(universe), full_lp=lp['value'],
                   cg_lp=cg['result']['value'], cg_columns=len(cg['pool']), cg_converged=cg['converged'],
                   cg_seconds=cg['seconds'], samples=samples, trace=cg['trace'])
        print(json.dumps({k:v for k,v in row.items() if k not in ('samples','trace')}), flush=True)
        cases.append(row)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(dict(cases=cases, seconds=time.perf_counter()-start),indent=2))


if __name__ == '__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--out', type=Path, default=Path(__file__).parent/'logs/pricing_correctness.json')
    run(ap.parse_args().out)
