"""Synthetic-only comparisons with exact input/output provenance and validation."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import importlib.util
import json
import os
from pathlib import Path
import random
import shutil
import subprocess
import sys
import time

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'experiments/colgen'))
from test_models import validator
spec=importlib.util.spec_from_file_location('synthetic_gen',ROOT/'tools/gen.py')
gen=importlib.util.module_from_spec(spec);spec.loader.exec_module(gen)


def data():
    folder=HERE/'data';folder.mkdir(exist_ok=True)
    for cls,(count,mk) in gen.SUITE.items():
        for j in range(count):
            p=folder/f'suite_{cls}{j}.json'
            if not p.exists():gen.gen2(31000+100*list(gen.SUITE).index(cls)+j,str(p),**mk(random.Random(31000+100*list(gen.SUITE).index(cls)+j)))
    edge=folder/'edge';edge.mkdir(exist_ok=True)
    if not(edge/'edge_big10k.json').exists():gen.edge(str(edge))
    return folder


def holdout_data():
    folder=HERE/'data/holdout';folder.mkdir(parents=True,exist_ok=True)
    configs={
        'huge0':dict(ns=10000,no=25,nw=50,nsk=5,dist='road',span=1.,dscale=1e5),
        'huge1':dict(ns=10000,no=30,nw=60,nsk=7,dist='road',wsk=3,tmax=4,capf=1.5,A=10000,af=0.),
        'anti0':dict(ns=700,no=12,nw=30,nsk=5,dist='anti',span=1.,dscale=1e4,af=.02),
        'balance0':dict(ns=800,no=12,nw=24,nsk=4,A=0,af=5.,tmax=6,capf=1.2),
    }
    manifest={}
    for j,(name,cfg) in enumerate(configs.items()):
        seed=42000+j;p=folder/f'holdout_{name}.json'
        if not p.exists():
            gen.gen2(seed,str(p),**cfg)
            # SUITE uses constant rewards. This holdout deliberately changes
            # their distribution, without consulting any solver results.
            obj=json.loads(p.read_text());rnd=random.Random(seed+100000)
            for site in obj['sites']:site['reward']*=rnd.uniform(.25,2.5)
            p.write_text(json.dumps(obj))
        manifest[name]=dict(seed=seed,parameters=cfg,reward_factor='U[0.25,2.5]',reward_seed=seed+100000)
    (folder/'manifest.txt').write_text(json.dumps(manifest,indent=2))
    return folder


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--seconds',type=float,default=5.)
    ap.add_argument('--runs',type=int,default=1);ap.add_argument('--threads',type=int,default=1)
    ap.add_argument('--jobs',type=int,default=3);ap.add_argument('--variants',default='base,random,genetic')
    ap.add_argument('--suite',choices=['screen','all','edge','holdout'],default='screen');ap.add_argument('--only',default='')
    ap.add_argument('--tag',default='screen');args=ap.parse_args()
    folder=data();logs=HERE/'logs'/args.tag;logs.mkdir(parents=True,exist_ok=True)
    binaries=logs/'bin';binaries.mkdir(exist_ok=True)
    for name in ('baseline','warm'):
        shutil.copy2(HERE/'artifacts'/name,binaries/name)
    if any(v.startswith('integrated') for v in args.variants.split(',')):
        shutil.copy2(HERE/'artifacts/integrated',binaries/'integrated')
        shutil.copy2(HERE/'artifacts/integrated.cpp',logs/'integrated.cpp.snapshot')
        shutil.copy2(HERE/'artifacts/integrated_build.json',logs/'integrated_build.json')
    shutil.copy2(HERE/'artifacts/build.json',logs/'build.json')
    for name in ('warm.h','memetic.h','workers.h','scout.h','build.py'):
        shutil.copy2(HERE/name,logs/(name+'.snapshot'))
    files=sorted((folder/'edge').glob('*.json')) if args.suite=='edge' else sorted(folder.glob('suite_*.json'))
    if args.suite=='holdout':files=sorted(holdout_data().glob('*.json'))
    if args.suite=='screen':files=[p for p in files if p.stem.endswith('0')]
    if args.only:
        names=args.only.split(',');files=[p for p in files if p.stem.removeprefix('suite_').removeprefix('holdout_') in names or p.stem in names]
        found={p.stem.removeprefix('suite_').removeprefix('holdout_') for p in files}|{p.stem for p in files}
        assert set(names)<=found, f'Unknown requested cases: {set(names)-found}'
    assert files,'No inputs selected'
    variants=args.variants.split(',')
    jobs=[(p,v,seed) for seed in range(1,args.runs+1) for p in files for v in variants]
    config=dict(vars(args),inputs=[str(p) for p in files])
    (logs/'config.json').write_text(json.dumps(config,indent=2))
    def run(job):
        p,v,seed=job;key=f'{p.stem}_{v}_s{seed}';out=logs/f'{key}.solution.json'
        exe=binaries/('integrated' if v.startswith('integrated') else 'baseline' if v=='base' else 'warm')
        if v.startswith('integrated'):
            flags={'integrated':(2,1),'integrated_legacy':(0,0),'integrated_workers':(0,1),'integrated_random':(1,1)}[v]
            env=dict(os.environ,NT=str(args.threads),SEED=str(seed),WARM_START=str(flags[0]),WORKER_DFS=str(flags[1]))
        else:
            env=dict(os.environ,NT=str(args.threads),SEED=str(seed),EVO=str({'base':0,'random':1,'genetic':2,'memetic':3,'mutation':4,'patch':5,'workers':0,'combined':2,'scout':0,'portfolio':2,'all':2}[v]),
                     WORKER_DFS='1' if v in ('workers','combined','all') else '0',
                     SCOUT='1' if v in ('scout','portfolio','all') else '0')
        t=time.perf_counter()
        r=subprocess.run([str(exe),str(p),str(out),str(args.seconds)],env=env,capture_output=True,text=True,
                         timeout=max(30.,args.seconds+18.))
        wall=time.perf_counter()-t;(logs/f'{key}.stderr.txt').write_text(r.stderr)
        score=validator.validate(p,out)
        result=dict(case=p.stem,variant=v,seed=seed,limit=args.seconds,threads=args.threads,wall=wall,
                    returncode=r.returncode,score=score if not isinstance(score,str) else None,
                    error=score if isinstance(score,str) else None,solution=str(out),stderr=r.stderr[-500:])
        if r.returncode:result['error']=f'process returned {r.returncode}'
        return result
    rows=[]
    with ThreadPoolExecutor(args.jobs) as pool:
        for r in pool.map(run,jobs):
            rows.append(r)
            print(json.dumps(r),flush=True)
            (logs/'results.json').write_text(json.dumps(dict(config=config,results=rows),indent=2))
    if any(r['error'] for r in rows):sys.exit(1)


if __name__=='__main__':main()
