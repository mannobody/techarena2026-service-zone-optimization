import random,json,itertools,subprocess,math,sys
tag=sys.argv[1] if len(sys.argv)>1 else "v1"
from pathlib import Path
from shapely.geometry import MultiPoint,Point
H=Path(__file__).resolve().parent;rows=[];errors=[]
for mode in [0,1]:
 for seed in range(160):
  r=random.Random(141000+seed);n=8
  pts=[(r.randrange(-4,5),r.randrange(-4,5)) if seed%4==0 else (r.random(),r.random()) for _ in range(n)]
  if seed%4==1:pts=[(x,0) for x,y in pts]
  weights=[r.randrange(-5,9) if mode==0 else r.randrange(0,9) for i in range(n)]
  red=[int(r.random()<.2) for i in range(n)] if mode==0 else [0]*n
  must=0 if mode==0 else n-1;red[must]=0
  vs=list(range(n)) if mode==0 else list(range(n-1));best=-1e100 if mode==0 else 1e100
  protect=[pts[0]] if mode else []
  for bits in range(1<<len(vs)):
   subset=[vs[i] for i in range(len(vs)) if bits>>i&1]
   if mode==0:
    if not subset:continue
    hull=MultiPoint([pts[i] for i in subset]).convex_hull
    covered=[i for i in range(n) if hull.covers(Point(pts[i]))]
    if must not in covered or any(red[i] for i in covered):continue
    best=max(best,sum(weights[i] for i in covered))
   else:
    hull=MultiPoint(protect+[pts[i] for i in subset]).convex_hull
    if not hull.covers(Point(pts[must])):best=min(best,sum(weights[i] for i in vs if i not in subset))
  text=f'{n} {len(vs)} {must} {mode}\n'+''.join(f'{x:.17g} {y:.17g} {w} {z}\n' for (x,y),w,z in zip(pts,weights,red))+' '.join(map(str,vs))+'\n'
  if mode:text+=str(len(protect))+'\n'+''.join(f'{x:.17g} {y:.17g}\n' for x,y in protect)
  p=subprocess.run([str(H/'artifacts'/f'oracle_{tag}')],input=text,text=True,capture_output=True,timeout=65);got=float(p.stdout.split()[0]);ok=(abs(got-best)<1e-6 or (best < -1e80 and got < -1e80) or (best >1e80 and got>1e80))
  row=dict(mode=mode,seed=141000+seed,expected=best,actual=got,ok=ok);rows.append(row)
  if not ok:errors.append(row);(H/'data'/f'oracle_fail_{mode}_{seed}.txt').write_text(text)
(H/'logs'/f'oracle_{tag}.json').write_text(json.dumps(rows,indent=2));print('Passed',sum(x['ok'] for x in rows),'/',len(rows));print(errors[:10]);assert not errors
