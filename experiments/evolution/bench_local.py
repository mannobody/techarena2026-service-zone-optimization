"""Frozen incumbents -> local MIP, and a fresh baseline with matching total wall."""
import argparse
from itertools import combinations
import json
import os
from pathlib import Path
import random
import shutil
import subprocess
import time

from bench import HERE,ROOT,data,validator
from local_mip import Instance,improve,objective


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--source',default='screen_v1')
    ap.add_argument('--source-variant',choices=['base','workers'],default='base')
    ap.add_argument('--seed',type=int,default=1)
    ap.add_argument('--limit',type=float,default=2.);ap.add_argument('--attempts',type=int,default=3)
    ap.add_argument('--radius',type=int,default=12);ap.add_argument('--only',default='anti0,multiskill0,tightA0,small0,large0,huge0')
    ap.add_argument('--tag',default='local_v1');args=ap.parse_args()
    logs=HERE/'logs'/args.tag;logs.mkdir(parents=True,exist_ok=True)
    (logs/'bin').mkdir(exist_ok=True)
    binary='baseline' if args.source_variant=='base' else 'warm'
    source_binary=HERE/'logs'/args.source/'bin'/binary
    if not source_binary.exists():source_binary=HERE/'artifacts'/binary
    shutil.copy2(source_binary,logs/'bin'/binary)
    for name in ('local_mip.py','bench_local.py'):shutil.copy2(HERE/name,logs/(name+'.snapshot'))
    source=json.loads((HERE/'logs'/args.source/'results.json').read_text())['results'];rows=[]
    for name in args.only.split(','):
        choices=[r for r in source if r['case']=='suite_'+name and r['variant']==args.source_variant and r['seed']==args.seed]
        if not choices:continue
        base=choices[0];I=Instance.read(HERE/'data'/f'suite_{name}.json');initial=json.loads(Path(base['solution']).read_text())
        current=initial;history=[];start=time.perf_counter();rnd=random.Random(40000)
        opened=[r['officeId'] for r in current]
        pairs=list(combinations(opened,2))
        if len(opened)==1:
            pairs=[(opened[0],o) for o in range(I.m) if o!=opened[0]]
        pairs.sort(key=lambda p:float(np_distance(I,p)))
        for step in range(min(args.attempts,len(pairs))):
            offices=list(pairs[step])
            # Alternate a neighboring pair with a triplet/new office.
            if step%3==2:
                unused=[o for o in range(I.m) if o not in offices]
                if unused:offices.append(rnd.choice(unused))
            r=improve(I,current,offices,seconds=args.limit,radius=args.radius)
            current=r['solution'];history.append({k:v for k,v in r.items() if k!='solution'})
        extra=time.perf_counter()-start
        score=objective(I,current);out=logs/f'{name}.solution.json';out.write_text(json.dumps(current))
        matched=logs/f'{name}_matched.solution.json';t=time.perf_counter()
        proc=subprocess.run([str(logs/'bin'/binary),str(HERE/'data'/f'suite_{name}.json'),str(matched),str(base['wall']+extra)],
                            env=dict(os.environ,NT=str(base['threads']),SEED=str(args.seed),EVO='0',
                                     WORKER_DFS='1' if args.source_variant=='workers' else '0'),capture_output=True,text=True)
        wall=time.perf_counter()-t;(logs/f'{name}_matched.stderr.txt').write_text(proc.stderr)
        matched_score=validator.validate(HERE/'data'/f'suite_{name}.json',matched)
        row=dict(case=name,seed=args.seed,source_variant=args.source_variant,n=I.n,offices=I.m,base=base['score'],base_wall=base['wall'],
                 local=score,extra_wall=extra,matched=matched_score,matched_limit=base['wall']+extra,
                 matched_wall=wall,history=history,solution=str(out))
        rows.append(row);print(json.dumps(row),flush=True)
        (logs/'results.json').write_text(json.dumps(dict(config=vars(args),results=rows),indent=2))


def np_distance(I,p):
    a,b=I.xy[I.n+p[0]],I.xy[I.n+p[1]]
    return ((a-b)**2).sum()


if __name__=='__main__':main()
