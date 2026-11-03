import json,subprocess,sys,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];ROOT=R.parents[1];revision=sys.argv[1]
def stage(name,**kw):(R/('STATUS_'+revision+'.json')).write_text(json.dumps(dict(stage=name,updated_unix=time.time(),**kw),indent=2))
def run(script,args,log):
 with (R/'logs'/log).open('x')as f:subprocess.run([sys.executable,str(R/'src'/script),*map(str,args)],cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,check=True)
stage('waiting_build')
while not (R/'artifacts'/revision/'BUILD.json').exists():time.sleep(1)
run('qa.py',[revision],'qa_'+revision+'.progress')
name='screen30_'+revision;stage(name);run('run.py',[R/('SCREEN30_'+revision.upper()+'.json')],name+'.progress')
run('analysis.py',[name],name+'.summary');stage(name+'_complete')
