# Structural exact repair diagnostic; neither this driver nor backend ships.
import sys,json,time,hashlib,os
from pathlib import Path
from shapely import MultiPoint,Point
import itertools,math
R=Path(__file__).resolve().parent;ROOT=R.parents[2]
sys.path.insert(0,str(ROOT/'experiments/v4_local_search'));from repair_mip import improve
case,kind,backend=sys.argv[1:4];seconds=float(sys.argv[4]);dest=R/'logs/mip_neighbors';dest.mkdir(exist_ok=True)
inp=R/'inputs'/f'dev_{case}.json';incp=R/'logs/baseline280'/f'{case}_711_v4.solution.json';d=json.loads(inp.read_text());inc=json.loads(incp.read_text());n=len(d['sites']);xy=[(s['x'],s['y']) for s in d['sites']]+[(o['x'],o['y']) for o in d['offices']];by={r['officeId']:r for r in inc};ops=sorted(by)
h={o:MultiPoint([xy[n+o]]+[xy[x] for x in by[o]['sites']]).convex_hull for o in ops};pairs=sorted(itertools.combinations(ops,2),key=lambda p:(h[p[0]].distance(h[p[1]]),p))
if not pairs:raise SystemExit(0)
pair=list(pairs[int(kind)%len(pairs)])
if int(kind)>=2 and len(ops)>2:
 q=min((q for q in ops if q not in pair),key=lambda q:min(h[q].distance(h[p]) for p in pair));pair.append(q)
selected=[x for o in pair for x in by[o]['sites']];old={x for r in inc for x in r['sites']};free=[x for x in range(n) if x not in old]
free.sort(key=lambda x:min(h[o].distance(Point(xy[x])) for o in pair));selected+=free[:max(12,len(selected)//2)]
# No safe region or frozen hull restriction: all selected support sites may change.
result=improve(d,inc,seconds,len(selected),backend,True,selected)
result.update(case=case,kind=kind,neighborhood_offices=pair,input_sha256=hashlib.sha256(inp.read_bytes()).hexdigest(),checkpoint_sha256=hashlib.sha256(incp.read_bytes()).hexdigest(),cpu=sorted(os.sched_getaffinity(0)),python=sys.executable)
p=dest/f'{case}_{kind}_{backend}.json';p.write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k not in ('solution','events','selected')}))
