from pathlib import Path
import json,itertools,time
import numpy as np
import shapely
from shapely.geometry import MultiPoint
H=Path(__file__).resolve().parent;rows=[]
for p in sorted((H/'data/train').glob('*.json')):
 d=json.loads(p.read_text());sol=json.loads((H/'logs/train_base60'/f'{p.stem}_1_base.json').read_text());n=len(d['sites']);m=len(d['offices']);xy=[(s['x'],s['y']) for s in d['sites']+d['offices']];points=shapely.points(xy);asg=[-1]*n
 hull={o['officeId']:MultiPoint([xy[n+o['officeId']]]+[xy[s] for s in o['sites']]).convex_hull for o in sol};cov={o:shapely.covers(h,points) for o,h in hull.items()};union=np.zeros(n+m,dtype=bool)
 for o in sol:
  for x in o['sites']:asg[x]=o['officeId']
 for mask in cov.values():union|=mask
 pairs=[(a,b) for a,b in itertools.combinations(hull,2) if hull[a].intersects(hull[b])]
 assert all(not np.any(cov[a]&cov[b]) for a,b in itertools.combinations(hull,2))
 offers=sorted([(d['sites'][x]['reward']-d['distances'][o][x],o,x) for x in range(n) if asg[x]<0 for o in hull if d['sites'][x]['reward']>d['distances'][o][x]],reverse=True)[:200]
 stat=dict(clear=0,blocked=0,blocked_by_office=0,inside_own=0,foreign_footprint=0,total=len(offers));samples=[]
 for gain,o,x in offers:
  if cov[o][x]:stat['inside_own']+=1
  elif union[x]:stat['foreign_footprint']+=1
  coords=list(hull[o].exterior.coords) if hull[o].geom_type=='Polygon' else list(hull[o].coords)
  nh=MultiPoint(coords+[xy[x]]).convex_hull;hit=shapely.covers(nh,points)&union&~cov[o];ids=np.flatnonzero(hit)
  if len(ids):stat['blocked']+=1
  else:stat['clear']+=1
  if any(i>=n and i-n in hull and i-n!=o for i in ids):stat['blocked_by_office']+=1
  if len(samples)<5:samples.append(dict(gain=gain,office=o,site=x,blocking_points=len(ids)))
 rows.append(dict(case=p.stem,sites=n,active_offices=len(sol),assigned=sum(a>=0 for a in asg),covered_unassigned=sum(asg[x]<0 and union[x] for x in range(n)),crossing_zone_pairs=pairs,top200_free_offers=stat,samples=samples));print(p.stem,stat,'crossings',len(pairs),flush=True)
(H/'logs/diagnosis.json').write_text(json.dumps(rows,indent=2))
