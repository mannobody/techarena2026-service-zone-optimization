import hashlib,json,subprocess,sys,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
def stage(name,**kw):(R/'LONG_V4_STATUS.json').write_text(json.dumps(dict(stage=name,updated_unix=time.time(),**kw),indent=2))
stage('waiting_bootstrap_screen')
while json.loads((R/'STATUS_v4.json').read_text())['stage']!='screen30_v4_complete':time.sleep(1)
a=json.loads((R/'logs/screen30_v4/ANALYSIS.json').read_text())
assert a['runs']==a['expected']
for v in ['geometry','memetic']:
 assert all(x.get('variant')!=v for x in a['failures']),a['failures']
 worst=a['comparisons'][v+'_vs_v4']['per_case']['huge']['worst']
 assert worst>=-5.,(v,'bootstrap still fails on huge',worst)
files=[R/'src/run.py',R/'src/analysis.py',R/'DEVELOPMENT280_V4.json',R/'artifacts/v4/main.cpp',R/'artifacts/v4/candidate']
(R/'DEVELOPMENT_FREEZE.json').write_text(json.dumps(dict(files={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()for p in files}),indent=2))
stage('development280_v4')
with (R/'logs/development280_v4.progress').open('x')as f:
 subprocess.run([sys.executable,str(R/'src/run.py'),str(R/'DEVELOPMENT280_V4.json')],cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,check=True)
with (R/'logs/development280_v4.summary').open('x')as f:
 subprocess.run([sys.executable,str(R/'src/analysis.py'),'development280_v4'],cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,check=True)
stage('development280_v4_complete')
