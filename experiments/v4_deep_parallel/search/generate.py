import sys,random,json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parent;ROOT=R.parents[2];sys.path.insert(0,str(ROOT/'tools'));import gen
classes=['anti','alphabig','tightA','multiskill','grid','cluster','large','huge']; meta={}
for j,c in enumerate(classes):
 seed=721000+100*j;p=gen.SUITE[c][1](random.Random(seed));p['A']=0 if c=='tightA' else p.get('A');out=R/'inputs'/f'{c}.json';gen.gen2(seed,str(out),**p)
 meta[c]={'seed':seed,'parameters':p,'path':str(out.relative_to(ROOT)),'sha256':hashlib.sha256(out.read_bytes()).hexdigest()}
(R/'INPUTS.json').write_text(json.dumps(meta,indent=2))
