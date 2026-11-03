from pathlib import Path
import json,time,hashlib
lab=Path(__file__).resolve().parent;root=lab.parents[2]
s=json.loads((lab/'MATURE280.json').read_text());s.update(destination=str((lab/'logs/repeat280').relative_to(root)),seeds=[2601,2602],order_seed=871055)
v={}
for k,m in [('v4',0),('off',0),('retain',4),('tabu',3)]:
 suffix='v4' if k=='v4' else 'escape';v[k]={'binary':str((lab/f'bin/post_repeat_{suffix}').relative_to(root)),'source':str((lab/f'src/post_repeat_{suffix}.cpp').relative_to(root)),'mode':m,'env':{'DBG':'1'}}
s['variants']=v;(lab/'REPEAT280.json').write_text(json.dumps(s,indent=2))
paths=[lab/'src/post_repeat_v4.cpp',lab/'src/post_repeat_escape.cpp',lab/'src/escape.h',lab/'src/escape_v4.cpp',lab/'bin/post_repeat_v4',lab/'bin/post_repeat_escape',root/'experiments/v4_perturbation/shared/checkpoint.h',root/'experiments/v4_local_search/baseline/frozen_v4.cpp']
(lab/'FREEZE_REPEAT.json').write_text(json.dumps({'time':time.time(),'files':{str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}},indent=2))
