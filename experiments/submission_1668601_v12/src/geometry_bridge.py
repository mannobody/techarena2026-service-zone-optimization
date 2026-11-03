import json,os,time,sys,subprocess,random,statistics
from pathlib import Path
R=Path(__file__).resolve().parents[1];ROOT=R.parents[1];os.sched_setaffinity(0,{14,15})
def read(p):return json.loads((R/p).read_text())
def save(p,a):(R/p).write_text(json.dumps(a,indent=2))
save('BRIDGE_STATUS.json',dict(stage='waiting_core_long'))
while not(R/'SELECTED.json').exists():time.sleep(1)
s=read('DEVELOPMENT280.json');control=read('logs/development280/results.json');cfg=read('SCREEN20.json')['variants']['geometry'];cp={x['case']:x['affinity']for x in control if x['variant']=='submission'};assert len(cp)==6 and len({tuple(x)for x in cp.values()})==6
s['name']='geometry_bridge280';s['variants']={'geometry':cfg};s['case_affinity']=cp;save('GEOMETRY_BRIDGE280.json',s);save('BRIDGE_STATUS.json',dict(stage='geometry_bridge280'))
with(R/'logs/geometry_bridge280.output').open('x')as f:p=subprocess.run([sys.executable,str(R/'src/run_bridge.py'),str(R/'GEOMETRY_BRIDGE280.json')],cwd=ROOT,stdout=f,stderr=subprocess.STDOUT)
assert p.returncode==0,p.returncode
rows=read('logs/geometry_bridge280/results.json');assert len(rows)==6
base={(x['case'],x['seed']):x for x in control if x['variant']=='submission'};pairs=[]
for a in rows:
 b=base[a['case'],a['seed']];assert a['affinity']==b['affinity'];delta=a['official']-b['official']if a['valid']and b['valid']else None
 if delta is not None:pairs.append(dict(case=a['case'],seed=a['seed'],delta=delta,percent=100*delta/abs(b['official'])if abs(b['official'])>1e-9 else None,base=b['official'],candidate=a['official'],both_success=a['success']and b['success']))
x=[z['percent']for z in pairs if z['percent']is not None];rng=random.Random(717);boot=sorted(statistics.mean(rng.choices(x,k=len(x)))for _ in range(5000))if x else[]
m=dict(pairs=len(pairs),mean_case_percent=statistics.mean(x)if x else None,median=statistics.median(x)if x else None,sd=statistics.stdev(x)if len(x)>1 else 0,worst=min(x,default=None),best=max(x,default=None),wins=sum(z['delta']>1e-7 for z in pairs),ties=sum(abs(z['delta'])<=1e-7 for z in pairs),losses=sum(z['delta']<-1e-7 for z in pairs),case_bootstrap95=[boot[125],boot[4875]]if boot else None)
save('GEOMETRY_BRIDGE_ANALYSIS.json',dict(runs=6,valid=sum(z['valid']for z in rows),success=sum(z['success']for z in rows),metrics=m,pairs=pairs,order_confounded=True,control_source='logs/development280/results.json',interpretation='Exploratory supplemental development; same actual controls reused, not6 additional control runs. Proper randomized independent evaluation follows.'))
rank=read('DEVELOPMENT280_SELECTION.json')['ranking'];rank.append(dict(variant='geometry',operational=all(z['rc']==0 and z['valid']and not z['timeout']and not z['error']and z['wall']<300 for z in rows),mean=m['mean_case_percent'],worst=m['worst'],family='geometry',configuration=cfg))
good=[z for z in rank if z['operational']and z['mean']is not None];qualified=[z for z in good if z['worst']>=-5];good=qualified if qualified else good;winner=max(good,key=lambda z:(z['mean'],z['worst']))
save('SELECTED_FINAL.json',dict(selected=winner,ranking=rank,selected_unix=time.time(),fresh_inputs_exist=(R/'inputs/fresh').exists(),rule='Initial PROTOCOL plus development-only GEOMETRY_LONG_ADDENDUM; three long methods, supplementalgeometry fixed-last; fresh source/config frozen next.'));assert not(R/'inputs/fresh').exists();save('BRIDGE_STATUS.json',dict(stage='complete',selected=winner['variant']));print('final long-development choice',winner['variant'],m,flush=True)
