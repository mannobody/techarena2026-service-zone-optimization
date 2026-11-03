import json
from pathlib import Path
R=Path(__file__).resolve().parent;ROOT=R.parents[2];SH=R.parent/'shared'
inputs=json.loads((SH/'DEV_INPUTS.json').read_text())
for suffix,cases,seed in [('60',['anti','tightA','alphabig','multiskill','cluster','grid','large','huge'],1901),('280',['anti','tightA','alphabig','multiskill','cluster','huge'],1902)]:
 spec={'destination':str((R/'logs'/('screen'+suffix)).relative_to(ROOT)),'seconds':4,'cpu_pairs':[[12,13]],'seeds':[2101,2102],
 'cases':{c:inputs[c]['path'] for c in cases},'checkpoints':{c:str((SH/'logs'/('checkpoint'+suffix)/f'{c}_{seed}_v4.solution.json').relative_to(ROOT)) for c in cases},
 'variants':{name:{'binary':str((R/'post_geometry').relative_to(ROOT)),'source':str((R/'src/post_geometry.cpp').relative_to(ROOT)),'env':{},'mode':mode}for name,mode in [('lns',0),('packet',1),('support',2),('cycle',3),('polish',4)]}}
 (R/('SCREEN'+suffix+'.json')).write_text(json.dumps(spec,indent=2))
