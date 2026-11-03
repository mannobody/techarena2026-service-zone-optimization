import json,hashlib,shutil,sys,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];ROOT=R.parents[1];sys.path.insert(0,str(ROOT/'tools'));import gen
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
protocol=dict(task='Input-feature and online adaptive solver portfolio',controls=dict(v4='experiments/v4_local_search/baseline/frozen_v4.cpp',v4_sha256='5b3914fa9791cb879f3232fb2876a915de83b848ad4b353b0dbf25b574998c25',geometry='experiments/warm_v10/artifacts/v5/main.cpp'),historical='All previous inputs/results, including former holdouts, are development. Local checkpoint operators and different TL are not merged into full TL280 labels.',classification='Dimensionless physical features; leave entire instance+all seeds out in development diagnostics. Static tree failed to beat constant geometry; no runtime input hash/id/file-name/seed routing.',new_method='Two native experts on one compute worker each, common best verified publisher, optional in-invocation incumbent exchange; race observed at .40TL or .55TL for ns>2000/pressure>1/negative geo correlation. Promote only if >2% objective gap and observed slope projection also favors leader; otherwise preserve both. Cancellation precedes second-worker start.',screen=dict(seconds=45,seeds=[0],variants=['v4','v10','dual','race','race_no_share']),selection='Among operationally valid portfolio configurations choose greatest mean improvement over v10 on screen, prefer worst>=-5% vs v4 if any. This is a short-budget development screen. Confirm full TL280, two seeds, fixed8-case subset with both controls. No fresh inputs before selection/freeze. If long development has material implementation failures repair on development only, retain all revisions; do not call short score confirmation.',development=dict(seconds=280,seeds=[0,11602],cases=['euclid240','anti220','equal180','grid180','multi260','cluster500','road1600','huge10000']),independent=dict(seconds=280,seeds=[0,11702,11703],input_seed_offset=1300000,count=8),promotion='100% candidate valid, rc0, no emergency/error, wall<300; equal-case means>0 vs exactv4 and geometryv10; case-bootstrap95 lower>0 vs v4; worst pair vs v4>=-1%. Otherwise candidate experimental. All primary rows preserved; fixed-seed wall scheduling does not guarantee bitwise answers.',resources='Matched (case,seed) same two CPU affinity, randomized variant order, GNUtime and /proc thread runqueue/runtime plus PSI snapshots. 5 slots distinct physical cores, controller14/15. No exclusive-machine claim. If primary promotion passes but CPU/wall range>.5 in a matched block, one predeclared viewed-case repeat on largest-disparity case, same3seeds/all3versions/3slots may veto on worst<-1% vs v4 or any operational failure; never replace primary.',preservation='New directory only, no removal, no staging/commit/push/submit. Source versions and canceled/failed logs retained. Read only current instance/write only solution in packaged runtime.')
(R/'PROTOCOL.json').write_text(json.dumps(protocol,indent=2))
params=[
 ('tiny12',dict(ns=12,no=4,nw=7,nsk=3,A=1,af=.3,wsk=2)),
 ('euclid240',dict(ns=240,no=9,nw=28,nsk=4,A=5,af=.02)),
 ('road200',dict(ns=200,no=8,nw=24,nsk=4,A=3,af=.02,dist='road',tmax=5)),
 ('anti220',dict(ns=220,no=10,nw=30,nsk=5,A=4,af=.01,dist='anti',offices='perimeter')),
 ('equal180',dict(ns=180,no=9,nw=24,nsk=4,A=0,af=.7,tmax=7,wsk=2)),
 ('balance300',dict(ns=300,no=10,nw=30,nsk=5,A=12,af=3,tmax=6,span=1,dscale=10000)),
 ('grid180',dict(ns=180,no=10,nw=28,nsk=4,A=1,af=.15,layout='grid',offices='onsite',wsk=2,tmax=4)),
 ('multi260',dict(ns=260,no=12,nw=15,nsk=7,A=5,af=.03,dist='road',wsk=3,deficit=2,tmax=5)),
 ('cluster500',dict(ns=500,no=12,nw=32,nsk=5,A=10,af=0,layout='cluster',span=1,dscale=10000)),
 ('capacity240',dict(ns=240,no=9,nw=24,nsk=4,A=0,af=.05,capf=.45)),
 ('free500',dict(ns=500,no=15,nw=35,nsk=5,A=500,af=0,capf=2)),
 ('manhattan350',dict(ns=350,no=11,nw=26,nsk=4,A=4,af=.05,dist='manhattan',offices='perimeter')),
 ('road1600',dict(ns=1600,no=18,nw=48,nsk=7,A=20,af=.015,dist='road',tmax=4)),
 ('large3000',dict(ns=3000,no=20,nw=56,nsk=6,A=35,af=.02)),
 ('huge10000',dict(ns=10000,no=24,nw=64,nsk=6,A=100,af=.01,tmax=3)),
 ('sparse300',dict(ns=300,no=12,nw=18,nsk=6,A=2,af=.08,deficit=3,capf=.7,tmax=5)),
]
d=R/'inputs/dev';d.mkdir(exist_ok=False);rows={}
for i,(name,kw)in enumerate(params):
 p=d/(name+'.json');gen.gen2(1200000+i,str(p),**kw);rows[name]=dict(path=str(p.relative_to(ROOT)),sha256=sha(p),seed=1200000+i,parameters=kw)
(R/'DEV_INPUTS.json').write_text(json.dumps(rows,indent=2))
# The independent design is fixed now; no fresh input is generated here.
fresh=[
 ('euclid310',dict(ns=310,no=11,nw=32,nsk=5,A=6,af=.03)),
 ('road230',dict(ns=230,no=9,nw=26,nsk=5,A=3,af=.025,dist='road',tmax=5)),
 ('anti270',dict(ns=270,no=12,nw=36,nsk=5,A=5,af=.02,dist='anti')),
 ('equal210',dict(ns=210,no=10,nw=26,nsk=4,A=0,af=.8,wsk=2,tmax=7)),
 ('grid240',dict(ns=240,no=12,nw=32,nsk=4,A=1,af=.18,layout='grid',offices='onsite',tmax=4,wsk=2)),
 ('multi330',dict(ns=330,no=13,nw=18,nsk=7,A=5,af=.04,dist='road',tmax=5,wsk=3,deficit=2)),
 ('road1900',dict(ns=1900,no=20,nw=52,nsk=7,A=24,af=.02,dist='road',tmax=4)),
 ('huge9000',dict(ns=9000,no=26,nw=68,nsk=6,A=90,af=.015,tmax=3)),
]
(R/'INDEPENDENT_PLAN.json').write_text(json.dumps(dict(parameters=fresh,seed_offset=1300000,seeds=[0,11702,11703],seconds=280,generator_sha256=sha(Path(gen.__file__))),indent=2))
# Preserve the previously instrumented runner while changing only experiment root by file placement.
shutil.copy2(ROOT/'experiments/warm_v10/src/run_instrumented.py',R/'src/run_instrumented.py')
shutil.copy2(ROOT/'experiments/warm_v10/src/analysis.py',R/'src/analysis.py')
shutil.copy2(ROOT/'experiments/warm_v10/src/live.py',R/'src/live.py')
variants=dict(v4=dict(binary='experiments/structural_v9/artifacts/v4'),v10=dict(binary='experiments/warm_v10/artifacts/v5/candidate',env=dict(ZM_POOL='0',ZM_RESERVE='0',GW_MODE='1')))
for name,policy,share in [('dual',0,1),('race',1,1),('race_no_share',1,0)]:variants[name]=dict(binary='experiments/adaptive_v11/artifacts/v2/candidate',env=dict(AP_POLICY=str(policy),AP_SHARE=str(share)))
spec=dict(name='screen45_v2',seconds=45,seeds=[0],cpus=[[0,1],[12,13],[16,17],[18,19],[20,21]],cases={k:v['path']for k,v in rows.items()},variants=variants)
(R/'SCREEN45_V2.json').write_text(json.dumps(spec,indent=2))
print(json.dumps(dict(development_inputs=len(rows),planned_fresh=len(fresh),screen_runs=len(rows)*len(variants))))
