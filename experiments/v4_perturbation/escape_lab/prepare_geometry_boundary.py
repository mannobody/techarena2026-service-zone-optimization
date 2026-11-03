from pathlib import Path
import json,time,hashlib
lab=Path(__file__).resolve().parent;root=lab.parents[2]
s=json.loads((lab/'GEOMETRY_KICK60.json').read_text());s.update(destination=str((lab/'logs/geometry_boundary60').relative_to(root)),cpu_pairs=[[14,15],[18,19]],order_seed=871088)
s['variants']={k:dict(v) for k,v in s['variants'].items() if k=='v4'}
for k,m in [('off',0),('retain',4),('geometry_boundary',5),('boundary_only',6)]:s['variants'][k]={'binary':str((lab/'bin/post_geometry_boundary').relative_to(root)),'source':str((lab/'src/post_geometry_boundary.cpp').relative_to(root)),'mode':m,'env':{'DBG':'1'}}
(lab/'GEOMETRY_BOUNDARY60.json').write_text(json.dumps(s,indent=2))
paths=[lab/'src/escape_geometry_boundary.h',lab/'src/geometry_boundary_v4.cpp',lab/'src/post_geometry_boundary.cpp',lab/'src/geometry_perturb_only_v1.h',lab/'bin/post_geometry_boundary',lab/'bin/post_repeat_v4',lab/'src/post_repeat_v4.cpp',root/'experiments/v4_perturbation/shared/checkpoint.h']
(lab/'FREEZE_GEOMETRY_BOUNDARY.json').write_text(json.dumps({'time':time.time(),'files':{str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}},indent=2))
