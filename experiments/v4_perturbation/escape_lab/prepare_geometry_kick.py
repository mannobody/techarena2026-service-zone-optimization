from pathlib import Path
import json,time,hashlib,subprocess,shutil
lab=Path(__file__).resolve().parent;root=lab.parents[2];dev=json.loads((root/'experiments/v4_perturbation/shared/DEV_INPUTS.json').read_text())
# A late preregistration clarification requests isolated kick RNG. Preserve the
# not-yet-benchmarked preliminary compile, then rebuild exact current inputs.
shutil.copy2(lab/'bin/post_geometry_kick',lab/'bin/post_geometry_kick_pre_rng_unbenchmarked')
with (lab/'logs/build_geometry_kick_rng_final.log').open('w') as log:
 subprocess.run(['taskset','-c','14,15','g++','-O3','-std=c++17','-pthread',str(lab/'src/post_geometry_kick.cpp'),'-o',str(lab/'bin/post_geometry_kick')],stderr=log,check=True)
s=json.loads((lab/'SCREEN60.json').read_text());classes=['anti','tightA','alphabig','multiskill','huge','cluster'];s.update(destination=str((lab/'logs/geometry_kick60').relative_to(root)),seeds=[2701,2702],order_seed=871066)
s['cases']={c:dev[c]['path'] for c in classes};s['checkpoints']={c:f'experiments/v4_perturbation/shared/logs/checkpoint60/{c}_1901_v4.solution.json' for c in classes}
s['variants']={'v4':{'binary':str((lab/'bin/post_repeat_v4').relative_to(root)),'source':str((lab/'src/post_repeat_v4.cpp').relative_to(root)),'mode':0,'env':{'DBG':'1'}},**{k:{'binary':str((lab/'bin/post_geometry_kick').relative_to(root)),'source':str((lab/'src/post_geometry_kick.cpp').relative_to(root)),'mode':m,'env':{'DBG':'1'}}for k,m in [('off',0),('geometry_kick',5)]}}
(lab/'GEOMETRY_KICK60.json').write_text(json.dumps(s,indent=2))
paths=[lab/'src/escape_geometry_kick.h',lab/'src/geometry_perturb_only_v1.h',lab/'src/geometry_kick_v4.cpp',lab/'src/post_geometry_kick.cpp',lab/'bin/post_geometry_kick',lab/'src/escape.h',lab/'src/escape_v4.cpp',lab/'bin/post_repeat_v4',lab/'src/post_repeat_v4.cpp',root/'experiments/v4_perturbation/shared/checkpoint.h']
(lab/'FREEZE_GEOMETRY_KICK.json').write_text(json.dumps({'time':time.time(),'files':{str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}},indent=2))
