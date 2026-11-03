import sys,random,json,hashlib,math
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
for split,base in [('train',81000),('holdout',91000)]:
 d=H/'data'/split;d.mkdir(exist_ok=True)
 for j,(cls,(_,mk)) in enumerate(gen.SUITE.items()):
  for i in range(2 if split=='train' else 1):
   seed=base+j*100+i;p=d/f'{cls}{i}.json';assert not p.exists()
   params=mk(random.Random(seed));gen.gen2(seed,p,**params)
   manifest.append(dict(path=str(p),generator='gen2',seed=seed,params=params))
# Independent generator: correlated road preferences unrelated to positions,
# heterogeneous rewards, deterministic skill coverage, varying task multiplicity.
for split,base in [('train',82000),('holdout',92000)]:
 for i in range(4):
  seed=base+i;r=random.Random(seed);n=[160,320,700,10000][i];m=[6,8,12,24][i];K=4
  xy=[(r.random(),r.random()) for _ in range(n+m)];scale=1e5 if i==3 else 100
  latent=[r.randrange(m) for _ in range(n)];groups=[r.randrange(3) for _ in range(m)]
  sites=[dict(x=x,y=y,reward=scale*r.uniform(.6,2.4),tasks=[r.randrange(K) for _ in range(r.randint(1,4))]) for x,y in xy[:n]]
  offices=[dict(x=x,y=y,cost=scale*n/m*r.uniform(.01,.04),maxSize=int(n/m*1.4)) for x,y in xy[n:]]
  distances=[[scale*(.1+(.08 if groups[o]==groups[latent[s]] else .7)+.25*r.random()+.2*math.dist(xy[n+o],xy[s])) for s in range(n)] for o in range(m)]
  data=dict(sites=sites,offices=offices,workers=[[k] for k in range(K) for _ in range(m//2)]+[[k,(k+1)%K] for k in range(K)],distances=distances,maxDifference=0 if i==0 else n,balanceCoefficient=0 if i%2 else scale*.5)
  p=H/'data'/split/f'latent{i}.json';assert not p.exists();p.write_text(json.dumps(data))
  manifest.append(dict(path=str(p),generator='latent-v1',seed=seed,n=n,m=m))
for e in manifest:e['sha256']=hashlib.sha256(Path(e['path']).read_bytes()).hexdigest()
(H/'data/manifest.json').write_text(report_json(manifest,indent=2))
print(len(manifest),'instances generated; holdout frozen before experiments')
