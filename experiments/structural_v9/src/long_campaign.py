"""Frozen development selection -> fresh independent TL280 confirmation.
Never changes the solver in response to independent outcomes.
"""
import hashlib,json,subprocess,sys,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
freeze=json.loads((R/'FREEZE.json').read_text())
def verify():
    for p,h in freeze['files'].items():assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h,p
def stage(name,**kw):(R/'CAMPAIGN_STATUS.json').write_text(json.dumps(dict(stage=name,updated_unix=time.time(),**kw),indent=2))
def execute(script,args,log):
    with (R/'logs'/log).open('x')as f:subprocess.run([sys.executable,str(R/'src'/script),*map(str,args)],cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,check=True)
verify();stage('development280')
execute('run.py',[R/'DEVELOPMENT280.json'],'development280.progress')
execute('summarize.py',['development280'],'development280.summary.txt')
summary=json.loads((R/'logs/development280/SUMMARY.json').read_text())
assert not summary['missing']
rank=sorted(summary['variants'],key=lambda v:summary['variants'][v]['successful_pairs']['mean_case_percent'],reverse=True)
selected=rank[0];spec=json.loads((R/'DEVELOPMENT280.json').read_text());config=spec['variants'][selected]
selection=dict(selected=selected,config=config,development_metrics={v:summary['variants'][v]['successful_pairs']for v in rank},selected_unix=time.time(),freeze_sha256=hashlib.sha256((R/'FREEZE.json').read_bytes()).hexdigest(),holdout_seen=False)
(R/'HOLDOUT_SELECTION.json').write_text(json.dumps(selection,indent=2));verify();stage('generating_holdout',selected=selected)
execute('generate.py',['holdout'],'generate_holdout.txt')
inputs=json.loads((R/'HOLDOUT_INPUTS.json').read_text());protocol=json.loads((R/'PREREGISTRATION.json').read_text())['holdout']
holdout=dict(name='independent280',seconds=protocol['seconds'],seeds=protocol['seeds'],cpus=spec['cpus'],cases={k:inputs[k]['path']for k in protocol['cases']},variants={'v4':spec['variants']['v4'],'candidate':config})
(R/'INDEPENDENT280.json').write_text(json.dumps(holdout,indent=2));verify();stage('independent280',selected=selected)
execute('run.py',[R/'INDEPENDENT280.json'],'independent280.progress')
execute('summarize.py',['independent280'],'independent280.summary.txt')
final=json.loads((R/'logs/independent280/SUMMARY.json').read_text());assert not final['missing'];verify();stage('complete',selected=selected,runs=summary['runs']+final['runs'])
print(json.dumps(dict(status='complete',selected=selected,independent=final['variants']['candidate']['all_valid_pairs'])))
