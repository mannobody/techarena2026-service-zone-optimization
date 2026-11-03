import json,math,random,statistics,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]
name=sys.argv[1];d=R/'logs'/name;manifest=json.loads((d/'MANIFEST.json').read_text());s=manifest['spec'];a=json.loads((d/'results.json').read_text())
expected={(c,seed,v)for c in s['cases']for seed in s['seeds']for v in s['variants']};keys=[(r['case'],r['seed'],r['variant'])for r in a]
assert len(keys)==len(set(keys)), 'duplicate rows'
by={k:r for k,r in zip(keys,a)};base='v4';variants=[v for v in s['variants']if v!=base]
out=dict(series=name,seconds=s['seconds'],runs=len(a),expected_runs=len(expected),missing=sorted(expected-set(keys)),valid=sum(r['valid']for r in a),success=sum(r['success']for r in a),failures=[{k:r[k]for k in ['case','seed','variant','rc','timeout','wall','valid','error']}for r in a if not r['success']],variants={})
for v in variants:
    pairs=[];groups={}
    for c in s['cases']:
        ps=[]
        for seed in s['seeds']:
            b=by.get((c,seed,base));z=by.get((c,seed,v))
            if not b or not z:continue
            assert b['affinity']==z['affinity']
            if not b['valid']or not z['valid']:continue
            delta=z['official']-b['official'];pct=100*delta/abs(b['official'])if abs(b['official'])>1e-9 else None
            p=dict(case=c,seed=seed,base=b['official'],candidate=z['official'],delta=delta,percent=pct,both_success=b['success']and z['success']);ps.append(p);pairs.append(p)
        if ps:groups[c]=ps
    percase={c:dict(mean_percent=statistics.mean(p['percent']for p in ps if p['percent']is not None)if any(p['percent']is not None for p in ps)else None,base_values=[p['base']for p in ps],candidate_values=[p['candidate']for p in ps],median_delta=statistics.median(p['delta']for p in ps),worst_percent=min((p['percent']for p in ps if p['percent']is not None),default=None))for c,ps in groups.items()}
    def metric(ps):
        percentages=[p['percent']for p in ps if p['percent']is not None];g={c:[p['percent']for p in ps if p['case']==c and p['percent']is not None]for c in groups};means=[statistics.mean(x)for x in g.values()if x]
        return dict(pairs=len(ps),nonzero_reference_pairs=len(percentages),mean_case_percent=statistics.mean(means)if means else None,median_pair_percent=statistics.median(percentages)if percentages else None,sd_pair_percent=statistics.stdev(percentages)if len(percentages)>1 else 0,worst_percent=min(percentages,default=None),best_percent=max(percentages,default=None),wins=sum(p['delta']>1e-7 for p in ps),ties=sum(abs(p['delta'])<=1e-7 for p in ps),losses=sum(p['delta']<-1e-7 for p in ps))
    cm=[p['mean_percent']for p in percase.values()if p['mean_percent']is not None];boot=[];rng=random.Random(717)
    if cm:
        for _ in range(5000):boot.append(statistics.mean(rng.choices(cm,k=len(cm))))
        boot.sort()
    out['variants'][v]=dict(all_valid_pairs=metric(pairs),successful_pairs=metric([p for p in pairs if p['both_success']]),bootstrap_cases_95=[boot[125],boot[4875]]if boot else None,per_case=percase,pairs=pairs)
(d/'SUMMARY.json').write_text(json.dumps(out,indent=2))
print(json.dumps({k:x for k,x in out.items()if k not in ['variants','failures','missing']}))
for v,x in out['variants'].items():print(v,json.dumps(x['all_valid_pairs']), 'success_only',json.dumps(x['successful_pairs']))
for c,x in out['variants'][variants[0]]['per_case'].items():print(c,json.dumps(x))
