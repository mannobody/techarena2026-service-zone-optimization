"""Predeclared resource-risk veto; never replaces or merges independent primary rows."""
import hashlib,json,subprocess,sys,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
def stage(name,**kw):(R/'RESOURCE_DIAGNOSTIC_STATUS.json').write_text(json.dumps(dict(stage=name,updated_unix=time.time(),**kw),indent=2))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
stage('waiting_primary')
while not (R/'CONFIRMATION_STATUS.json').exists()or json.loads((R/'CONFIRMATION_STATUS.json').read_text())['stage']!='independent280_complete':time.sleep(1)
selection=json.loads((R/'SELECTION.json').read_text());v=selection['variant'];spec=json.loads((R/'INDEPENDENT280.json').read_text());summary=json.loads((R/'logs/independent280/ANALYSIS.json').read_text());rows=json.loads((R/'logs/independent280/results.json').read_text())
metrics=[summary['comparisons'][v+'_vs_'+c]['all_valid']for c in ['v4','v9']]
candidate=[x for x in rows if x['variant']==v]
primary=(len(rows)==72 and len(candidate)==24 and all(x['valid']and x['rc']==0 and not x['timeout']and not x['error']and x['wall']<300 for x in candidate)
         and all(x['pairs']==24 and x['mean_case_percent']>0 for x in metrics)
         and metrics[0]['case_bootstrap95'][0]>0 and metrics[0]['worst']>=-1.)
by={(x['case'],x['seed'],x['variant']):x for x in rows};disparities=[]
for c in spec['cases']:
 for seed in spec['seeds']:
  ratios=[]
  for label in spec['variants']:
   a=by[(c,seed,label)];f=a['resource_fields'];ratios.append((f.get('user',0)+f.get('sys',0))/a['wall'])
  disparities.append(dict(case=c,seed=seed,range=max(ratios)-min(ratios),ratios=ratios))
disparities.sort(key=lambda x:(-x['range'],x['case'],x['seed']));trigger=primary and disparities[0]['range']>.5
decision=dict(primary_gate=primary,trigger=trigger,largest_disparity=disparities[0],all_disparities=disparities,purpose='Viewed-input scheduling diagnostic and promotion veto; no new holdout and no replacement of original primary rows.')
(R/'RESOURCE_DIAGNOSTIC_DECISION.json').write_text(json.dumps(decision,indent=2))
if not trigger:
 stage('not_required',primary_gate=primary,reason='Primary already fails the declared promotion gate'if not primary else 'No paired CPU ratio range above 0.5');sys.exit()
case=disparities[0]['case'];s=dict(spec);s['name']='resource_diagnostic280';s['cases']={case:spec['cases'][case]};s['cpus']=[[12,13],[16,17],[20,21]]
p=R/'RESOURCE_DIAGNOSTIC280.json';p.write_text(json.dumps(s,indent=2));stage('resource_diagnostic280',case=case)
with (R/'logs/resource_diagnostic280.progress').open('x')as f:subprocess.run([sys.executable,str(R/'src/run_instrumented.py'),str(p)],cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,check=True)
with (R/'logs/resource_diagnostic280.summary').open('x')as f:subprocess.run([sys.executable,str(R/'src/analysis.py'),'resource_diagnostic280'],cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,check=True)
diag=json.loads((R/'logs/resource_diagnostic280/ANALYSIS.json').read_text());dr=json.loads((R/'logs/resource_diagnostic280/results.json').read_text());dm=diag['comparisons'][v+'_vs_v4']['all_valid']
passed=(len(dr)==9 and dm['pairs']==3 and dm['worst']>=-1. and all(x['valid']and x['rc']==0 and not x['timeout']and not x['error']and x['wall']<300 for x in dr if x['variant']==v))
for fp,h in json.loads((R/'FREEZE.json').read_text())['files'].items():assert sha(ROOT/fp)==h,fp
(R/'RESOURCE_DIAGNOSTIC_RESULT.json').write_text(json.dumps(dict(passed=passed,case=case,metrics_vs_v4=dm,primary_unchanged=True,diagnostic_only=True),indent=2));stage('resource_diagnostic280_complete',passed=passed,case=case)
