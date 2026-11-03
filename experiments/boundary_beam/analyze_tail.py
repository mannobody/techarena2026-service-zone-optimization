import json,re,statistics,math,random
from pathlib import Path
H=Path(__file__).resolve().parent
out={}
for folder in (H/'logs').iterdir():
 p=folder/'results.json'
 if not p.exists():continue
 data=json.loads(p.read_text())
 if not isinstance(data,dict) or not data.get('results') or not any(r.get('variant')=='tail' for r in data['results']):continue
 rows=data['results'];paired=[];local=[]
 for row in rows:
  if row['variant']!='tail':continue
  base=next((r for r in rows if r['case']==row['case'] and r['seed']==row['seed'] and r['variant']=='base'),None)
  if base and base['score']>0:paired.append(dict(case=row['case'],seed=row['seed'],delta_pct=100*(row['score']/base['score']-1)))
  text=Path(row['solution']).with_suffix('.stderr').read_text()
  m=re.search(r'boundary_finish before=([-\d.]+) after=([-\d.]+) seconds=([-\d.]+)',text)
  if m:
   before,after,seconds=map(float,m.groups());local.append(dict(case=row['case'],seed=row['seed'],before=before,after=after,seconds=seconds,delta_pct=100*(after/before-1) if before>0 else 0))
 cases=[]
 for case in sorted(set(r['case'] for r in rows)):
  a=[r['score'] for r in rows if r['case']==case and r['variant']=='tail'];b=[r['score'] for r in rows if r['case']==case and r['variant']=='base']
  if a and b and statistics.median(b)>0:
   inp=next(r['input'] for r in rows if r['case']==case)
   ns=len(json.loads(Path(inp).read_text())['sites'])
   cases.append(dict(case=case,sites=ns,operator_enabled=ns<=1500,delta_pct=100*(statistics.median(a)/statistics.median(b)-1),base_n=len(b),tail_n=len(a)))
 ds=[r['delta_pct'] for r in cases];rng=random.Random(999);samples=[]
 if ds:
  for _ in range(5000):samples.append(statistics.mean(rng.choices(ds,k=len(ds))))
  samples.sort()
 out[folder.name]=dict(cases=cases,paired=paired,actual_tail=local,case_mean_pct=statistics.mean(ds) if ds else None,case_median_pct=statistics.median(ds) if ds else None,case_bootstrap_mean_ci95=[samples[125],samples[4874]] if samples else None,actual_positive=sum(x['delta_pct']>1e-7 for x in local),actual_count=len(local),actual_mean_pct=statistics.mean(x['delta_pct'] for x in local) if local else 0)
 for label,enabled in [('enabled_cases',True),('disabled_control_cases',False)]:
  selected=[r for r in cases if r['operator_enabled']==enabled];values=[r['delta_pct'] for r in selected]
  out[folder.name][label]=dict(cases=selected,count=len(values),mean_pct=statistics.mean(values) if values else None,median_pct=statistics.median(values) if values else None,min_pct=min(values) if values else None,max_pct=max(values) if values else None)
(H/'logs/TAIL_ANALYSIS.json').write_text(json.dumps(out,indent=2))
for tag,r in out.items():print(tag,'cases',len(r['cases']),'mean',round(r['case_mean_pct'],3),'median',round(r['case_median_pct'],3),'local wins',r['actual_positive'],'/',r['actual_count'],'local mean',round(r['actual_mean_pct'],3))
