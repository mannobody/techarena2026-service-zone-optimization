"""Compare the frozen previous integrated solver with the server candidate."""
import json,os,sys,time,subprocess,hashlib
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'experiments/evolution'))
sys.path.insert(0,str(ROOT/"experiments/colgen"))
from test_models import validator

if __name__=='__main__':
    cases=['anti3','huge0','huge1','large2','multiskill0','multiskill2','tightA0','alphazero2']
    folder=ROOT/'experiments/clustering/data'
    logs=HERE/'logs/repeat12';logs.mkdir(parents=True,exist_ok=True)
    jobs=[(case,variant,seed) for seed in (1,2,3) for case in cases for variant in ('before','candidate')]
    def run(job):
        case,variant,seed=job;key=f'{case}_{variant}_s{seed}';inp=folder/(case+'.json');out=logs/(key+'.solution.json')
        env=dict(os.environ,NT='2',SEED=str(seed),DBG='1')
        for flag in ('FINAL_POLISH','WORKER_DFS','WARM_START','EXACT2','LAZY','WFIX','LEVEL'):env.pop(flag,None)
        start=time.perf_counter();p=subprocess.run([str(HERE/'artifacts'/variant),str(inp),str(out),'12'],env=env,capture_output=True,text=True,timeout=35)
        wall=time.perf_counter()-start;score=validator.validate(inp,out)
        row=dict(case=case,variant=variant,seed=seed,limit=12,threads=2,wall=wall,returncode=p.returncode,error=score if isinstance(score,str) else None,score=score if not isinstance(score,str) else None,input=str(inp),solution=str(out))
        (logs/(key+'.stderr.txt')).write_text(p.stderr);return row
    rows=[]
    with ThreadPoolExecutor(3) as pool:
        for row in pool.map(run,jobs):
            rows.append(row);(logs/'results.json').write_text(json.dumps(dict(config=dict(seconds=12,threads=2,seeds=[1,2,3],jobs=3),results=rows),indent=2));print(row['case'],row['variant'],row['seed'],row['score'],row['error'],flush=True)
    assert all(not r['error'] and r['returncode']==0 for r in rows)
