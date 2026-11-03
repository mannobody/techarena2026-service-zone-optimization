"""Real GWW executions after population initialization repair; correctness only."""
import sys,json,subprocess,time,hashlib,os
from pathlib import Path
R=Path(__file__).resolve().parent;ROOT=R.parents[1];sys.path.insert(0,str(ROOT/'task'))
from validate_solution import validate
D=R/'logs/gww_fixed';D.mkdir(exist_ok=False);rows=[]
exe=R/'artifacts/post_gww_fixed'
(D/'MANIFEST.json').write_text(json.dumps({'binary_sha256':hashlib.sha256(exe.read_bytes()).hexdigest(),'source_sha256':hashlib.sha256((ROOT/'solver/search_research.h').read_bytes()).hexdigest(),'compiler':'g++ -O1 -std=c++17 -D_GLIBCXX_ASSERTIONS','purpose':'correctness only, not throughput/quality'},indent=2))
for source in ['warm_checkpoints5','development60_v1']:
 for case in ['alphabig','tightA','multiskill','grid']:
  for seed in [801,802,803]:
   pre=D/f'{source}_{case}_{seed}';inp=R/'data/development'/f'{case}.json';checkpoint=R/'logs'/source/f'{case}_301_base.solution.json';out=pre.with_suffix('.solution.json')
   start=time.monotonic()
   with pre.with_suffix('.stderr').open('w') as err:
    result=subprocess.run(['taskset','-c','20',str(exe),str(inp),str(checkpoint),str(out),'1','4',str(seed)],stdout=subprocess.DEVNULL,stderr=err,env={'PATH':os.environ['PATH'],'NT':'1','SEARCH_TRACE':'1'},timeout=15)
   val=validate(inp,out);row={'source':source,'case':case,'seed':seed,'rc':result.returncode,'wall':time.monotonic()-start,'valid':not isinstance(val,str),'objective':val,'success':result.returncode==0 and not isinstance(val,str)};rows.append(row);(D/'results.json').write_text(json.dumps(rows,indent=2))
print('GWW fixed:',sum(x['success'] for x in rows),'/',len(rows))
