import json
from pathlib import Path
R=Path(__file__).resolve().parents[1];ROOT=R.parents[1];rel=lambda p:str(p.relative_to(ROOT))
d=json.loads((ROOT/'experiments/v4_perturbation/shared/DEV_INPUTS.json').read_text())
src=rel(R/'artifacts/candidate_v2/main.cpp');exe=rel(R/'artifacts/candidate_v2/solution')
env={'DBG':'1','ESCAPE_MODE':'5','XN_SIG_FIX':'0','XN_FILL':'0','XN_MODE':'0'}
variants={'v4':dict(binary=rel(R/'artifacts/v4'),source='experiments/v4_local_search/baseline/frozen_v4.cpp',env={'DBG':'1'}),
    'v8':dict(binary=rel(R/'artifacts/v8'),source=rel(R/'src/frozen_v8.cpp'),env={'DBG':'1'}),
    'off':dict(binary=exe,source=src,env=env),
    'fill':dict(binary=exe,source=src,env=env|{'XN_FILL':'1'}),
    'packet':dict(binary=exe,source=src,env=env|{'XN_MODE':'4'}),
    'exact':dict(binary=exe,source=src,env=env|{'XN_MODE':'3'})}
spec=dict(destination=rel(R/'logs/full_dev4'),seconds=4,seeds=[3201,3202],cpu_pairs=[[18,19],[20,21]],
    cases={k:v['path'] for k,v in d.items()},variants=variants,order_seed=20261021,snapshots=[1,2,3])
(R/'FULL_DEV4.json').write_text(json.dumps(spec,indent=2))
print('144 processes, TL4, 12 known inputs x 2 seeds x 6 variants; two disjoint CPU pairs.')
