"""Exhaustive finite-point geometry vs rank <= 6 forbidden-support clauses.
Research only. Two offices, six sites; all 3^6 assignments, no resource constraints.
"""
from pathlib import Path
from itertools import combinations,product
import random,json
from shapely.geometry import MultiPoint,Point
H=Path(__file__).resolve().parent;out=[]
for seed in range(181000,181040):
 r=random.Random(seed);pts=[(r.randrange(-5,6),r.randrange(-5,6)) for _ in range(8)]
 if seed%5==0:pts=[(r.randrange(-5,6),0) for _ in range(8)]
 covers=[];witness=[]
 for o in range(2):
  cc=[]
  for mask in range(64):
   h=MultiPoint([pts[6+o]]+[pts[x] for x in range(6) if mask>>x&1]).convex_hull
   cc.append(sum((int(h.covers(Point(p)))<<j) for j,p in enumerate(pts)))
  covers.append(cc);ww=[]
  for q in range(8):
   candidates=[m for m in range(64) if m.bit_count()<=3 and cc[m]>>q&1]
   ww.append([m for m in candidates if not any(k!=m and k&m==k for k in candidates)])
  witness.append(ww)
 clauses=set()
 for q in range(8):
  clauses.update(product(witness[0][q],witness[1][q]))
 checked=0;valid=0;maxrank=0
 for a,b in clauses:maxrank=max(maxrank,max(1,a.bit_count())+max(1,b.bit_count()))
 for assignment in product((-1,0,1),repeat=6):
  masks=[sum(1<<x for x,o in enumerate(assignment) if o==k) for k in range(2)]
  actual=not(masks[0] and masks[1] and covers[0][masks[0]]&covers[1][masks[1]])
  model=not(masks[0] and masks[1] and any(a&masks[0]==a and b&masks[1]==b for a,b in clauses))
  assert actual==model,(seed,assignment);checked+=1;valid+=actual
 out.append(dict(seed=seed,points=pts,assignments=checked,valid=valid,clauses=len(clauses),max_rank=maxrank))
print(json.dumps(dict(instances=len(out),assignments=sum(x['assignments'] for x in out),max_rank=max(x['max_rank'] for x in out),max_clauses=max(x['clauses'] for x in out))))
(H/'logs/circuit_oracle.json').write_text(json.dumps(out,indent=2))
