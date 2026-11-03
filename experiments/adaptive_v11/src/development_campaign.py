import json,subprocess,sys,time,os,statistics
from pathlib import Path
R=Path(__file__).resolve().parents[1];ROOT=R.parents[1];os.sched_setaffinity(0,{14,15})
def stage(name,**extra):(R/'DEVELOPMENT_STATUS.json').write_text(json.dumps(dict(stage=name,updated_unix=time.time(),**extra),indent=2))
stage('waiting_screen_and_oracle')
while not (R/'SCREEN_STATUS.json').exists()or not (R/'logs/specialists_v3/results.json').exists():time.sleep(1)
q=json.loads((R/'logs/specialists_v3/results.json').read_text());assert len(q)==84 and all(x['valid']and x['rc']==0 for x in q)
a=json.loads((R/'logs/screen45_v2/ANALYSIS.json').read_text());spec=json.loads((R/'SCREEN45_V2.json').read_text());rows=json.loads((R/'logs/screen45_v2/results.json').read_text())
rank=[]
for name in ['dual','race','race_no_share']:
 ps=[x for x in rows if x['variant']==name]
 valid=all(x['valid']and x['rc']==0 and not x['timeout']and not x['error']and x['wall']<300 for x in ps)
 b=a['comparisons'][name+'_vs_v4']['all_valid'];c=a['comparisons'][name+'_vs_v10']['all_valid']
 rank.append(dict(variant=name,operational=valid,mean_vs_v10=c['mean_case_percent'],mean_vs_v4=b['mean_case_percent'],worst_vs_v4=b['worst'],env=spec['variants'][name]['env']))
assert any(x['operational']for x in rank)
qualified=[x for x in rank if x['operational']and x['worst_vs_v4']>=-5]
if not qualified:qualified=[x for x in rank if x['operational']]
selected=max(qualified,key=lambda x:(x['mean_vs_v10'],x['worst_vs_v4']))
(R/'SCREEN_SELECTION.json').write_text(json.dumps(dict(selected=selected,all_candidates=rank,rule='PROTOCOL.selection, screen45 development; includes tiny input, no claim at TL280',new_revision='v3 adds verified specialists, all general random screen instances use the same racing algorithm'),indent=2))
protocol=json.loads((R/'PROTOCOL.json').read_text());spec['name']='development280_v3';spec['seconds']=280;spec['seeds']=[0,11602];spec['cases']={k:v for k,v in spec['cases'].items()if k in protocol['development']['cases']}
spec['variants']={k:v for k,v in spec['variants'].items()if k in ['v4','v10']};spec['variants']['adaptive']=dict(binary='experiments/adaptive_v11/artifacts/v3/candidate',env=selected['env'])
(R/'DEVELOPMENT280_V3.json').write_text(json.dumps(spec,indent=2));stage('development280',selected=selected)
with (R/'logs/development280_v3.output').open('x')as f:subprocess.run([sys.executable,str(R/'src/run_instrumented.py'),str(R/'DEVELOPMENT280_V3.json')],cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,check=True)
subprocess.run([sys.executable,str(R/'src/analysis.py'),'development280_v3'],cwd=ROOT,check=True);stage('development_complete_await_freeze',selected=selected)
