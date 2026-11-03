"""Descriptive same-hardware TL280 controls; no significance claim from four blocks."""
from pathlib import Path
import json, statistics as st
R=Path(__file__).resolve().parent
rows=json.loads((R/'logs/control280/results.json').read_text())
assert len(rows)==16 and all(x['success'] for x in rows), 'Do not summarize incomplete or failed controls as success'
blocks={}
for x in rows: blocks.setdefault((x['case'],x['seed']),{})[x['variant']]=x
out={'blocks':[], 'comparisons':{}}
for (case,seed),v in sorted(blocks.items()):
 assert len({tuple(x['affinity']) for x in v.values()})==1
 out['blocks'].append({'case':case,'seed':seed,'affinity':v['v4']['affinity'], 'objective':{k:x['objective'] for k,x in v.items()},'wall':{k:x['wall'] for k,x in v.items()}})
for control in ['v4','lab_off']:
 for variant in ['lab_off','batch','wide']:
  if variant==control:continue
  ps=[100*(v[variant]['objective']-v[control]['objective'])/max(1,abs(v[control]['objective'])) for v in blocks.values()]
  out['comparisons'][variant+'_vs_'+control]={'n':len(ps),'mean':st.mean(ps),'median':st.median(ps),'min':min(ps),'max':max(ps),'std':st.pstdev(ps),'wtl':[sum(p>1e-7 for p in ps),sum(abs(p)<=1e-7 for p in ps),sum(p< -1e-7 for p in ps)]}
(R/'CONTROL_COMPARISONS.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
