"""Bounds comparable on the SAME domain of allowed open offices.

The old bound's fixed-U Lagrangian dual is solved here as one LP, avoiding
subgradient stopping noise. Maximizing it over all U is only for tiny instances.
"""
from itertools import combinations
import json
from pathlib import Path
import time

import highspy
import numpy as np
from scipy.sparse import coo_matrix

from model import Instance, Master
from test_models import tiny


def fixed_office_lagrange(I, offices):
    ss=[s for s in range(I.n) if I.servable[s]]
    K, N=len(offices),len(ss)
    H,L=K*N,K*N+1
    obj=[I.profit[o,s] for o in offices for s in ss]+[-I.alpha,I.alpha]
    rr=[]; cc=[]; vv=[]; rhs=[]
    def row(d,b):
        r=len(rhs); rhs.append(float(b))
        for j,v in d.items():
            if v:
                rr.append(r); cc.append(j); vv.append(float(v))
    for i,s in enumerate(ss):
        row({b*N+i:1. for b in range(K)},1.)
    for b,o in enumerate(offices):
        row({b*N+i:1. for i in range(N)},I.cap[o])
        row({**{b*N+i:int(I.tasks[s]) for i,s in enumerate(ss)},H:-1.},0.)
        row({**{b*N+i:-int(I.tasks[s]) for i,s in enumerate(ss)},L:1.},0.)
    row({L:1.,H:-1.},0.)
    A=coo_matrix((vv,(rr,cc)),shape=(len(rhs),len(obj))).tocsc()
    h=highspy.Highs(); h.setOptionValue('output_flag',False); h.setOptionValue('threads',1)
    lp=highspy.HighsLp(); lp.num_col_,lp.num_row_=A.shape[1],A.shape[0]
    lp.col_cost_=-np.asarray(obj); lp.col_lower_=np.zeros(len(obj)); lp.col_upper_=np.full(len(obj),highspy.kHighsInf)
    lp.row_lower_=np.full(len(rhs),-highspy.kHighsInf); lp.row_upper_=np.array(rhs)
    lp.a_matrix_.format_=highspy.MatrixFormat.kColwise
    lp.a_matrix_.start_,lp.a_matrix_.index_,lp.a_matrix_.value_=A.indptr,A.indices,A.data
    h.passModel(lp); h.run()
    assert h.getModelStatus()==highspy.HighsModelStatus.kOptimal
    return -h.getObjectiveValue()-float(I.cost[list(offices)].sum())


def run():
    rows=[]
    for j,mode in enumerate(['normal','multiskill','missing','A0','freeA','alpha0','alpha_huge',
                             'zero_capacity','duplicates','collinear','scale','anti']):
        I=Instance(tiny(12000+j,mode=mode)); cols=I.enumerate_columns()
        t0=time.perf_counter()
        old=max([0.]+[fixed_office_lagrange(I,U) for k in range(1,I.m+1) for U in combinations(range(I.m),k)])
        dw=Master(I).solve(cols)['value']
        r=dict(mode=mode,seed=12000+j,old_global_lagrange=old,geometry_dw_lp=dw,
               tightening_pct=100*(1-dw/old) if old>0 else 0.,seconds=time.perf_counter()-t0)
        # Both are valid upper bounds; their formulations need not dominate each
        # other in general because the compact DW master has conditional big-M.
        rows.append(r); print(json.dumps(r),flush=True)
    windows=[]
    for seed,mode in [(12003,'A0'),(12006,'alpha_huge')]:
        I=Instance(tiny(seed,mode=mode)); cols=I.enumerate_columns()
        levels=sorted({c.load for c in cols}); best=0.; count=0; t0=time.perf_counter()
        for b in range(1,max(I.cap)+1):
            for i,lo in enumerate(levels):
                for hi in levels[i:]:
                    M=Master(I,window=(b,lo,hi)); subset=[c for c in cols if M.accepts(c)]
                    if subset:
                        best=max(best,M.solve(subset)['value']); count+=1
        row=dict(mode=mode,seed=seed,n=I.n,offices=I.m,windows=count,
                 global_window_lp=best,compact_lp=Master(I).solve(cols)['value'],
                 exact_ip=Master(I).solve(cols,integer=True)['value'],seconds=time.perf_counter()-t0)
        windows.append(row); print(json.dumps(row),flush=True)
    (Path(__file__).parent/'logs/bounds.json').write_text(json.dumps(dict(bounds=rows,windows=windows),indent=2))


if __name__=='__main__':
    run()
