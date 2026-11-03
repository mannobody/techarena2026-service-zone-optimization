import json,sys,statistics as st
from pathlib import Path
R=Path(__file__).resolve().parent
out={}
for name in sys.argv[1:]:
 path=R/'logs'/name/'results.json'
 if not path.exists():continue
 rows=json.loads(path.read_text());d={}
 def stat(a):return dict(n=len(a),mean=st.mean(a),median=st.median(a),min=min(a),max=max(a),std=st.pstdev(a)) if a else {}
 for v in sorted({x['variant'] for x in rows}):
  vr=[x for x in rows if x['variant']==v];pairs=[];bycase={}
  for x in vr:
   b=next((z for z in rows if z['variant']=='v4' and z['case']==x['case'] and z['seed']==x['seed'] and z['success']),None)
   if b and x['success']:
    p=(x['objective']-b['objective'])/max(1,abs(b['objective']))*100;pairs.append(p);bycase.setdefault(x['case'],[]).append(p)
  d[v]={'runs':len(vr),'failures':sum(not x['success'] for x in vr),'delta_percent':stat(pairs),'wtl':[sum(p>1e-7 for p in pairs),sum(abs(p)<=1e-7 for p in pairs),sum(p< -1e-7 for p in pairs)],'by_case':{c:stat(vs) for c,vs in bycase.items()},'wall':stat([x['wall'] for x in vr])}
 out[name]=d
(R/'METRICS.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
