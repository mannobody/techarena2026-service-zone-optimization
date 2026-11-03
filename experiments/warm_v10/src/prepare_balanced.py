import json,subprocess,sys,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
while not (R/'artifacts/v8/BUILD.json').exists():time.sleep(1)
def run(script,args,log):
 with (R/'logs'/log).open('x')as f:subprocess.run([sys.executable,str(R/'src'/script),*map(str,args)],cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,check=True)
run('qa.py',['v8'],'qa_v8.progress')
run('balanced_mechanism.py',[],'balanced_mechanism.progress')
run('package_revision.py',['v8'],'package_v8.progress')
