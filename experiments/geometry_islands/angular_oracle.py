"""Anchored membership = singleton ray + threshold edges between opposite halfplanes."""
from pathlib import Path
from fractions import Fraction
import random,json
from shapely.geometry import MultiPoint,Point
H=Path(__file__).resolve().parent;checks=0;rows=[]
for seed in range(201000,201040):
 r=random.Random(seed);pts=[(r.randrange(-5,6),r.randrange(-5,6)) for _ in range(8)]
 if seed%5==0:pts=[(r.randrange(-5,6),0) for _ in range(8)]
 for o in range(2):
  for q in range(8):
   origin=pts[6+o];target=pts[q];d=(target[0]-origin[0],target[1]-origin[1]);up=[];low=[];single=[]
   for i,a in enumerate(pts[:6]):
    v=(a[0]-target[0],a[1]-target[1]);X=d[0]*v[0]+d[1]*v[1];Y=d[0]*v[1]-d[1]*v[0]
    if Y>0:up.append((Fraction(X,Y),i))
    elif Y<0:low.append((Fraction(X,Y),i))
    elif X>=0:single.append(i)
   low.sort();up.sort()
   for mask in range(64):
    shape=MultiPoint([origin]+[pts[i] for i in range(6) if mask>>i&1]).convex_hull
    actual=shape.covers(Point(target))
    pred=origin==target or any(mask>>i&1 for i in single)
    # A selected lower prefix with ratio <= upper ratio forces footprint membership.
    pred=pred or any(mask>>a&1 and any(v<=u and mask>>b&1 for v,b in low) for u,a in up)
    assert bool(pred)==actual,(seed,o,q,mask,pts);checks+=1
 rows.append(dict(seed=seed,points=pts))
(H/'logs/angular_oracle.json').write_text(json.dumps(dict(checks=checks,rows=rows),indent=2));print(checks,'exact integer angular-prefix / Shapely matches')
