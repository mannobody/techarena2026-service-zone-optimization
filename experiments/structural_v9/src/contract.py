import json,os,subprocess,sys,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];ROOT=R.parents[1];sys.path.insert(0,str(ROOT/'task'));sys.path.insert(0,str(ROOT/'tools'))
from validate_solution import validate
import gen
revision=sys.argv[1]if len(sys.argv)>1 else 'v3';exe=R/'artifacts'/revision/'candidate';d=R/'logs'/('contract_'+revision);d.mkdir(exist_ok=False)
oracle=json.loads((R/'logs/correctness/oracle.json').read_text());tests=[(r['name'],R/'inputs'/f"{r['name']}.json",r['oracle']['objective'])for r in oracle]
edge=d/'inputs';edge.mkdir();gen.edge(str(edge));tests +=[(p.stem,p,None)for p in edge.glob('*.json')];rows=[]
for name,inp,expected in tests:
    out=d/f'{name}.solution.json';err=d/f'{name}.stderr';t=time.monotonic()
    with err.open('w')as f:p=subprocess.run(['taskset','-c','14,15',str(exe),str(inp),str(out),'1'],env={'PATH':os.environ['PATH'],'NT':'2','SEED':'9301'},stderr=f,timeout=3)
    wall=time.monotonic()-t;v=validate(inp,out);valid=isinstance(v,(int,float));ok=valid and (expected is None or abs(v-expected)<1e-7)
    rows.append(dict(name=name,expected=expected,official=v,valid=valid,ok=ok,rc=p.returncode,wall=wall))
# Server contract: no argv and no NT, one input, one output. stderr captured by
# parent outside cwd. TL override only for the inexpensive contract check.
wd=d/'noarg';wd.mkdir();(wd/'instance.json').write_bytes((R/'inputs/dev/small_grid.json').read_bytes())
with (d/'noarg.stderr').open('w')as f:
    p=subprocess.run(['taskset','-c','14,15',str(exe)],cwd=wd,env={'PATH':os.environ['PATH'],'TL':'1'},stderr=f,timeout=3)
v=validate(wd/'instance.json',wd/'solution.json');rows.append(dict(name='noarg',official=v,ok=isinstance(v,(int,float))and p.returncode==0,files=sorted(p.name for p in wd.iterdir())))
(d/'results.json').write_text(json.dumps(rows,indent=2));print(json.dumps(dict(cases=len(rows),ok=sum(r['ok']for r in rows),failures=[r for r in rows if not r['ok']])));assert all(r['ok']for r in rows)
