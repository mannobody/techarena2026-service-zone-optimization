import hashlib,json,subprocess,sys,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def stage(name,**kw):(R/'BALANCED_STATUS.json').write_text(json.dumps(dict(stage=name,updated_unix=time.time(),**kw),indent=2))
stage('waiting_v5_and_balanced_qa')
while not (R/'ACCELERATION_SUPERSEDED_ACK.json').exists():time.sleep(1)
while not (R/'logs/qa_v8/results.json').exists()or not (R/'PACKAGE_CHECK_v8.json').exists():time.sleep(1)
qa=json.loads((R/'logs/qa_v8/results.json').read_text());assert len(qa)==60 and all(x['valid']and x['rc']==0 for x in qa)
for f in ['ACCELERATION280.json','ACCELERATION_FREEZE.json']:(R/'artifacts/plans'/('superseded_'+f)).write_bytes((R/f).read_bytes())
s=json.loads((R/'ACCELERATION280.json').read_text());s['allow_superseded']=True
config=s['variants']['candidate'];s['variants']['balanced']=dict(binary='experiments/warm_v10/artifacts/v8/candidate',env=dict(config['env']))
p=R/'ACCELERATION280.json';p.write_text(json.dumps(s,indent=2))
old=json.loads((R/'ACCELERATION_FREEZE.json').read_text());files=[ROOT/q for q in old['files']if q!=str(p.relative_to(ROOT))]
files +=[p,R/'artifacts/v8/main.cpp',R/'artifacts/v8/candidate',R/'artifacts/v8/balanced_warm.h',R/'src/run_instrumented.py']
old['files']={str(q.relative_to(ROOT)):sha(q)for q in files};old['balanced_added_before_runs']=True;old['expected_runs']=30
(R/'ACCELERATION_FREEZE.json').write_text(json.dumps(old,indent=2));stage('acceleration280')
with (R/'logs/acceleration280_balanced.progress').open('x')as f:subprocess.run([sys.executable,str(R/'src/run_instrumented.py'),str(p)],cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,check=True)
with (R/'logs/acceleration280_balanced.summary').open('x')as f:subprocess.run([sys.executable,str(R/'src/analysis.py'),'acceleration280'],cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,check=True)
stage('acceleration280_complete');(R/'ACCELERATION_STATUS.json').write_text(json.dumps(dict(stage='acceleration280_complete',balanced=True,expected_runs=30),indent=2))
