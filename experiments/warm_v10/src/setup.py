import hashlib,json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
old=ROOT/'experiments/structural_v9';tail={'ZM_POOL':'0','ZM_RESERVE':'0','DBG':'1'}
for f in ['run.py','summarize.py']:
    p=R/'src'/f
    assert not p.exists()
    s=(old/'src'/f).read_text()
    if f=='run.py':s=s.replace("[.25,.50,.85]","[.10,.22,.25,.50,.85]")
    p.write_text(s)
dev=json.loads((old/'DEV_INPUTS.json').read_text())
cases={k:dev[k]['path']for k in ['medium_road','medium_anti','medium_A0','medium_multi','cluster_alpha0','grid_boundary','large','huge']}
cases|={'official_3':'task/instance3/instance.json','official_4':'task/instance4/instance.json'}
variants={
 'v4':{'binary':'experiments/structural_v9/artifacts/v4','env':{'DBG':'1'}},
 'v9':{'binary':'experiments/structural_v9/artifacts/final_research/candidate','env':tail},
 'geometry':{'binary':'experiments/warm_v10/artifacts/v1/candidate','env':tail|{'GW_MODE':'1','GW_TRACE':'1'}},
 'memetic':{'binary':'experiments/warm_v10/artifacts/v1/candidate','env':tail|{'GW_MODE':'2','GW_TRACE':'1'}}}
cpus=[[0,1],[3,6],[8,10],[12,13],[16,17],[18,19],[20,21]]
spec=dict(name='screen30_v1',seconds=30,seeds=[10101,10102],cpus=cpus,cases=cases,variants=variants)
(R/'SCREEN30_V1.json').write_text(json.dumps(spec,indent=2))
spec['name']='screen60_v1';spec['seconds']=60;spec['seeds']=[10201,10202]
(R/'SCREEN60_V1.json').write_text(json.dumps(spec,indent=2))
files=[ROOT/'experiments/v4_local_search/baseline/frozen_v4.cpp',old/'artifacts/final_research/main.cpp',old/'artifacts/final_research/candidate',old/'artifacts/v4',ROOT/'CLAUDE.md',ROOT/'EXPERIMENTS.md']
(R/'PROVENANCE.json').write_text(json.dumps({str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()for p in files},indent=2))
(R/'PROTOCOL.json').write_text(json.dumps(dict(
 objective='Improve v9 warm start, retaining exact server v4 control',
 development='Previously viewed v9 development and holdout are development here; none will be relabelled independent.',
 screen='NT2 / matched affinity pairs / identical seed and total TL. Full solver, includes warm construction.',
 new_methods=['Geometry genomes h/G plus inherited assignment centroids, true feasible fitness, two independent warm lanes, direct feasible transfer','Spatial whole-zone atomic crossover, memetic local search and assignment-diverse elite archive'],
 independent='Freeze selected code and configuration before creating fresh inputs. New seed offset 1080000. Three seeds 10501,10502,10503, TL280. v4, v9, selected variant.',
 independent_cases=['road120','anti180','equal_count150','multi220','cluster400','grid160','road1500','huge10000'],
 selection='After short screen and development TL280. Prioritize no invalids/timeouts; improvement over v9 and v4 on equal-weight inputs, inspect worst losses. No quality tuning after independent data generation.',
 promotion='Independent mean >0 vs both controls; case-bootstrap 95 lower >0 vs v4; worst pair >=-1% vs v4; 100% candidate valid and below contest 300 sec. Otherwise experimental, report all outcomes.',
 preservation='All revisions and outputs retained in new directory. No prior artifact rewritten; no deletions.',
 ),indent=2))
print(json.dumps(dict(cases=len(cases),runs=80)))
