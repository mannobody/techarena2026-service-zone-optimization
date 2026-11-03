import hashlib,json,os,random,subprocess,sys,time
from pathlib import Path
from oracle import R,ROOT,enumerate_all,official,fixtures
from mip import improve

tag=sys.argv[1] if len(sys.argv)>1 else 'verify_complete'
assert (R/'artifacts/solution').exists(),'Build must complete before this script starts'
out=R/'logs'/tag;out.mkdir(exist_ok=False);records=[]
source=json.loads((R/'logs/oracle/results.json').read_text())
for i,row in enumerate(source):
    name=row['case'];d=json.loads((R/'inputs'/f'{name}.json').read_text())
    configs=[('structure',[],row['oracle'])]
    # Independently enumerate fixed-open geometry from a non-optimal valid state.
    if i<11:
        fixture=fixtures()[name][1];inc=fixture if isinstance(official(d,fixture),(float,int)) else []
        if inc:configs.append(('geometry',inc,enumerate_all(d,inc=inc,kind='geometry')))
    for kind,inc,oracle in configs:
        labels=['scip','highs'];random.Random(791+i).shuffle(labels)
        for label in labels:
            r=improve(d,inc,list(range(len(d['sites']))),kind=kind,backend=label,seconds=3,
                export=R/'models'/tag/f'{name}_{kind}_{label}')
            ok=abs(r['value']-oracle['value'])<1e-6 and r['conditional_optimal']
            entry=dict(case=name,kind=kind,backend=label,ok=ok,expected=oracle['value'],result=r)
            records.append(entry);(out/f'{name}_{kind}_{label}.json').write_text(json.dumps(entry,indent=2))
    # Direct standalone runtime on identical input; entire process is timed.
    p=out/f'{name}_runtime.solution.json';err=out/f'{name}_runtime.stderr'
    t=time.perf_counter()
    with err.open('w') as f:
        cp=subprocess.run(['taskset','-c','18,19',str(R/'artifacts/solution'),str(R/'inputs'/f'{name}.json'),str(p),'2'],
            env=dict(os.environ,NT='2',DBG='1',SEED='101'),stderr=f,timeout=6)
    sol=json.loads(p.read_text());v=official(d,sol)
    entry=dict(case=name,kind='runtime',ok=cp.returncode==0 and isinstance(v,(float,int)) and abs(v-row['oracle']['value'])<1e-6,
        value=v,expected=row['oracle']['value'],rc=cp.returncode,wall=time.perf_counter()-t)
    records.append(entry)
(out/'results.json').write_text(json.dumps(records,indent=2))
failed=[{k:v for k,v in r.items() if k!='result'} for r in records if not r['ok']]
print(json.dumps(dict(comparisons=len(records),failures=failed,cut_models=sum(r.get('result',{}).get('cuts',0)>0 for r in records))))
if failed:sys.exit(1)
