from pathlib import Path
import json,statistics as st
H=Path(__file__).resolve().parent
out={}
for folder in sorted((H/'logs').glob('*')):
 p=folder/'results.json'
 if not p.exists():continue
 raw=json.loads(p.read_text());rows=raw.get('results',[]) if isinstance(raw,dict) else raw
 if not rows or 'variant' not in rows[0]:continue
 table=[]
 for case in sorted(set(r['case'] for r in rows)):
  base=[r['score'] for r in rows if r['case']==case and r['variant']=='base'];b=st.median(base) if base else None
  for v in sorted(set(r['variant'] for r in rows if r['case']==case)):
   rs=[r for r in rows if r['case']==case and r['variant']==v];scores=[r['score'] for r in rs]
   if any(not isinstance(s,(int,float)) for s in scores):continue
   table.append(dict(case=case,variant=v,n=len(rs),median=st.median(scores),min=min(scores),max=max(scores),delta_pct=100*(st.median(scores)/b-1) if b else None,max_wall=max(r['wall'] for r in rs)))
 out[folder.name]=dict(config=raw.get('config') if isinstance(raw,dict) else None,valid=sum(not r.get('error') and r.get('rc',0)==0 for r in rows),count=len(rows),table=table)
(H/'logs/SUMMARY.json').write_text(json.dumps(out,indent=2))
for tag,info in out.items():
 print(tag,info['valid'],info['count'])
 for v in sorted(set(r['variant'] for r in info['table'])):
  if v=='base':continue
  a=[r for r in info['table'] if r['variant']==v and r['delta_pct'] is not None];ds=[r['delta_pct'] for r in a]
  print(v,'mean',round(st.mean(ds),3),'median',round(st.median(ds),3),'worst',round(min(ds),3),'best',round(max(ds),3))
