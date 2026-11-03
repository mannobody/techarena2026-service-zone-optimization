import sys,json,random,hashlib,math
from pathlib import Path

# Serialize an observation copy without altering commands or subprocess env.
import sys as _report_sys
_REPORT_ROOT = next(p for p in Path(__file__).resolve().parents
                    if (p / 'tools/public_metadata.py').is_file())
_report_sys.path.insert(0, str(_REPORT_ROOT / 'tools'))
from public_metadata import public_json as _public_json
def report_json(value, **kwargs):
    return _public_json(value, _REPORT_ROOT, **kwargs)

H=Path(__file__).resolve().parent;R=H.parents[1];sys.path.insert(0,str(R/'tools'));import gen
manifest=[]
for split,base in [('coop_holdout',321000)]:
 d=H/'data'/split;d.mkdir()
 for j,cls in enumerate(['anti','alphabig','tightA','multiskill','grid','cluster','large','huge']):
  seed=base+j*100;params=gen.SUITE[cls][1](random.Random(seed));p=d/f'{cls}0.json';gen.gen2(seed,p,**params)
  manifest.append(dict(path=str(p),split=split,generator='gen2',seed=seed,params=params))
 for j in range(2):
  seed=base+1000+j;r=random.Random(seed);n=[160,480][j];m=[6,10][j];K=4
  xy=[(r.random(),r.random()) for _ in range(n+m)];labels=[r.randrange(m) for _ in range(n)];groups=[r.randrange(3) for _ in range(m)]
  data=dict(sites=[dict(x=x,y=y,reward=r.uniform(60,240),tasks=[r.randrange(K) for _ in range(r.randint(1,4))]) for x,y in xy[:n]],offices=[dict(x=x,y=y,cost=n/m*r.uniform(1,4),maxSize=int(n/m*1.4)) for x,y in xy[n:]],workers=[[k] for k in range(K) for _ in range(m//2)]+[[k,(k+1)%K] for k in range(K)],distances=[[100*(.1+(.08 if groups[o]==groups[labels[s]] else .7)+.25*r.random()+.2*math.dist(xy[n+o],xy[s])) for s in range(n)] for o in range(m)],maxDifference=0 if j==0 else n,balanceCoefficient=50 if j==0 else 0)
  p=d/f'latent{j}.json';p.write_text(json.dumps(data));manifest.append(dict(path=str(p),split=split,generator='latent-v1',seed=seed,n=n,m=m))
for e in manifest:e['sha256']=hashlib.sha256(Path(e['path']).read_bytes()).hexdigest()
(H/'data/coop_holdout_manifest.json').write_text(report_json(manifest,indent=2))
