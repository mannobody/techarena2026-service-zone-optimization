"""Conservative resource veto; no extra long jobs under the user's speed request."""
import json,time,os
from pathlib import Path
R=Path(__file__).resolve().parents[1];os.sched_setaffinity(0,{14,15})
def read(p):return json.loads((R/p).read_text())
def save(p,a):(R/p).write_text(json.dumps(a,indent=2))
save('RESOURCE_STATUS.json',dict(stage='waiting_accelerated_primary'))
while not (R/'CONFIRMATION_STATUS.json').exists()or read('CONFIRMATION_STATUS.json')['stage']!='independent280_complete':time.sleep(1)
rows=read('logs/independent280_v4/results.json');a=read('logs/independent280_v4/ANALYSIS.json');c4=a['comparisons']['adaptive_vs_v4']['all_valid'];c10=a['comparisons']['adaptive_vs_v10']['all_valid']
operational=lambda r:r['valid']and r['rc']==0 and not r['timeout']and not r['error']and r['wall']<300
criteria=dict(all30_operational=len(rows)==30 and all(operational(r)for r in rows),mean_vs_v4_positive=c4['mean_case_percent']>0,mean_vs_v10_positive=c10['mean_case_percent']>0,bootstrap_v4_lower_positive=c4['case_bootstrap95'][0]>0,worst_v4_at_least_minus1=c4['worst']>=-1)
blocks={}
for r in rows:blocks.setdefault((r['case'],r['seed']),[]).append(r)
disparities=[]
for (case,seed),rs in blocks.items():
 vals={r['variant']:(r['resource_fields']['user']+r['resource_fields']['sys'])/r['wall']for r in rs};disparities.append(dict(case=case,seed=seed,ratios=vals,range=max(vals.values())-min(vals.values())))
disparities.sort(key=lambda x:x['range'],reverse=True)
criteria['matched_cpu_spread_at_most_half']=all(x['range']<=.5 for x in disparities)
save('RESOURCE_DECISION.json',dict(primary_quality_gate=all(v for k,v in criteria.items()if k!='matched_cpu_spread_at_most_half'),promote=all(criteria.values()),criteria=criteria,disparities=disparities,meaning='Conservative veto only. No primary rows replaced. No additional long repeat under predeclared SPEED_ADDENDUM. CPU/wall disparity may also reflect early exact completion; it is not proof of external contention.'))
save('RESOURCE_STATUS.json',dict(stage='complete',promote=all(criteria.values()),extra_runs=0))
