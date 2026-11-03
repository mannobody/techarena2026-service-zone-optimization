import json,os,subprocess,sys,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
def stage(name,**kw):(R/'STATUS.json').write_text(json.dumps(dict(stage=name,updated_unix=time.time(),**kw),indent=2))
def run(script,args,log):
 with (R/'logs'/log).open('x')as f:subprocess.run([sys.executable,str(R/'src'/script),*map(str,args)],cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,check=True)
stage('waiting_build_v2')
while not (R/'artifacts/v2/BUILD.json').exists():time.sleep(1)
stage('qa_v2');run('qa.py',['v2'],'qa_v2.progress')
stage('mechanism')
with (R/'logs/mechanism_compile.log').open('x')as f:
 subprocess.run(['taskset','-c','14,15','g++','-O1','-std=c++17',str(R/'src/mechanism.cpp'),'-o',str(R/'artifacts/mechanism')],stdout=f,stderr=subprocess.STDOUT,check=True)
with (R/'logs/mechanism.json').open('x')as f:subprocess.run([str(R/'artifacts/mechanism'),str(R/'inputs/equal_score_geometry.json')],stdout=f,check=True)
stage('screen30_v2');run('run.py',[R/'SCREEN30_V2.json'],'screen30_v2.progress')
run('analysis.py',['screen30_v2'],'screen30_v2.summary')
stage('screen30_v2_complete')
