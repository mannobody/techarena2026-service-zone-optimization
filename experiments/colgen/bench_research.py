"""Offline reproducible research: geometry-aware pool recombination and LP bounds.

Uses only synthetic inputs, never selects parameters by an open-instance ID.
All generated files stay inside this experiment directory. No contest submission.
"""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time

import highspy
import numpy as np

from model import Instance, Master, dedup
from pricing import cg_scip
from test_models import assert_valid, tiny, validator

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from public_metadata import public_json
def report_json(value, **kwargs):
    return public_json(value, ROOT, **kwargs)
spec = importlib.util.spec_from_file_location('data_generator', ROOT/'tools/gen.py')
gen = importlib.util.module_from_spec(spec); spec.loader.exec_module(gen)

CASES = {
    'euclid80': dict(ns=80,no=5,nw=12,nsk=3),
    'road150': dict(ns=150,no=6,nw=12,nsk=4,dist='road'),
    'anti100': dict(ns=100,no=6,nw=12,nsk=3,dist='anti'),
    'tightA120': dict(ns=120,no=6,nw=12,nsk=4,A=0),
    'multiskill100': dict(ns=100,no=7,nw=6,nsk=5,wsk=3,af=.05),
    'missing120': dict(ns=120,no=6,nw=10,nsk=5,wsk=2,deficit=2),
    'alpha0_200': dict(ns=200,no=8,nw=16,nsk=4,af=0.,A=200),
    'alphaHuge100': dict(ns=100,no=6,nw=12,nsk=3,af=1e5),
    'grid100': dict(ns=100,no=6,nw=12,nsk=3,layout='grid',offices='onsite'),
    'scale200': dict(ns=200,no=8,nw=16,nsk=4,span=1.,dscale=1e5),
    'large2000': dict(ns=2000,no=20,nw=40,nsk=5,dist='road'),
    'huge10000': dict(ns=10000,no=24,nw=48,nsk=5,dist='road'),
}


def prepare():
    for name in ('data','logs','artifacts'):
        (HERE/name).mkdir(exist_ok=True)
    for j, (name, cfg) in enumerate(CASES.items()):
        p = HERE/'data'/f'{name}.json'
        if not p.exists():
            gen.gen2(21000+j, str(p), **cfg)
    p = HERE/'data'/'zero_capacity.json'
    if not p.exists():
        p.write_text(report_json(tiny(21999, mode='zero_capacity')))
    exe = HERE/'artifacts'/'baseline'
    if not exe.exists():
        subprocess.run(['g++','-O2','-std=c++17',str(ROOT/'solver/solve.cpp'),'-o',str(exe)],check=True)
    collector = HERE/'artifacts'/'collector'
    if not collector.exists():
        subprocess.run(['g++','-O2','-std=c++17',str(HERE/'collect.cpp'),'-o',str(collector)],check=True)
    return exe


def baseline(exe, path, prefix, seconds, seed):
    out = HERE/'logs'/f'{prefix}.solution.json'
    start = time.perf_counter()
    p = subprocess.run([str(exe),str(path),str(out),str(seconds)],
                       env=dict(os.environ,NT='1',SEED=str(seed)),capture_output=True,text=True,
                       timeout=max(30.,seconds+20.))
    wall = time.perf_counter()-start
    (HERE/'logs'/f'{prefix}.stderr.txt').write_text(p.stderr)
    if p.returncode:
        raise RuntimeError((prefix,p.returncode,p.stderr[-1000:]))
    solution = json.loads(out.read_text())
    value = validator.validate_solution(validator.Instance.load(path),
                                       [validator.OpenedOffice.model_validate(s) for s in solution])
    if isinstance(value,str):
        raise AssertionError((prefix,value))
    pool=json.loads(p.stdout) if p.stdout.strip() else solution
    if p.stdout.strip():
        (HERE/'logs'/f'{prefix}.pool.json').write_text(p.stdout)
    return dict(value=float(value),wall=wall,limit=seconds,seed=seed,path=str(out),solution=solution,pool=pool)


def enrich(I, pool, deadline):
    """Shrunken zones preserve geometry and skills; new columns recompute footprint.

    Counts present elsewhere in the pool are included to let A=0 combinations
    meet exactly. Every parameter depends on data size/scale, not an instance ID.
    """
    result = list(pool)
    sizes = sorted({len(c.sites) for c in pool})
    for c in pool:
        if time.perf_counter() >= deadline:
            break
        n = len(c.sites)
        keep_sizes = {max(1,n-1), max(1,int(.95*n)),max(1,int(.85*n)),max(1,int(.7*n))}
        keep_sizes.update(k for k in sizes if k<n)
        orders = [sorted(c.sites,key=lambda s:I.profit[c.office,s],reverse=True),
                  sorted(c.sites,key=lambda s:(I.profit[c.office,s]/max(1,int(I.tasks[s]))),reverse=True)]
        for order in orders:
            for k in sorted(keep_sizes,reverse=True):
                if time.perf_counter() >= deadline:
                    return dedup(result)
                result.append(I.column(c.office,order[:k]))
    return dedup(result)


def dual_mutate(I, M, pool, dual, deadline):
    """Heuristic pricing: hull vertices and expensive assigned sites are deletions.

    No claim of exact pricing or full-LP upper bound. The cheap corrected dual
    bound is recorded separately. The control uses zero dual prices.
    """
    out=[]; evaluations=0
    ranked=sorted(pool,key=lambda c:M.rc(c,dual),reverse=True)
    for initial in ranked:
        if time.perf_counter() >= deadline:
            break
        c=initial
        for _ in range(3):
            if len(c.sites)<=1 or time.perf_counter()>=deadline:
                break
            _, weights, _, _ = M.pricing_parts(c.office,dual)
            order=sorted(c.sites,key=lambda s:weights[s])
            # A bounded data-derived candidate count keeps the experiment scalable.
            trials=order[:min(len(order),max(4,int(np.sqrt(len(order)))))]
            base=M.rc(c,dual); best=c; bestv=base
            for x in trials:
                if time.perf_counter()>=deadline:
                    break
                d=I.column(c.office,[s for s in c.sites if s!=x]); evaluations+=1
                v=M.rc(d,dual)
                if v>bestv+1e-8:
                    best,bestv=d,v
                if v>1e-7:
                    out.append(d)
            if best is c:
                break
            c=best
    return dedup(out),evaluations


def pool_bench(args):
    exe=prepare()
    selected=args.only.split(',') if args.only else list(CASES)
    rows=[]
    for name in selected:
        path=HERE/'data'/f'{name}.json'; I=Instance.read(path)
        for repeat in range(args.repeats):
            tag=args.out.stem
            short_exe=HERE/'artifacts'/'collector' if args.collect else exe
            shorts=[baseline(short_exe,path,f'{tag}_{name}_r{repeat}_seed{s}',args.short,s+100*repeat)
                    for s in range(1,args.starts+1)]
            incumbent=max(shorts,key=lambda r:r['value'])
            t0=time.perf_counter()
            raw=dedup(I.column(o['officeId'],o['sites']) for r in shorts for o in r['pool'])
            M=Master(I)
            rawip=M.solve(raw,integer=True,engine='scip',seconds=args.mip,incumbent=incumbent['solution'])
            expanded=enrich(I,raw,time.perf_counter()+args.generate)
            lp=M.solve(expanded,seconds=args.mip)
            extra=[]; evaluations=0
            if lp['dual'] is not None:
                extra,evaluations=dual_mutate(I,M,expanded,lp['dual'],time.perf_counter()+args.generate)
            allcols=dedup([*expanded,*extra])
            warm = rawip['solution'] if rawip['value']>incumbent['value'] else incumbent['solution']
            ip=M.solve(allcols,integer=True,engine='scip',seconds=args.mip,incumbent=warm)
            hybrid_overhead=time.perf_counter()-t0
            hybrid_wall=sum(r['wall'] for r in shorts)+hybrid_overhead
            for r in (rawip,ip):
                assert_valid(I.data,r['solution'],r['value'])
                assert r['value']>=incumbent['value']-1e-5*max(1.,abs(incumbent['value'])), (name,r['status'])
            out=HERE/'logs'/f'{tag}_{name}_r{repeat}_hybrid.solution.json'
            out.write_text(report_json(ip['solution']))
            # A single baseline run gets the actually spent hybrid wall budget.
            long=baseline(exe,path,f'{tag}_{name}_r{repeat}_matched',hybrid_wall,1+100*repeat)
            certificate=None
            if lp['dual'] is not None:
                certificate=max(0.,lp['dual_base']+sum(max(0.,M.relaxed_pricing_bound(o,lp['dual'])) for o in range(I.m)))
            row=dict(case=name,repeat=repeat,n=I.n,offices=I.m,workers=I.w,
                     starts=args.starts,short_limit=args.short,mip_limit=args.mip,generation_limit=args.generate,
                     short_scores=[r['value'] for r in shorts],short_walls=[r['wall'] for r in shorts],
                     best_short=incumbent['value'],raw_ip=rawip['value'],hybrid=ip['value'],
                     matched_baseline=long['value'],matched_limit=long['limit'],matched_wall=long['wall'],
                     hybrid_wall=hybrid_wall,hybrid_overhead=hybrid_overhead,
                     pool_raw=len(raw),pool_enriched=len(expanded),pool_final=len(allcols),
                     dual_evaluations=evaluations,restricted_lp=lp['value'],
                     safe_cheap_certificate=certificate,rows=lp['rows'],nnz=lp['nnz'],
                     mip_status=ip['status'],pool_ip_bound=ip['bound'],solution=str(out),
                     gain_vs_best_short=(ip['value']/incumbent['value']-1.) if incumbent['value']>0 else None,
                     gain_vs_matched=(ip['value']/long['value']-1.) if long['value']>0 else None)
            rows.append(row)
            print(report_json(row),flush=True)
            args.out.parent.mkdir(parents=True,exist_ok=True)
            args.out.write_text(report_json(dict(config=vars_json(args),results=rows,metadata=metadata()),indent=2))


def pricing_bench(args):
    prepare(); rows=[]
    for n,m in ((12,3),(20,4),(40,5),(80,6)):
        p=HERE/'data'/f'pricing{n}.json'
        gen.gen2(23000+n,str(p),ns=n,no=m,nw=2*m,nsk=3,wsk=2,dist='road',af=.03,capf=1.2)
        data=json.loads(p.read_text()); I=Instance(data); M=Master(I)
        init=[I.column(o,[s]) for o in range(I.m) for s in range(I.n)]
        init=dedup(init)
        cg=cg_scip(M,init,seconds=args.total,price_seconds=args.price)
        final_lp=M.solve(cg['pool'],seconds=args.mip)
        ip=M.solve(cg['pool'],integer=True,engine='scip',seconds=args.mip)
        assert_valid(data,ip['solution'],ip['value'])
        r=dict(n=n,offices=m,seed=23000+n,total_limit=args.total,price_limit=args.price,
               cg_seconds=cg['seconds'],converged=cg['converged'],columns=len(cg['pool']),
               restricted_lp=final_lp['value'],restricted_ip=ip['value'],
               upper_bound=cg['upper_bound'],final_lp_seconds=final_lp['seconds'],
               final_ip_seconds=ip['seconds'],final_ip_status=ip['status'],
               final_ip_limit=args.mip,trace=cg['trace'])
        rows.append(r); print(report_json({k:v for k,v in r.items() if k!='trace'}),flush=True)
        args.out.parent.mkdir(parents=True,exist_ok=True)
        args.out.write_text(report_json(dict(results=rows,metadata=metadata()),indent=2))


def metadata():
    return dict(python=sys.version.split()[0],os_family=platform.system(),highs=highspy.Highs().version(),
                affinity_cpus=len(os.sched_getaffinity(0)),threads_per_solve=1,
                git_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip())


def vars_json(args):
    return {k:str(v) if isinstance(v,Path) else v for k,v in vars(args).items() if k!='func'}


if __name__=='__main__':
    ap=argparse.ArgumentParser(); sub=ap.add_subparsers(required=True)
    p=sub.add_parser('pool'); p.add_argument('--short',type=float,default=2.)
    p.add_argument('--mip',type=float,default=1.); p.add_argument('--generate',type=float,default=.5)
    p.add_argument('--repeats',type=int,default=2); p.add_argument('--only',default='')
    p.add_argument('--starts',type=int,default=3)
    p.add_argument('--collect',action='store_true',help='observe intermediate best and elite zones')
    p.add_argument('--out',type=Path,default=HERE/'logs/pool_bench.json'); p.set_defaults(func=pool_bench)
    p=sub.add_parser('pricing'); p.add_argument('--total',type=float,default=10.)
    p.add_argument('--price',type=float,default=.3); p.add_argument('--mip',type=float,default=1.)
    p.add_argument('--out',type=Path,default=HERE/'logs/pricing_scale.json'); p.set_defaults(func=pricing_bench)
    args=ap.parse_args(); args.func(args)
