import json,statistics,sys,math
from pathlib import Path
R=Path(__file__).resolve().parent;tag=sys.argv[1];p=R/'logs'/tag/'results.json';rows=json.loads(p.read_text());lookup={(r['case'],r['seed'],r['variant']):r for r in rows};out={'runs':len(rows),'success':sum(r['success'] for r in rows),'variants':{}}
def stats(a):return dict(mean=statistics.mean(a),median=statistics.median(a),worst=min(a),best=max(a),std=statistics.pstdev(a)) if a else None
for v in sorted({r['variant'] for r in rows}):
 a=[r for r in rows if r['variant']==v];pairs=[]
 for r in a:
  b=lookup.get((r['case'],r['seed'],'v4'))
  if b and b['success'] and r['success']:pairs.append(dict(case=r['case'],seed=r['seed'],delta_pct=(r['objective']-b['objective'])/max(1,abs(b['objective']))*100))
 out['variants'][v]=dict(completed=len(a),paired=len(pairs),delta_pct=stats([r['delta_pct'] for r in pairs]),wtl=[sum(r['delta_pct']>1e-7 for r in pairs),sum(abs(r['delta_pct'])<=1e-7 for r in pairs),sum(r['delta_pct']< -1e-7 for r in pairs)],wall=stats([r['wall'] for r in a]),by_case={c:dict(objective=stats([r['objective'] for r in a if r['case']==c and r['success']]),delta_pct=stats([r['delta_pct'] for r in pairs if r['case']==c])) for c in sorted({r['case'] for r in a})},pairs=pairs)
(R/f'{tag.upper()}_SUMMARY.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
