#!/usr/bin/env python3
import sys,json,statistics as st,re
from pathlib import Path
p=Path(sys.argv[1]);rows=json.loads(p.read_text());out={'runs':len(rows),'success':sum(r['success'] for r in rows),'failures':[r for r in rows if not r['success']],'variants':{},'comparisons':{}}
variants=sorted({r['variant'] for r in rows});cases=sorted({r['case'] for r in rows})
def distribution(v):
 return dict(mean=st.mean(v),median=st.median(v),worst=min(v),best=max(v),std=st.pstdev(v)) if v else {}
for v in variants:
 rs=[r for r in rows if r['variant']==v];out['variants'][v]={'cases':{},'wall':distribution([r['wall'] for r in rs]),'max_rss_kb':max([int(m[1]) for r in rs if (m:=re.search(r'rss_kb=(\d+)',r.get('resource','')))]+[0]),'actual_threads':sorted({str(r.get('actual_nt')) for r in rs})}
 wall=out['variants'][v]['wall'];wall['min']=wall['worst'];wall['max']=wall['best'];wall['worst'],wall['best']=wall['max'],wall['min']
 for c in cases:out['variants'][v]['cases'][c]=distribution([r['objective'] for r in rs if r['case']==c and r['success']])
lookup={(r['case'],r['seed'],r['variant']):r for r in rows}
for v in variants:
 if v=='base':continue
 vals=[];casevals={}
 for r in rows:
  if r['variant']!=v:continue
  b=lookup.get((r['case'],r['seed'],'base'))
  if b and b['success'] and r['success']:
   d=100*(r['objective']-b['objective'])/max(1,abs(b['objective']));vals.append(d);casevals.setdefault(r['case'],[]).append(d)
 cm={}
 for c,ds in casevals.items():
  bb=out['variants']['base']['cases'][c];cc=out['variants'][v]['cases'][c]
  cm[c]={'paired':distribution(ds),'median_delta_pct':100*(cc['median']-bb['median'])/max(1,abs(bb['median']))}
 out['comparisons'][v]={'paired_pct':distribution(vals),'wtl':[sum(x>1e-7 for x in vals),sum(abs(x)<=1e-7 for x in vals),sum(x< -1e-7 for x in vals)],'cases':cm,'complete_pairs':len(vals)}
p.with_name('SUMMARY.json').write_text(json.dumps(out,indent=2))
print('runs',out['runs'],'success',out['success'])
for v,d in out['comparisons'].items():print(v,d['paired_pct'],d['wtl'], {c:round(x['median_delta_pct'],4) for c,x in d['cases'].items()})
