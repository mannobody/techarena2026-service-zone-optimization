"""Matched long check of the exact singleton acceleration after warm-architecture selection."""
import hashlib,json,subprocess,sys,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def stage(name,**kw):(R/'ACCELERATION_STATUS.json').write_text(json.dumps(dict(stage=name,updated_unix=time.time(),**kw),indent=2))
stage('waiting_full_warm_development')
while json.loads((R/'LONG_BOTH_STATUS.json').read_text())['stage']!='development280_v5_both_complete':time.sleep(1)
a=json.loads((R/'logs/development280_v5_both/ANALYSIS.json').read_text());assert a['runs']==a['expected']==48
methods=['geometry','memetic']
def score(v):
 m=[a['comparisons'][v+'_vs_'+c]['all_valid']for c in ['v4','v9']]
 # Prefer a positive robust result; quality mean breaks ties between viable methods.
 return (min(x['worst']for x in m)>=-1.,min(x['mean_case_percent']for x in m))
selected=max(methods,key=score)
s=json.loads((R/'DEVELOPMENT280_V5_BOTH.json').read_text());config=s['variants'][selected]
s['name']='acceleration280';s['seeds']=[9403,10402];s['cases']={k:s['cases'][k]for k in ['medium_anti','regression_large','huge']}
s['variants']={'v4':s['variants']['v4'],'v9':s['variants']['v9'],'prior':config,'candidate':dict(binary='experiments/warm_v10/artifacts/v6/candidate',env=dict(config['env']))}
for v in s['variants'].values():v['env'].pop('DBG',None)
s['cpus']=json.loads((R/'INDEPENDENT_RESOURCE_ADDENDUM.json').read_text())['cpus']
p=R/'ACCELERATION280.json';assert not p.exists();p.write_text(json.dumps(s,indent=2))
files=[R/'artifacts/v5/main.cpp',R/'artifacts/v5/candidate',R/'artifacts/v6/main.cpp',R/'artifacts/v6/candidate',R/'src/run_instrumented.py',p]
(R/'ACCELERATION_FREEZE.json').write_text(json.dumps(dict(files={str(p.relative_to(ROOT)):sha(p)for p in files},selected_architecture=selected,selection_scores={v:score(v)for v in methods},reason='Full warm development selected architecture; exact singleton shortcut checked on all 24 offices with zero score difference, then compared in full solver to both immutable controls and the matching pre-shortcut v5. No fresh independent inputs yet.',selected_unix=time.time()),indent=2))
stage('acceleration280',architecture=selected)
with (R/'logs/acceleration280.progress').open('x')as f:subprocess.run([sys.executable,str(R/'src/run_instrumented.py'),str(p)],cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,check=True)
with (R/'logs/acceleration280.summary').open('x')as f:subprocess.run([sys.executable,str(R/'src/analysis.py'),'acceleration280'],cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,check=True)
stage('acceleration280_complete',architecture=selected)
