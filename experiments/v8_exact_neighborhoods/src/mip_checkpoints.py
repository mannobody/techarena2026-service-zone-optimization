import hashlib,json,math,os,random,sys,time
from pathlib import Path
from legacy_mip import choose_peel
from mip import improve
from oracle import R,ROOT

tag=sys.argv[1] if len(sys.argv)>1 else 'mip_checkpoints'
seconds=float(sys.argv[2]) if len(sys.argv)>2 else 2
spec=json.loads((R/'CHECKPOINT_SPEC.json').read_text());dest=R/'logs'/tag;dest.mkdir(exist_ok=False);records=[]
(dest/'MANIFEST.json').write_text(json.dumps(dict(affinity=sorted(os.sched_getaffinity(0)),seconds=seconds,
    source_sha256=hashlib.sha256((R/'src/mip.py').read_bytes()).hexdigest(),
    selection_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),seed=1,
    note='Same small models; no compilation on these physical cores during timed repeat'),indent=2))
for name,inp in spec['cases'].items():
    d=json.loads((ROOT/inp).read_text());inc=json.loads((ROOT/spec['checkpoints'][name]).read_text());by={r['officeId']:r for r in inc}
    oxy=[(o['x'],o['y']) for o in d['offices']]
    for kind in ['geometry','structure']:
        if kind=='geometry':selected=choose_peel(d,inc,18)
        else:
            small=min(by,key=lambda o:len(by[o]['sites']));selected=list(by[small]['sites']) if len(by[small]['sites'])<=24 else choose_peel(d,inc,18)
            for s in choose_peel(d,inc,24):
                if s not in selected and len(selected)<24:selected.append(s)
        ops=sorted({r['officeId'] for r in inc if any(s in selected for s in r['sites'])})
        if kind=='structure':
            closed=[o for o in range(len(oxy)) if o not in by]
            if closed:ops.append(min(closed,key=lambda o:min(math.dist(oxy[o],oxy[p]) for p in ops)))
        labels=['scip','highs'];random.Random(name+kind).shuffle(labels)
        for label in labels:
            p=dest/f'{name}_{kind}_{label}.json'
            r=improve(d,inc,selected,offices=ops,kind=kind,backend=label,seconds=seconds,export=R/'models'/tag/p.name)
            p.write_text(json.dumps(r,indent=2));records.append(dict(case=name,**{k:v for k,v in r.items() if k not in ['solution','events','selected']}))
            print(name,kind,label,round(r['gain'],6),r['conditional_optimal'],round(r['seconds'],3),flush=True)
(dest/'results.json').write_text(json.dumps(records,indent=2))
