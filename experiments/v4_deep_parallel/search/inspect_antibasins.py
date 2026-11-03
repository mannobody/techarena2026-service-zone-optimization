"""Offline final-geometry inspection; never linked into solver."""
import json,math
from pathlib import Path
from shapely.geometry import Point,MultiPoint
R=Path(__file__).resolve().parent;I=json.loads((R/'inputs/anti.json').read_text());P=[Point(z['x'],z['y']) for z in I['sites']];off=[Point(z['x'],z['y']) for z in I['offices']];allP=P+off;rows=[];assign=[]
for seed in [1101,1102]:
 sol=json.loads((R/f'logs/screen60/anti_{seed}_v4.solution.json').read_text());asg=[-1]*len(P)
 for z in sol:
  for x in z['sites']:asg[x]=z['officeId']
 zones=[]
 for z in sol:
  o=z['officeId'];ids=z['sites'];h=MultiPoint([P[x] for x in ids]+[off[o]]).convex_hull;cover=[i for i,p in enumerate(allP) if h.covers(p)]
  blocked=[i for i in cover if i<len(P) and asg[i]<0]
  zones.append({'office':o,'assigned':len(ids),'task_load':sum(len(I['sites'][i]['tasks']) for i in ids),'hull_area':h.area,'hull_perimeter':h.length,'covered_input_points':len(cover),'unassigned_sites_inside':len(blocked),'their_positive_profit_sum':sum(max(0,I['sites'][i]['reward']-I['distances'][o][i]) for i in blocked)})
 rows.append({'seed':seed,'zones':zones,'assigned_total':sum(a>=0 for a in asg),'hull_area_sum':sum(z['hull_area'] for z in zones),'unassigned_covered_sum':sum(z['unassigned_sites_inside'] for z in zones)})
 assign.append(asg)
a,b=assign;both=[i for i in range(len(P)) if a[i]>=0 and b[i]>=0]
change={'only_first':sum(x>=0 and y<0 for x,y in zip(a,b)),'only_second':sum(x<0 and y>=0 for x,y in zip(a,b)),'reassigned_between_offices':sum(a[i]!=b[i] for i in both),'same_office':sum(a[i]==b[i] for i in both)}
(R/'ANTI_GEOMETRY.json').write_text(json.dumps({'solutions':rows,'assignment_difference':change},indent=2));print(json.dumps({'totals':[{k:v for k,v in x.items() if k!='zones'} for x in rows],'difference':change},indent=2))
