import json,random,statistics,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]
name=sys.argv[1];d=R/'logs'/name;s=json.loads((d/'MANIFEST.json').read_text())['spec'];rows=json.loads((d/'results.json').read_text());by={(r['case'],r['seed'],r['variant']):r for r in rows}
out=dict(series=name,runs=len(rows),expected=len(s['cases'])*len(s['seeds'])*len(s['variants']),valid=sum(r['valid']for r in rows),success=sum(r['success']for r in rows),failures=[{k:r[k]for k in ['case','seed','variant','rc','timeout','wall','valid','error']}for r in rows if not r['success']],comparisons={})
def metrics(ps):
 p=[x['percent']for x in ps if x['percent']is not None];means=[statistics.mean(x['percent']for x in ps if x['case']==c and x['percent']is not None)for c in sorted({x['case']for x in ps})if any(x['percent']is not None for x in ps if x['case']==c)]
 boot=[];rng=random.Random(717)
 if means:
  for _ in range(5000):boot.append(statistics.mean(rng.choices(means,k=len(means))))
  boot.sort()
 return dict(pairs=len(ps),mean_case_percent=statistics.mean(means)if means else None,median=statistics.median(p)if p else None,sd=statistics.stdev(p)if len(p)>1 else 0,worst=min(p,default=None),best=max(p,default=None),wins=sum(x['delta']>1e-7 for x in ps),ties=sum(abs(x['delta'])<=1e-7 for x in ps),losses=sum(x['delta']<-1e-7 for x in ps),case_bootstrap95=[boot[125],boot[4875]]if boot else None)
for v in s['variants']:
 if v in ['v4','v10']:continue
 for control in ['v4','v10']:
  if control not in s['variants']:continue
  pairs=[]
  for c in s['cases']:
   for seed in s['seeds']:
    a=by.get((c,seed,v));b=by.get((c,seed,control))
    if not a or not b or not a['valid']or not b['valid']:continue
    assert a['affinity']==b['affinity'];delta=a['official']-b['official']
    pairs.append(dict(case=c,seed=seed,delta=delta,percent=100*delta/abs(b['official'])if abs(b['official'])>1e-9 else None,base=b['official'],candidate=a['official'],both_success=a['success']and b['success']))
  out['comparisons'][v+'_vs_'+control]=dict(all_valid=metrics(pairs),successful=metrics([p for p in pairs if p['both_success']]),per_case={c:metrics([p for p in pairs if p['case']==c])for c in s['cases']},pairs=pairs)
(d/'ANALYSIS.json').write_text(json.dumps(out,indent=2))
print(json.dumps({k:v for k,v in out.items()if k!='comparisons'}))
for k,v in out['comparisons'].items():print(k,json.dumps(v['all_valid']))
