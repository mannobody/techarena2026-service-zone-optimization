"""Development mechanism study, never pooled with the independent general suite."""
import json,random,hashlib,subprocess,sys,time,os
from pathlib import Path
R=Path(__file__).resolve().parents[1];ROOT=R.parents[1];os.sched_setaffinity(0,{14,15})
plan=dict(purpose='Data-class specialist mechanism; no general quality claim',cases=10,ns=110,no=9,workers='9 universal [0,1]',alpha=0,A=110,distances='independent random road matrix',seed_offset=1240000,screen_seconds=8,screen_seed=0,long_seconds=280,long_seeds=[0,11802,11803],long_selection='Largest short v4 relative gap to independently certified exact value; viewed development, not fresh holdout',cpus=[[3,6],[8,10]])
(R/'LINE_MECHANISM_PLAN.json').write_text(json.dumps(plan,indent=2))
d=R/'inputs/line_mechanism';d.mkdir(exist_ok=False);cases={}
for i in range(10):
 rng=random.Random(1240000+i);ns=110;no=9;anchors=rng.sample(range(ns),no)
 a=dict(sites=[dict(x=s,y=0,reward=rng.uniform(15,30),tasks=[0]*(1+s%3)+([1]if s%5==0 else[]))for s in range(ns)],offices=[dict(x=x,y=0,cost=rng.uniform(10,30),maxSize=rng.randint(10,25))for x in anchors],workers=[[0,1]for _ in range(no)],distances=[[rng.uniform(0,40)for s in range(ns)]for o in range(no)],maxDifference=ns,balanceCoefficient=0)
 p=d/f'line{i}.json';p.write_text(json.dumps(a));cases[p.stem]=str(p.relative_to(ROOT))
# Wait for correctness work on the same dedicated pair to finish first.
while not (R/'logs/qa_v3/results.json').exists()or len(json.loads((R/'logs/qa_v3/results.json').read_text()))<66:time.sleep(1)
variants=dict(v4=dict(binary='experiments/structural_v9/artifacts/v4'),v10=dict(binary='experiments/warm_v10/artifacts/v5/candidate',env=dict(ZM_POOL='0',ZM_RESERVE='0',GW_MODE='1')),adaptive=dict(binary='experiments/adaptive_v11/artifacts/v3/candidate'))
spec=dict(name='line_screen8',seconds=8,seeds=[0],cpus=plan['cpus'],cases=cases,variants=variants)
def run(spec,path):
 (R/path).write_text(json.dumps(spec,indent=2))
 with (R/'logs'/(spec['name']+'.output')).open('x')as f:subprocess.run([sys.executable,str(R/'src/run_instrumented.py'),str(R/path)],cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,check=True)
 subprocess.run([sys.executable,str(R/'src/analysis.py'),spec['name']],cwd=ROOT,check=True)
run(spec,'LINE_SCREEN8.json')
a=json.loads((R/'logs/line_screen8/ANALYSIS.json').read_text());pairs=a['comparisons']['adaptive_vs_v4']['pairs'];selected=max(pairs,key=lambda x:x['percent'])['case']
(R/'LINE_MECHANISM_SELECTION.json').write_text(json.dumps(dict(case=selected,reason=plan['long_selection']),indent=2))
spec['name']='line_development280';spec['seconds']=280;spec['seeds']=plan['long_seeds'];spec['cases']={selected:cases[selected]}
run(spec,'LINE_DEVELOPMENT280.json')
(R/'LINE_STATUS.json').write_text(json.dumps(dict(stage='complete',case=selected),indent=2));print(json.dumps(dict(complete=True,line_case=selected)),flush=True)
