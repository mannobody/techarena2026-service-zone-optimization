import json
from oracle import R,ROOT
src=str((R/'artifacts/candidate_v2/main.cpp').relative_to(ROOT));exe=str((R/'artifacts/candidate_v2/checkpoint').relative_to(ROOT))
variants={k:dict(binary=exe,source=src,mode=mode,env={'DBG':'1','XN_FILL':fill,'XN_MODE':'0','ESCAPE_MODE':'0','XN_SIG_FIX':'0'})
    for k,mode,fill in [('native_fill',5,'0'),('full_fill',5,'1'),('native_open',6,'0'),('packets',4,'0'),('exact',2,'0')]}
cases=['fill_geo_fallback','negative_profit_balance','large_A0_open','joint_open_workers','joint_exchange']
spec=dict(destination=str((R/'logs/barriers').relative_to(ROOT)),seconds=1,seeds=[3111],cpu_pairs=[[18,19]],
    cases={k:str((R/'inputs'/f'{k}.json').relative_to(ROOT)) for k in cases},
    checkpoints={k:str((R/'solutions'/f'{k}.json').relative_to(ROOT)) for k in cases},variants=variants,order_seed=791)
(R/'BARRIER_SPEC.json').write_text(json.dumps(spec,indent=2))
print('25 short operator tests saved.')
