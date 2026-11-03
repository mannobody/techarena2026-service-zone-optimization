import hashlib,json,subprocess,sys,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
def stage(name,**kw):(R/'LONG_BOTH_STATUS.json').write_text(json.dumps(dict(stage=name,updated_unix=time.time(),**kw),indent=2))
stage('waiting_screen')
while json.loads((R/'STATUS_v5.json').read_text())['stage']!='screen30_v5_complete':time.sleep(1)
a=json.loads((R/'logs/screen30_v5/results.json').read_text());assert len(a)==24
assert all(x['valid']and x['rc']==0 and not x['timeout']and not x['error']for x in a if x['variant']in ['geometry','memetic'])
files=[R/'src/run.py',R/'src/analysis.py',R/'DEVELOPMENT280_V5_BOTH.json',R/'artifacts/v5/main.cpp',R/'artifacts/v5/candidate']
(R/'DEVELOPMENT_FREEZE_BOTH.json').write_text(json.dumps(dict(files={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()for p in files},reason='Both variants evaluated at 280 despite short quality differences. Correctness and broad-mask bootstrap verified; short timing tolerance failures retained. Five concurrent pairs to leave hardware headroom.'),indent=2))
stage('development280_v5_both')
with (R/'logs/development280_v5_both.progress').open('x')as f:
 subprocess.run([sys.executable,str(R/'src/run.py'),str(R/'DEVELOPMENT280_V5_BOTH.json')],cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,check=True)
with (R/'logs/development280_v5_both.summary').open('x')as f:
 subprocess.run([sys.executable,str(R/'src/analysis.py'),'development280_v5_both'],cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,check=True)
stage('development280_v5_both_complete')
