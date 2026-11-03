"""Summarize completed confirmatory measurements without changing any raw logs."""
import json,statistics as st
from pathlib import Path
H=Path(__file__).resolve().parent
expected={'holdout60_broad':72,'validation2_wide60':48,'holdout60':8}
out={}
for tag,n in expected.items():
 d=json.loads((H/'logs'/tag/'results.json').read_text());rows=d['results']
 assert len(rows)==n,(tag,len(rows),n)
 assert all(r['error'] is None and r['rc']==0 for r in rows)
 variant=next(r['variant'] for r in rows if r['variant']!='base');cases=[];pairs=[]
 for case in sorted(set(r['case'] for r in rows)):
  a=[r for r in rows if r['case']==case and r['variant']==variant];b=[r for r in rows if r['case']==case and r['variant']=='base']
  sa=[r['score'] for r in a];sb=[r['score'] for r in b]
  cases.append(dict(case=case,sites=len(json.loads(Path(a[0]['input']).read_text())['sites']),base_median=st.median(sb),candidate_median=st.median(sa),delta_pct=100*(st.median(sa)/st.median(sb)-1)))
  for x in a:
   y=next(y for y in b if y['seed']==x['seed']);pairs.append(dict(case=case,seed=x['seed'],delta_pct=100*(x['score']/y['score']-1)))
 ds=[x['delta_pct'] for x in cases]
 out[tag]=dict(config=d['config'],valid=n,cases=cases,case_mean_pct=st.mean(ds),case_median_pct=st.median(ds),case_worst=min(cases,key=lambda x:x['delta_pct']),case_best=max(cases,key=lambda x:x['delta_pct']),pair_worst=min(pairs,key=lambda x:x['delta_pct']),pair_best=max(pairs,key=lambda x:x['delta_pct']),max_wall_by_variant={v:max(r['wall'] for r in rows if r['variant']==v) for v in ['base',variant]})
(H/'logs/CONFIRMATION.json').write_text(json.dumps(out,indent=2))
for tag,d in out.items():print(tag,json.dumps({k:v for k,v in d.items() if k not in ['config','cases']},ensure_ascii=False))
