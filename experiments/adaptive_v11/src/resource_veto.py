import json,time,subprocess,sys,os
from pathlib import Path
R=Path(__file__).resolve().parents[1];ROOT=R.parents[1];os.sched_setaffinity(0,{14,15})
def save(p,x):(R/p).write_text(json.dumps(x,indent=2))
save('RESOURCE_STATUS.json',dict(stage='waiting_primary'))
while not (R/'CONFIRMATION_STATUS.json').exists()or json.loads((R/'CONFIRMATION_STATUS.json').read_text())['stage']!='independent280_complete':time.sleep(1)
rows=json.loads((R/'logs/independent280_v4/results.json').read_text());a=json.loads((R/'logs/independent280_v4/ANALYSIS.json').read_text());c4=a['comparisons']['adaptive_vs_v4']['all_valid'];c10=a['comparisons']['adaptive_vs_v10']['all_valid']
operational=lambda r:r['valid']and r['rc']==0 and not r['timeout']and not r['error']and r['wall']<300
criteria=dict(all72_operational=len(rows)==72 and all(operational(r)for r in rows),mean_vs_v4_positive=c4['mean_case_percent']>0,mean_vs_v10_positive=c10['mean_case_percent']>0,bootstrap_v4_lower_positive=c4['case_bootstrap95'][0]>0,worst_v4_at_least_minus1=c4['worst']>=-1)
gate=all(criteria.values());blocks={}
for r in rows:blocks.setdefault((r['case'],r['seed']),[]).append(r)
disparities=[]
for (case,seed),rs in blocks.items():
 vals={r['variant']:(r['resource_fields']['user']+r['resource_fields']['sys'])/r['wall']for r in rs};disparities.append(dict(case=case,seed=seed,ratios=vals,range=max(vals.values())-min(vals.values())))
disparities.sort(key=lambda x:x['range'],reverse=True);trigger=gate and disparities[0]['range']>.5
save('RESOURCE_DECISION.json',dict(primary_gate=gate,criteria=criteria,trigger=trigger,disparities=disparities,meaning='Viewed-input scheduling veto; never replaces/merges primary'))
if not trigger:save('RESOURCE_STATUS.json',dict(stage='not_required',reason='Primary promotion fails'if not gate else'No matched CPU/wall disparity above0.5'));sys.exit(0)
s=json.loads((R/'INDEPENDENT280_V4.json').read_text());case=disparities[0]['case'];s['name']='resource_repeat280_v4';s['cpus']=[[12,13],[16,17],[20,21]];s['cases']={case:s['cases'][case]};save('RESOURCE_REPEAT280_V4.json',s);save('RESOURCE_STATUS.json',dict(stage='resource_repeat280',case=case))
with (R/'logs/resource_repeat280_v4.output').open('x')as f:subprocess.run([sys.executable,str(R/'src/run_instrumented.py'),str(R/'RESOURCE_REPEAT280_V4.json')],cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,check=True)
subprocess.run([sys.executable,str(R/'src/analysis.py'),'resource_repeat280_v4'],cwd=ROOT,check=True)
b=json.loads((R/'logs/resource_repeat280_v4/ANALYSIS.json').read_text());rs=json.loads((R/'logs/resource_repeat280_v4/results.json').read_text());m=b['comparisons']['adaptive_vs_v4']['all_valid'];passed=len(rs)==9 and all(operational(r)for r in rs)and m['worst']>=-1
save('RESOURCE_RESULT.json',dict(case=case,passed=passed,metrics_vs_v4=m));save('RESOURCE_STATUS.json',dict(stage='complete',passed=passed,case=case))
