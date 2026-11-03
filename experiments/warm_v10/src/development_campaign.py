import json,subprocess,sys,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
def stage(name,**kw):(R/'LONG_STATUS.json').write_text(json.dumps(dict(stage=name,updated_unix=time.time(),**kw),indent=2))
def run(script,args,log):
 with (R/'logs'/log).open('x')as f:subprocess.run([sys.executable,str(R/'src'/script),*map(str,args)],cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,check=True)
stage('waiting_v3_build_and_short_screen')
while not (R/'artifacts/v3/BUILD.json').exists():time.sleep(1)
run('qa.py',['v3'],'qa_v3.progress')
while json.loads((R/'STATUS.json').read_text())['stage']!='screen30_v2_complete':time.sleep(1)
stage('development280_v3');run('run.py',[R/'DEVELOPMENT280_V3.json'],'development280_v3.progress')
run('analysis.py',['development280_v3'],'development280_v3.summary')
stage('development280_v3_complete')
