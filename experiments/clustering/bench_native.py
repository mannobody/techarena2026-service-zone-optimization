"""Equal-wall A/B on fresh synthetic regimes, with original-coordinate validation."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

from bench_embeddings import HERE,ROOT,data,validator


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--seconds',type=float,default=6.)
    ap.add_argument('--threads',type=int,default=4);ap.add_argument('--jobs',type=int,default=2)
    ap.add_argument('--runs',type=int,default=1);ap.add_argument('--tag',default='native_screen')
    ap.add_argument('--variants',default='base,schedule,mix,ot,affine');ap.add_argument('--only',default='')
    args=ap.parse_args();folder=data();files=sorted(folder.glob('*.json'))
    if args.only:
        requested=set(args.only.split(','));files=[p for p in files if p.stem in requested]
        assert {p.stem for p in files}==requested
    else:files=[p for p in files if p.stem.endswith('0')]
    logs=HERE/'logs'/args.tag;logs.mkdir(parents=True,exist_ok=True);(logs/'bin').mkdir(exist_ok=True)
    shutil.copy2(HERE/'artifacts/prototype',logs/'bin/prototype')
    shutil.copy2(ROOT/'experiments/evolution/artifacts/integrated',logs/'bin/base')
    for name in ('constructors.h','soft_profit.h','territory.h','fill.h','build.py','bench_native.py'):shutil.copy2(HERE/name,logs/(name+'.snapshot'))
    shutil.copy2(HERE/'artifacts/build.json',logs/'build.json')
    config=dict(vars(args),inputs=[str(p) for p in files]);(logs/'config.json').write_text(json.dumps(config,indent=2))
    variants=args.variants.split(',');jobs=[(p,v,seed) for seed in range(1,args.runs+1) for p in files for v in variants]
    def run(job):
        p,v,seed=job;key=f'{p.stem}_{v}_s{seed}';out=logs/(key+'.solution.json')
        mode={'base':0,'schedule':0,'portfolio':0,'mix':1,'ot':2,'affine':3,'soft':4,'fill':0,'fill_all':0,'fill_fast':0,'postfill':0,'postfill_all':0,'territory':0}[v]
        env=dict(os.environ,NT=str(args.threads),SEED=str(seed),CLUSTER_MODE=str(mode),
                 CTOR_SCHEDULE='2' if v=='portfolio' else '1' if v in ('schedule','mix','ot','affine','soft') else '0',
                 FILL_RETRY='1' if v in ('fill','fill_all','fill_fast') else '0',
                 FILL_ALL='1' if v in ('fill_all','postfill_all') else '0',
                 FILL_COVERED='1' if v in ('fill_fast','postfill','postfill_all') else '0',
                 POST_FILL='1' if v in ('postfill','postfill_all') else '0',POST_TERRITORY='1' if v=='territory' else '0')
        start=time.perf_counter()
        proc=subprocess.run([str(logs/'bin'/('base' if v=='base' else 'prototype')),str(p),str(out),str(args.seconds)],
                            env=env,capture_output=True,text=True,timeout=max(30.,args.seconds+18.))
        wall=time.perf_counter()-start;(logs/(key+'.stderr.txt')).write_text(proc.stderr)
        value=validator.validate(p,out)
        return dict(case=p.stem,variant=v,seed=seed,limit=args.seconds,threads=args.threads,wall=wall,
                    score=value if not isinstance(value,str) else None,returncode=proc.returncode,
                    error=value if isinstance(value,str) else None,solution=str(out),stderr=proc.stderr[-500:])
    rows=[]
    with ThreadPoolExecutor(args.jobs) as pool:
        for row in pool.map(run,jobs):
            rows.append(row);print(json.dumps(row),flush=True)
            (logs/'results.json').write_text(json.dumps(dict(config=config,results=rows),indent=2))
    assert all(not r['error'] and not r['returncode'] for r in rows)


if __name__=='__main__':main()
