import json,os,subprocess,sys,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];ROOT=R.parents[1];sys.path.insert(0,str(ROOT/'task'));sys.path.insert(0,str(ROOT/'tools'))
from validate_solution import validate
import gen
revision=sys.argv[1]if len(sys.argv)>1 else 'v1';d=R/'logs'/('qa_'+revision);d.mkdir(exist_ok=False)
inputs=d/'inputs';inputs.mkdir();gen.edge(str(inputs))
tests=[(p.stem,p)for p in inputs.glob('*.json')]
old=ROOT/'experiments/structural_v9'
tests +=[(k,ROOT/v['path'])for k,v in json.loads((old/'DEV_INPUTS.json').read_text()).items()]
exe=R/'artifacts'/revision/'candidate';assert exe.exists();rows=[]
for name,inp in tests:
 for mode in [1,2]:
    out=d/f'{name}_{mode}.solution.json';t=time.monotonic()
    env={'PATH':os.environ['PATH'],'NT':'2','SEED':'10001','ZM_POOL':'0','ZM_RESERVE':'0','GW_MODE':str(mode),'GW_TRACE':'1'}
    # Tiny exact would bypass warm start; exercise the new code on these tests.
    env['ZM_DISABLE']='1'
    with (d/f'{name}_{mode}.stderr').open('w')as f:
        p=subprocess.run(['taskset','-c','14,15',str(exe),str(inp),str(out),'2'],env=env,stderr=f,timeout=5)
    wall=time.monotonic()-t;v=validate(inp,out)
    rows.append(dict(case=name,mode=mode,rc=p.returncode,wall=wall,official=v,valid=isinstance(v,(int,float))))
(d/'results.json').write_text(json.dumps(rows,indent=2))
print(json.dumps(dict(runs=len(rows),valid=sum(r['valid']for r in rows),failures=[r for r in rows if not r['valid']or r['rc']!=0])))
assert all(r['valid']and r['rc']==0 for r in rows)
