import os,time,sys,json,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];ROOT=R.parents[1];os.sched_setaffinity(0,{14,15})
(R/'CLEAN_LINE_PLAN.json').write_text(json.dumps(dict(source_revision='v4',seconds=280,seeds=[0,11802,11803],selection='Same viewed line9 chosen by preregistered line_screen8 rule; repeat because provisional package test overlapped one old line baseline row',cpus=[[3,6],[8,10]],serialization='Starts only after CORRECTED_STATUS complete; all package/QA compute pinned controller14,15; no general-statistic merging'),indent=2))
while not (R/'CORRECTED_STATUS.json').exists():time.sleep(1)
s=json.loads((R/'LINE_DEVELOPMENT280.json').read_text());s['name']='line_corrected280_v4';s['variants']['adaptive']['binary']='experiments/adaptive_v11/artifacts/v4/candidate';s['variants']['adaptive']['env']=json.loads((R/'SCREEN_SELECTION.json').read_text())['selected']['env']
(R/'LINE_CORRECTED280_V4.json').write_text(json.dumps(s,indent=2))
with (R/'logs/line_corrected280_v4.output').open('x')as f:subprocess.run([sys.executable,str(R/'src/run_instrumented.py'),str(R/'LINE_CORRECTED280_V4.json')],cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,check=True)
subprocess.run([sys.executable,str(R/'src/analysis.py'),'line_corrected280_v4'],cwd=ROOT,check=True);(R/'CLEAN_LINE_STATUS.json').write_text(json.dumps(dict(stage='complete'),indent=2))
