import hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
d=json.loads((ROOT/'experiments/v4_perturbation/shared/DEV_INPUTS.json').read_text())
cases=['anti','tightA','alphabig','multiskill','cluster','large','huge']
cp={k:f'experiments/v4_perturbation/shared/logs/checkpoint280/{k}_1902_v4.solution.json' for k in cases}
cp['large']='experiments/v4_perturbation/shared/logs/checkpoint60/large_1901_v4.solution.json'
assert all((ROOT/p).exists() for p in cp.values())
src=str((R/'artifacts/main.cpp').relative_to(ROOT));exe=str((R/'artifacts/checkpoint').relative_to(ROOT))
variants={k:dict(binary=exe,source=src,mode=i,env={'DBG':'1','ESCAPE_MODE':'0','XN_SIG_FIX':'0'})
 for i,k in [(0,'boundary'),(1,'geometry'),(2,'structure'),(3,'mixed'),(4,'lns')]}
spec=dict(destination=str((R/'logs/checkpoint_screen').relative_to(ROOT)),seconds=2,seeds=[3101,3102],cpu_pairs=[[18,19]],
 cases={k:d[k]['path'] for k in cases},checkpoints=cp,variants=variants,order_seed=20261020)
(R/'CHECKPOINT_SPEC.json').write_text(json.dumps(spec,indent=2))
print('70 checkpoint processes, TL2; known development inputs, not holdout.')
