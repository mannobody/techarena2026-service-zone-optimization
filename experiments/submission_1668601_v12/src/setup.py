from pathlib import Path
import hashlib,json,os
R=Path(__file__).resolve().parents[1];ROOT=R.parents[1];os.sched_setaffinity(0,{14,15})
cpus=[[0,1],[3,6],[8,10],[12,13],[16,17],[18,19],[20,21]]
variants={'submission':dict(binary=str((R/'baseline/solution').relative_to(ROOT)))}
for n in ['hybrid','plateau','exact','zones','geometry']:
 variants[n]=dict(binary=str((R/'artifacts'/n/'candidate').relative_to(ROOT)))
variants['zones']['env']={'ZM_POOL':'0','ZM_RESERVE':'0'}
variants['zones_pool']=dict(binary=variants['zones']['binary'],env={'ZM_POOL':'1','ZM_RESERVE':'1'})
variants['geometry']['env']={'GW_MODE':'1','ZM_POOL':'0','ZM_RESERVE':'0'}
variants['geometry_diverse']=dict(binary=variants['geometry']['binary'],env={'GW_MODE':'2','ZM_POOL':'0','ZM_RESERVE':'0'})
variants['exact']['env']={'XN_MODE':'1','XN_FILL':'2','XN_WORKER':'1','ESCAPE_MODE':'0'}
variants['certified']=dict(binary=str((R/'artifacts/certified/candidate').relative_to(ROOT)))
cases={f'jury{i}':f'task/instance{i}/instance.json'for i in [1,4]}
for n in ['euclid240','road200','anti220','equal180','grid180','multi260','cluster500','huge10000']:cases[n]=f'experiments/adaptive_v11/inputs/dev/{n}.json'
s=dict(name='screen20',seconds=20,seeds=[0],cpus=cpus,cases=cases,variants=variants)
(R/'SCREEN20.json').write_text(json.dumps(s,indent=2))
family={n:n for n in variants};family.update(geometry_diverse='geometry',zones_pool='zones')
plan=dict(control='submission',original_archive='/home/user/Downloads/submit_1668601.zip',baseline_source_sha256='4144e63be49b938ca4885562dfd87bfdec78e46c8b3bd2ee9d32907997ff7bee',all_previous_inputs_are_development=True,initial_screen=dict(seconds=20,seeds=[0],general_inputs=10,variants=9),families=family,selection='Among operational candidates choose highest equal-case mean vs submission, prefer worst>=-5% if any. Select second from a different family. Short ranking is development only. Then compare both selected candidates and submission atTL280 on6 viewed classes/seed12602. Choose operational highest equal-case mean, same worst>=-5 preference. No candidate code changes after independent freeze.',long_development=dict(seconds=280,seeds=[12602],cases=['jury1','anti220','equal180','grid180','multi260','huge10000']),independent=dict(seconds=280,seeds=[0,12702],input_seed_offset=1400000,inputs=7,variants=['submission','selected']),promotion='All28 operational/VALID, rc0/no timeout/error/wall<300; equal-case mean positive; bootstrap95 lower>0; worst pair>=-1%. Otherwise experimental. No input-name/hash/seed routing.',resources='Matched(case,seed) sequential variants randomized on same pair of physical CPUs; GNUtime,/proc/PSI/RSS/checkpoints;7 disjoint slots, controller14/15. No exclusive-machine claim. No other quality experiment active. HiGHS default absent; main measurements portable mode with no LD override. Separately test optional existing HiGHS ABI without mixing labels.',preservation='All files and outcomes retained; no deletion/commit/push/submit; previous solver/user files and exactv4 remain unchanged. All candidate ports preserve submission MIP header and hooks, independently verified by roundtrip. Runtime instance→solution only; no cross-run starts.')
(R/'PROTOCOL.json').write_text(json.dumps(plan,indent=2))
# New instrumented runner, same full resource/validator accounting.
t=(ROOT/'experiments/adaptive_v11/src/run_instrumented.py').read_text();a=t.index("if spec['name']=='acceleration280'");b=t.index("dest=R/'logs'",a);t=t[:a]+t[b:];(R/'src/run.py').write_text(t)
t=(ROOT/'experiments/adaptive_v11/src/analysis.py').read_text().replace("['v4','v10']","['submission']");(R/'src/analyze.py').write_text(t)
(R/'src/live.py').write_text((ROOT/'experiments/adaptive_v11/src/live.py').read_text())
print('Protocol:90 short screen +18 long development +28 fresh confirmation runs')
