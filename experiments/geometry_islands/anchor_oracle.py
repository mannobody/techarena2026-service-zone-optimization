from pathlib import Path
from types import SimpleNamespace
import json,random,itertools
import numpy as np
from shapely.geometry import MultiPoint,Point
from anchor_support import support
H=Path(__file__).resolve().parent;checks=0;sizes={}
for seed in range(191000,191040):
 r=random.Random(seed);xy=np.array([(r.randrange(-5,6),r.randrange(-5,6)) for _ in range(8)],dtype=float)
 if seed%5==0:xy[:,1]=0
 I=SimpleNamespace(n=6,xy=xy)
 for o in range(2):
  for mask in range(1,64):
   sites=[i for i in range(6) if mask>>i&1];h=MultiPoint(xy[sites+[6+o]]).convex_hull
   for p in range(8):
    if not h.covers(Point(xy[p])):continue
    w=support(I,o,sites,p);assert len(w)<=2 and set(w)<=set(sites)
    assert MultiPoint(xy[[6+o,*w]]).convex_hull.covers(Point(xy[p]))
    checks+=1;sizes[len(w)]=sizes.get(len(w),0)+1
# Tight rank-four example: alternate vertices of a hexagon, unassigned central point.
pts=[(-1,2),(-1,-2),(-2,0),(1,-2),(0,0),(2,0),(1,2)]
covered=[]
for mask in range(16):
 a=[pts[5]]+[pts[i] for i in [0,1] if mask>>i&1]
 b=[pts[6]]+[pts[i] for i in [2,3] if mask>>i&1]
 activeA=bool(mask&3);activeB=bool(mask&12)
 clash=activeA and activeB and any(MultiPoint(a).convex_hull.covers(Point(q)) and MultiPoint(b).convex_hull.covers(Point(q)) for q in pts)
 assert bool(clash)==(mask==15);covered.append(dict(mask=mask,clash=bool(clash)))
r=dict(checks=checks,witness_size_counts=sizes,quartic_points=pts,quartic_assignments=covered)
(H/'logs/anchor_oracle.json').write_text(json.dumps(r,indent=2));print(checks,sizes,'quartic counterexample 16/16')
