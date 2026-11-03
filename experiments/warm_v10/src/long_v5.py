import hashlib,json,subprocess,sys,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
def stage(name,**kw):(R/'LONG_V5_STATUS.json').write_text(json.dumps(dict(stage=name,updated_unix=time.time(),**kw),indent=2))
def run(script,args,log):
 with (R/'logs'/log).open('x')as f:subprocess.run([sys.executable,str(R/'src'/script),*map(str,args)],cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,check=True)
stage('waiting_proxy_only_screen')
while json.loads((R/'STATUS_v5.json').read_text())['stage']!='screen30_v5_complete':time.sleep(1)
a=json.loads((R/'logs/screen30_v5/ANALYSIS.json').read_text());assert a['runs']==a['expected']
eligible=[]
for v in ['geometry','memetic']:
 if any(x['variant']==v for x in a['failures']):continue
 if a['comparisons'][v+'_vs_v4']['per_case']['huge']['worst']<-5.:continue
 eligible.append(v)
assert eligible,('bootstrap still fails',a['comparisons'])
selected=max(eligible,key=lambda v:a['comparisons'][v+'_vs_v9']['all_valid']['mean_case_percent'])
p=R/'DEVELOPMENT280_V5.json';original=p.read_bytes();(R/'artifacts/plans/DEVELOPMENT280_V5_FOUR_VARIANTS_PLANNED.json').write_bytes(original)
s=json.loads(original);s['variants']={k:v for k,v in s['variants'].items()if k in ['v4','v9',selected]}
s['cpus']=[[0,1],[12,13],[16,17],[18,19],[20,21]]
p.write_text(json.dumps(s,indent=2))
(R/'DEVELOPMENT_SELECTION.json').write_text(json.dumps(dict(selected=selected,eligible=eligible,reason='Highest mean against v9 on proxy-only bootstrap development screen, with no candidate failure and huge worst >= -5%. Reduced concurrency before long data.',short_metrics={v:a['comparisons'][v+'_vs_v9']['all_valid']for v in ['geometry','memetic']},long_cases=list(s['cases']),seeds=s['seeds'],seconds=s['seconds'],cpus=s['cpus'],selected_unix=time.time()),indent=2))
files=[R/'src/run.py',R/'src/analysis.py',p,R/'artifacts/v5/main.cpp',R/'artifacts/v5/candidate']
(R/'DEVELOPMENT_FREEZE_V5.json').write_text(json.dumps(dict(files={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()for p in files}),indent=2))
stage('development280_v5',selected=selected)
run('run.py',[p],'development280_v5.progress')
run('analysis.py',['development280_v5'],'development280_v5.summary')
stage('development280_v5_complete',selected=selected)
