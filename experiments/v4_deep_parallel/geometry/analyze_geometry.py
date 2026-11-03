import json,sys,itertools,collections,hashlib
from pathlib import Path
import numpy as np,shapely
from shapely import MultiPoint,Point
R=Path(__file__).resolve().parent;ROOT=R.parents[2]
case=sys.argv[1];src=R/'logs/baseline280';ip=R/'inputs'/f'dev_{case}.json';sp=src/f'{case}_711_v4.solution.json'
d=json.loads(ip.read_text());sol=json.loads(sp.read_text());n=len(d['sites']);xy=np.array([(s['x'],s['y']) for s in d['sites']]+[(o['x'],o['y']) for o in d['offices']]);points=shapely.points(xy);ops=[r['officeId'] for r in sol];by={r['officeId']:r for r in sol};owner={x:r['officeId'] for r in sol for x in r['sites']};A=d['maxDifference']
hulls={o:MultiPoint(xy[[n+o]+by[o]['sites']]).convex_hull for o in ops};coverage={o:np.asarray(shapely.covers(h,points)) for o,h in hulls.items()}
states=[]
for o,r in by.items():
 states.append(dict(office=o,count=len(r['sites']),load=sum(len(d['sites'][x]['tasks']) for x in r['sites']),capacity=d['offices'][o]['maxSize'],hull_vertices=len(hulls[o].exterior.coords)-1 if hulls[o].geom_type=='Polygon' else len(hulls[o].coords),free_covered=sum(bool(coverage[o][x]) for x in range(n) if x not in owner)))
pair=[]
for a,b in itertools.combinations(ops,2):
 other=[len(by[o]['sites']) for o in ops if o not in (a,b)];lim=min(other)+A if other else n
 pair.append(dict(a=a,b=b,distance=hulls[a].distance(hulls[b]),polygon_intersects=hulls[a].intersects(hulls[b]),shared_input_points=int(np.sum(coverage[a]&coverage[b])),count_cap=[min(d['offices'][o]['maxSize'],lim) for o in (a,b)],capacity_reduction=sum(max(0,d['offices'][o]['maxSize']-lim) for o in (a,b))))
edges=[]
for x in range(n):
 if x in owner:continue
 for o in ops:
  profit=d['sites'][x]['reward']-d['distances'][o][x]
  if profit>0:edges.append((profit,x,o))
edges.sort(reverse=True);targets=[]
for profit,x,o in edges[:100]:
 h=MultiPoint(xy[[n+o]+by[o]['sites']+[x]]).convex_hull;cov=np.asarray(shapely.covers(h,points));blocks=[]
 for q in ops:
  if q==o:continue
  overlap=np.flatnonzero(cov&coverage[q]);
  if len(overlap):blocks.append(dict(office=q,points=len(overlap),contains_anchor=bool(cov[n+q])))
 targets.append(dict(site=x,office=o,profit=profit,blocking_zones=blocks,already_covered=[q for q in ops if coverage[q][x]]))
summary=dict(case=case,sites=n,opened=len(ops),A=A,alpha=d['balanceCoefficient'],states=states,pairs=pair,top_free_insertions=targets,input_sha256=hashlib.sha256(ip.read_bytes()).hexdigest(),checkpoint_sha256=hashlib.sha256(sp.read_bytes()).hexdigest(),aggregate=dict(cap_reduced_pairs=sum(p['capacity_reduction']>0 for p in pair),crossing_hull_pairs=sum(p['polygon_intersects'] for p in pair),top_free=len(targets),unblocked=sum(not t['blocking_zones'] for t in targets),anchor_blocked=sum(any(b['contains_anchor'] for b in t['blocking_zones']) for t in targets),blocking_zone_hist=dict(collections.Counter(len(t['blocking_zones']) for t in targets))))
(R/'logs'/f'geometry_{case}.json').write_text(json.dumps(summary,indent=2));print(case,summary['aggregate'])
