import json,statistics,re
from pathlib import Path
R=Path(__file__).resolve().parents[1];ROOT=R.parents[1];D=json.loads((R/'CLASSIFIER_EXPLORATION.json').read_text())['inputs']
constant=statistics.mean(x['y']for x in D);oracle=statistics.mean(max(0,x['y'])for x in D);run_oracle=statistics.mean(statistics.mean(max(0,y)for y in x['raw'])for x in D)
rows=[]
for name in ['development280_v5_both','acceleration280','independent280']:
 d=ROOT/'experiments/warm_v10/logs'/name;a=json.loads((d/'results.json').read_text());spec=json.loads((d/'MANIFEST.json').read_text())['spec'];variants=[v for v,c in spec['variants'].items()if c['binary']=='experiments/warm_v10/artifacts/v5/candidate'and c.get('env',{}).get('GW_MODE')=='1'];by={(x['case'],x['seed'],x['variant']):x for x in a}
 for v in variants:
  for x in [z for z in a if z['variant']==v]:
   b=by[x['case'],x['seed'],'v4'];p=100*(x['official']-b['official'])/abs(b['official'])
   def ratio(z):
    f=z.get('resource_fields')or{k:float(v)for k,v in re.findall(r'(user|sys)=([0-9.]+)',z['resource'])};return(f['user']+f['sys'])/z['wall']
   rows.append(dict(series=name,case=x['case'],seed=x['seed'],percent=p,candidate_cpu_wall=ratio(x),v4_cpu_wall=ratio(b)))
res=dict(instances=len(D),constant_geometry_mean=constant,hindsight_instance_mean_oracle=oracle,available_headroom_pp=oracle-constant,hindsight_per_seed_oracle_mean=run_oracle,per_seed_headroom_pp=run_oracle-constant,warning='Oracles use final answers and cannot run at deployment. Noise/resource labels are not causally determined by input features. No row is deleted.',pairs=rows)
(R/'ROUTING_HEADROOM.json').write_text(json.dumps(res,indent=2));print(json.dumps({k:v for k,v in res.items()if k!='pairs'}));print('negative',json.dumps([x for x in rows if x['percent']<-.5]))
(R/'EXPLORATORY_POLICY_NOTE.json').write_text(json.dumps(dict(thresholds='Coarse bins were chosen during exploratory work after viewing historical data, not preregistered before label access. Grouped CV is development model-selection only, potentially optimistic after selection. The final independent plan and algorithm freeze provide separate confirmation.',runtime='No static fitted tree is used; only certified domain guards and fixed workload-horizon rules plus online objective comparison.'),indent=2))
