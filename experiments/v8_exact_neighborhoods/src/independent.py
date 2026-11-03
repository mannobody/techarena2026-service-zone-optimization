import hashlib,json,sys,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];ROOT=R.parents[1];sys.path.insert(0,str(ROOT/'tools'));import gen
f=json.loads((R/'FREEZE.json').read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for p,h in f['files'].items():assert sha(ROOT/p)==h,(p,'freeze mismatch')
d=R/'inputs/independent';d.mkdir(exist_ok=False);records={}
for k,params in f['independent_inputs'].items():
    p=d/f'{k}.json';gen.gen2(f['generator_seeds'][k],str(p),**params)
    data=json.loads(p.read_text())
    if k=='elongated':
        for x in data['sites']+data['offices']:x['y']*=.001
    p.write_text(json.dumps(data,separators=(',',':')))
    records[k]=dict(path=str(p.relative_to(ROOT)),sha256=sha(p),params=params,seed=f['generator_seeds'][k])
(R/'INDEPENDENT_INPUTS.json').write_text(json.dumps(dict(freeze_sha256=sha(R/'FREEZE.json'),generated_unix=time.time(),inputs=records),indent=2))
for name,seconds,seeds,variants in [('independent10',10,f['test_seeds'],f['variants']),('conditional60',60,[3401],{k:v for k,v in f['variants'].items() if k in ['v4','v8','off','candidate']})]:
    spec=dict(destination=str((R/'logs'/name).relative_to(ROOT)),seconds=seconds,seeds=seeds,cpu_pairs=f['cpu_pairs'],
        cases={k:v['path'] for k,v in records.items()},variants=variants,order_seed=f['order_seed'],hard_wall=True,
        snapshots=[3,7,9] if seconds==10 else [20,40,55])
    (R/f'{name.upper()}.json').write_text(json.dumps(spec,indent=2))
print('8 independent inputs generated after freeze; conditional60 spec is NOT authorization to skip its trigger.')
