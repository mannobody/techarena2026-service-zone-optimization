"""Contract and official-validator QA, separate from paired quality benchmarks."""
import hashlib,json,os,subprocess,sys,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];ROOT=R.parents[1];sys.path.insert(0,str(ROOT/'task'));sys.path.insert(0,str(ROOT/'tools'))
from validate_solution import validate
import gen
dest=R/'logs/contract';dest.mkdir(exist_ok=False);rows=[];exe=R/'artifacts/final/solution'
freeze=json.loads((R/'FREEZE.json').read_text());assert hashlib.sha256(exe.read_bytes()).hexdigest()==freeze['files'][str(exe.relative_to(ROOT))]
oracle=json.loads((R/'logs/oracle/results.json').read_text());tests=[(r['case'],R/'inputs'/f"{r['case']}.json",r['oracle']['value']) for r in oracle]
tests+=[(k,R/'inputs'/f'{k}.json',v) for k,v in [('negative_profit_balance',293),('fill_geo_fallback',27),('worker_budget',45)]]
edges=dest/'edge_inputs';edges.mkdir();gen.edge(str(edges))
tests += [(p.stem,p,None) for p in edges.glob('*.json')]
for name,inp,expected in tests:
    out=dest/f'{name}.solution.json';err=dest/f'{name}.stderr';t=time.monotonic()
    env={k:v for k,v in os.environ.items() if k in ['PATH','HOME','LANG']};env|={'NT':'2','SEED':'3501','DBG':'1'}
    with err.open('w') as f:cp=subprocess.run(['taskset','-c','14,15',str(exe),str(inp),str(out),'1'],env=env,stderr=f,stdout=subprocess.DEVNULL,timeout=3)
    wall=time.monotonic()-t;v=validate(inp,out);valid=not isinstance(v,str)
    row=dict(case=name,rc=cp.returncode,wall=wall,validator=v,valid=valid,expected=expected,
        optimal_tiny=expected is None or valid and abs(v-expected)<1e-6,source_sha256=freeze['files'][str((R/'artifacts/final/main.cpp').relative_to(ROOT))],affinity=[14,15])
    rows.append(row)
# No argv, NT unset, DBG unset; input/output names only. TL override avoids TL280.
for name in ['cross_segments','negative_profit_balance','worker_budget']:
    d=dest/f'noarg_{name}';d.mkdir();(d/'instance.json').write_bytes((R/'inputs'/f'{name}.json').read_bytes())
    env={k:v for k,v in os.environ.items() if k in ['PATH','HOME','LANG']};env['TL']='1'
    t=time.monotonic()
    with (d/'stderr').open('w') as f:cp=subprocess.run(['taskset','-c','14,15',str(exe)],cwd=d,env=env,stderr=f,timeout=3)
    v=validate(d/'instance.json',d/'solution.json');rows.append(dict(case='noarg_'+name,rc=cp.returncode,wall=time.monotonic()-t,validator=v,valid=not isinstance(v,str),files=sorted(p.name for p in d.iterdir()),DBG='unset',NT='unset'))
(dest/'results.json').write_text(json.dumps(rows,indent=2))
bad=[r for r in rows if r['rc'] or not r['valid'] or not r.get('optimal_tiny',True) or r['wall']>1.1]
print(json.dumps(dict(cases=len(rows),valid=sum(r['valid'] for r in rows),failures=bad,max_wall=max(r['wall'] for r in rows))))
if bad:sys.exit(1)
