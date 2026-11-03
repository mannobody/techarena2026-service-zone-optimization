import os,subprocess,json,sys,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];ROOT=R.parents[1];os.sched_setaffinity(0,{14,15})
(R/'CORRECTED280_PLAN.json').write_text(json.dumps(dict(timing='Before corrected outcomes and independent generation',cases=['grid180','huge10000'],seconds=280,seeds=[0],variants=['v4','v10','adaptive'],source_revision='v4',purpose='Direct long validation of the final numerical correction; separate from unmodified v3 full development',cpus=[[3,6],[8,10]]),indent=2))
while not (R/'LINE_STATUS.json').exists()or not (R/'logs/scale_qa_v4/results.json').exists():time.sleep(1)
rows=json.loads((R/'logs/scale_qa_v4/results.json').read_text());assert len(rows)==411 and all(x['valid']and x['match']for x in rows)
s=json.loads((R/'DEVELOPMENT280_V3.json').read_text());s['name']='corrected280_v4';s['seeds']=[0];s['cpus']=[[3,6],[8,10]];s['cases']={k:v for k,v in s['cases'].items()if k in ['grid180','huge10000']};s['variants']['adaptive']['binary']='experiments/adaptive_v11/artifacts/v4/candidate'
(R/'CORRECTED280_V4.json').write_text(json.dumps(s,indent=2))
with (R/'logs/corrected280_v4.output').open('x')as f:subprocess.run([sys.executable,str(R/'src/run_instrumented.py'),str(R/'CORRECTED280_V4.json')],cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,check=True)
subprocess.run([sys.executable,str(R/'src/analysis.py'),'corrected280_v4'],cwd=ROOT,check=True)
(R/'CORRECTED_STATUS.json').write_text(json.dumps(dict(stage='complete'),indent=2))
