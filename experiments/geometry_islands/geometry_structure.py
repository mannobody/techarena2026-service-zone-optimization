from pathlib import Path
import json,math,itertools,importlib.util
from shapely.geometry import MultiPoint,Point
H=Path(__file__).resolve().parent;R=H.parents[1]
spec=importlib.util.spec_from_file_location('validator',R/'task/validate_solution.py');V=importlib.util.module_from_spec(spec);spec.loader.exec_module(V)
out=[]
for k in [2,3,4,6,12]:
 # Distinct points on a strictly convex parabola avoids floating circle coincidences.
 pts=[(float(i),float(i*i)) for i in range(2*k)]
 # Pairs i,i+k alternate on the convex boundary, so every pair of segments crosses.
 data=dict(sites=[dict(x=x,y=y,reward=10,tasks=[]) for x,y in pts[k:]],offices=[dict(x=x,y=y,cost=0,maxSize=1) for x,y in pts[:k]],workers=[],distances=[[0 if i==j else 100 for j in range(k)] for i in range(k)],maxDifference=0,balanceCoefficient=0)
 sol=[dict(officeId=i,sites=[i],workers=[]) for i in range(k)]
 p=H/'data'/f'crossing_family_{k}.json';p.write_text(json.dumps(data));q=H/'data'/f'crossing_family_{k}.solution.json';q.write_text(json.dumps(sol));score=V.validate(p,q)
 hulls=[MultiPoint([pts[i],pts[i+k]]).convex_hull for i in range(k)];cross=sum(hulls[i].crosses(hulls[j]) for i in range(k) for j in range(i));assert cross==k*(k-1)//2 and score==10*k
 out.append(dict(k=k,validator_score=score,pairwise_crossings=cross,full_plane_convex_partition_upper_bound=10,ratio=k))
profiles=[]
for p in sorted((H/'data/train').glob('*.json')):
 d=json.loads(p.read_text());xy=[(s['x'],s['y']) for s in d['sites']+d['offices']];h=MultiPoint(xy).convex_hull;extreme=len(h.exterior.coords)-1 if h.geom_type=='Polygon' else len(h.coords)
 profiles.append(dict(case=p.stem,n=len(d['sites']),offices=len(d['offices']),extreme_points=extreme,extreme_fraction=extreme/len(xy)))
(H/'logs/geometry_structure.json').write_text(json.dumps(dict(crossing_family=out,profiles=profiles),indent=2));print(out);print(profiles)
