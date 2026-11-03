import collections,json,math,statistics,sys
from pathlib import Path
dest=Path(sys.argv[1]);base=sys.argv[2] if len(sys.argv)>2 else 'v4'
rows=json.loads((dest/'results.json').read_text());groups=collections.defaultdict(dict)
for row in rows:groups[row['case'],row['seed']][row['variant']]=row
labels=sorted({r['variant'] for r in rows}-{base});summary={}
for label in labels:
    pairs=[];by=collections.defaultdict(list);bad=[];undefined=[]
    for (case,seed),g in groups.items():
        if base not in g or label not in g:continue
        b,c=g[base],g[label]
        if not b['success'] or not c['success']:bad.append(dict(case=case,seed=seed,base=b['success'],candidate=c['success']))
        if b['objective'] is None or c['objective'] is None or b['objective']==0:
            undefined.append(dict(case=case,seed=seed));continue
        delta=100*(c['objective']-b['objective'])/abs(b['objective']);pairs.append(delta);by[case].append(delta)
    means=[statistics.mean(v) for v in by.values()]
    v=dict(pairs=len(pairs),input_weighted_mean=statistics.mean(means) if means else None,
        median=statistics.median(pairs) if pairs else None,worst=min(pairs) if pairs else None,
        wtl=[sum(x>1e-7 for x in pairs),sum(abs(x)<=1e-7 for x in pairs),sum(x< -1e-7 for x in pairs)],
        failed_pairs=bad,undefined=undefined,by_input={k:dict(mean=statistics.mean(v),median=statistics.median(v),worst=min(v)) for k,v in by.items()})
    summary[label]=v
(dest/f'SUMMARY_vs_{base}.json').write_text(json.dumps(summary,indent=2))
for k,v in summary.items():print(k,json.dumps({kk:vv for kk,vv in v.items() if kk!='by_input'}))
