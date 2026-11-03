import json,os,time,subprocess,sys,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];ROOT=R.parents[1];os.sched_setaffinity(0,{14,15})
def read(p):return json.loads((R/p).read_text())
def save(p,a):(R/p).write_text(json.dumps(a,indent=2))
def stage(n,**kw):save('STATUS.json',dict(stage=n,updated_unix=time.time(),**kw))
def run(spec):
 name=spec['name'];path=R/(name.upper()+'.json');assert not path.exists();save(path.name,spec)
 with(R/'logs'/(name+'.output')).open('x')as f:subprocess.run([sys.executable,str(R/'src/run.py'),str(path)],cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,check=True)
 subprocess.run([sys.executable,str(R/'src/analyze.py'),name],cwd=ROOT,check=True)
def select(name,limit,distinct):
 a=read('logs/'+name+'/ANALYSIS.json');spec=read('logs/'+name+'/MANIFEST.json')['spec'];rows=read('logs/'+name+'/results.json');rank=[]
 for n in spec['variants']:
  if n=='submission':continue
  rr=[x for x in rows if x['variant']==n];m=a['comparisons'][n+'_vs_submission']['all_valid'];ok=all(x['rc']==0 and x['valid']and not x['timeout']and not x['error']and x['wall']<300 for x in rr)
  rank.append(dict(variant=n,operational=ok,mean=m['mean_case_percent'],worst=m['worst'],family=read('PROTOCOL.json')['families'][n],configuration=spec['variants'][n]))
 good=[x for x in rank if x['operational']];assert good
 qualified=[x for x in good if x['worst']>=-5];good=qualified if qualified else good;good.sort(key=lambda x:(x['mean'],x['worst']),reverse=True)
 chosen=[]
 for x in good:
  if distinct and any(y['family']==x['family']for y in chosen):continue
  chosen.append(x)
  if len(chosen)==limit:break
 assert len(chosen)==limit,(rank,chosen)
 save(name.upper()+'_SELECTION.json',dict(selected=chosen,ranking=rank,rule='PROTOCOL.json; development only, no unseen inputs yet'))
 return chosen
stage('waiting_build_qa_optional_library')
while not all((R/p).exists()for p in ['BUILD_STATUS.json','QA_STATUS.json','HIGHS_QA.json']):time.sleep(1)
assert read('QA_STATUS.json')['all_valid'];assert read('HIGHS_QA.json')['valid']==18
stage('screen20');s=read('SCREEN20.json')
# SCREEN20 was preregistered, runner consumes that exact file.
with(R/'logs/screen20.output').open('x')as f:subprocess.run([sys.executable,str(R/'src/run.py'),str(R/'SCREEN20.json')],cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,check=True)
subprocess.run([sys.executable,str(R/'src/analyze.py'),'screen20'],cwd=ROOT,check=True);chosen=select('screen20',2,True)
p=read('PROTOCOL.json')['long_development'];s['name']='development280';s['seconds']=p['seconds'];s['seeds']=p['seeds'];s['cases']={n:s['cases'][n]for n in p['cases']};s['variants']={'submission':s['variants']['submission'],**{x['variant']:x['configuration']for x in chosen}}
stage('development280',selected=[x['variant']for x in chosen]);run(s);winner=select('development280',1,False)[0]
save('SELECTED.json',dict(selected=winner,selected_unix=time.time(),fresh_inputs_exist=(R/'inputs/fresh').exists()));assert not(R/'inputs/fresh').exists();stage('development_complete_await_package_freeze',selected=winner['variant']);print('selection ready',winner['variant'],flush=True)
