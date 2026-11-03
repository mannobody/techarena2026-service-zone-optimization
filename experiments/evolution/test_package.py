"""Exercise the actual standalone package with contest filenames and defaults."""
from concurrent.futures import ThreadPoolExecutor
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

from bench import HERE,validator


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--package',default='candidate_workers_v4')
    ap.add_argument('--tag',default='package_smoke_v4');args=ap.parse_args()
    package=HERE/'artifacts'/args.package
    logs=HERE/'logs'/args.tag;logs.mkdir(exist_ok=True)
    inputs=sorted((HERE/'data/edge').glob('*.json'))+sorted((HERE/'data').glob('suite_multiskill*.json'))
    inputs+=[HERE/'data/holdout/holdout_huge1.json']
    def run(p):
        folder=logs/p.stem;folder.mkdir(exist_ok=True)
        shutil.copy2(p,folder/'instance.json')
        env=dict(os.environ,TL='2',NT='2',SEED='7')
        for flag in ('EVO','SCOUT','WORKER_DFS'):env.pop(flag,None)
        start=time.perf_counter()
        r=subprocess.run([str(package/'solution')],cwd=folder,env=env,capture_output=True,text=True,timeout=20.)
        wall=time.perf_counter()-start
        assert {x.name for x in folder.iterdir()}=={'instance.json','solution.json'}
        score=validator.validate(folder/'instance.json',folder/'solution.json')
        assert r.returncode==0 and not isinstance(score,str),(p,r.returncode,score)
        (logs/(p.stem+'.stderr.txt')).write_text(r.stderr)
        return dict(case=p.stem,score=score,wall=wall,returncode=r.returncode,stderr=r.stderr)
    with ThreadPoolExecutor(2) as pool:rows=list(pool.map(run,inputs))
    (logs/'results.json').write_text(json.dumps(dict(package=str(package),seconds=2.,threads=2,results=rows),indent=2))
    print(f'VALID {len(rows)}/{len(rows)}; max wall {max(r["wall"] for r in rows):.3f}s')
