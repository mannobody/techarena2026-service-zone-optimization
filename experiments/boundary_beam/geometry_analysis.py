import json
from pathlib import Path
from shapely import MultiPoint,Point
from bench import H
rows=[]
for r in json.loads((H/'logs/post_v2/results.json').read_text()):
 if r['method']!=1 or r['q']!=24:continue
 data=json.loads(Path(r['input']).read_text());base=json.loads((H/'logs/screen_v1'/f"{r['case']}_1_base.json").read_text());end=json.loads(Path(r['solution']).read_text())
 owner={s:o['officeId'] for o in base for s in o['sites']};new={s:o['officeId'] for o in end for s in o['sites']}
 xy=lambda p:(p['x'],p['y'])
 hull={o['officeId']:MultiPoint([xy(data['sites'][s]) for s in o['sites']]+[xy(data['offices'][o['officeId']])]).convex_hull for o in base}
 changed=[s for s in set(owner)|set(new) if owner.get(s,-1)!=new.get(s,-1)]
 expanded=[s for s in changed if s in new and not hull[new[s]].covers(Point(xy(data['sites'][s])))]
 transfers=[s for s in changed if s in owner and s in new]
 rows.append(dict(case=r['case'],seed=r['seed'],before=r['stats']['before'],after=r['score'],changed_sites=len(changed),transfers=len(transfers),new_sites=sum(s not in owner for s in changed),removed_sites=sum(s not in new for s in changed),outside_previous_hulls=len(expanded),expanded_site_ids=expanded))
(H/'logs/geometry_changes.json').write_text(json.dumps(rows,indent=2))
print('improved',sum(r['after']>r['before']+1e-5 for r in rows),'of',len(rows),'expanded',sum(bool(r['outside_previous_hulls']) for r in rows),'transferred',sum(bool(r['transfers']) for r in rows))
for r in rows:print(r['case'],r['seed'],r['changed_sites'],r['transfers'],r['outside_previous_hulls'])
