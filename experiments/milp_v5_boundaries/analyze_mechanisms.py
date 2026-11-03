from regions import *
import json
rows=[]
for tag,case,mode in [('native_post60','alphabig0','fixed'),('native_post60','latent0','fixed'),('master_train60','alphabig0','power')]:
 r=next(r for r in json.loads((H/'logs'/tag/'results.json').read_text()) if r['case']==case and r['mode']==mode);I=Instance.read(r['input']);old=json.loads(Path(r['incumbent']).read_text());raw=json.loads((H/'logs'/tag/f'{case}_{mode}.json').read_text());new=raw['solution'] if isinstance(raw,dict) else raw
 def summarize(sol):
  owner={s:r['officeId'] for r in sol for s in r['sites']};loads={r['officeId']:sum(int(I.tasks[s]) for s in r['sites']) for r in sol};counts={r['officeId']:len(r['sites']) for r in sol};profit=sum(float(I.profit[o,s]) for s,o in owner.items());cost=sum(float(I.cost[o]) for o in loads);penalty=I.alpha*(max(loads.values())-min(loads.values())) if loads else 0
  return owner,dict(loads=loads,counts=counts,profit=profit,cost=cost,penalty=penalty,score=value(I,sol))
 a,b=summarize(old);c,d=summarize(new);item=dict(tag=tag,case=case,mode=mode,before=b,after=d,transferred=sum(s in a and a[s]!=o for s,o in c.items()),added=sum(s not in a for s in c),removed=sum(s not in c for s in a),opened=sorted(set(d['loads'])-set(b['loads'])),closed=sorted(set(b['loads'])-set(d['loads'])));rows.append(item);print(json.dumps(item))
(H/'logs/mechanisms.json').write_text(json.dumps(rows,indent=2))
