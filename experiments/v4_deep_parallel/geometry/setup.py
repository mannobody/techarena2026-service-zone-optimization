import sys,json,random,hashlib
from pathlib import Path
R=Path(__file__).resolve().parent;ROOT=R.parents[2]
sys.path.insert(0,str(ROOT/'tools'));import gen
classes=['anti','cluster','tightA','alphabig','multiskill','large']
inputs={};meta=[]
for j,c in enumerate(classes):
 seed=711000+100*j;p=gen.SUITE[c][1](random.Random(seed))
 if c=='tightA':p['A']=0
 f=R/'inputs'/f'dev_{c}.json';gen.gen2(seed,str(f),**p);inputs[c]=str(f.relative_to(ROOT));meta.append(dict(case=c,seed=seed,params=p,sha256=hashlib.sha256(f.read_bytes()).hexdigest()))
(R/'INPUTS.json').write_text(json.dumps(meta,indent=2))
base='experiments/v4_deep_parallel/shared/v4'
spec=dict(name='baseline280',jobs=3,cases=inputs,seeds=[711],seconds=280,variants={'v4':dict(binary=base,env={'DBG':'1'})})
(R/'BASELINE280.json').write_text(json.dumps(spec,indent=2))
run=(ROOT/'experiments/v4_local_search/run.py').read_text().replace("parents[2]; R=", "parents[3]; R=")
(R/'run.py').write_text(run)
