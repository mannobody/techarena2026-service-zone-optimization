"""Audit CPU overlap and final-solution diversity without changing results."""
import json,itertools,statistics as st
from pathlib import Path
R=Path(__file__).resolve().parent;ROOT=R.parents[1]
names=['development60_clean','development60_v3','holdout60_tail','huge180','open60_tail','regression60_repeat','development60_cycle_repeat','holdout60_cycle','package_cycle_synthetic','holdout60_cycle_variance']
intervals=[];diversity={}
for name in names:
 p=R/'logs'/name/'results.json'
 if not p.exists():continue
 rows=json.loads(p.read_text());group={}
 for row in rows:
  intervals.append(dict(row,series=name))
  if not row['success']:continue
  source=row.get('source',name)
  # clean result lineage uses explicit relative/absolute path when provided.
  pref=R/'logs'/source if '/' not in source else Path(source)
  sol=p.parent/f"{row['case']}_{row['seed']}_{row['variant']}.solution.json"
  if not sol.exists():sol=pref/f"{row['case']}_{row['seed']}_{row['variant']}.solution.json"
  if not sol.exists():continue
  a=json.loads(sol.read_text());assign={s:z['officeId'] for z in a for s in z['sites']};mask=tuple(sorted(z['officeId'] for z in a));group.setdefault((row['case'],row['variant']),[]).append((assign,mask))
 out={}
 for (c,v),aa in group.items():
  if len(aa)<2:continue
  ds=[sum(a.get(s,-1)!=b.get(s,-1) for s in a.keys()|b.keys()) for (a,_),(b,_) in itertools.combinations(aa,2)]
  out[c+'/'+v]={'runs':len(aa),'distinct_office_masks':len({m for a,m in aa}),'assignment_difference_sites_mean':st.mean(ds),'assignment_difference_sites_max':max(ds)}
 diversity[name]=out
conflicts=[]
for a,b in itertools.combinations(intervals,2):
 if 'started_unix' not in a or 'started_unix' not in b:continue
 if not set(a['affinity'])&set(b['affinity']):continue
 overlap=min(a['ended_unix'],b['ended_unix'])-max(a['started_unix'],b['started_unix'])
 if overlap>0.01:conflicts.append({'a':[a['series'],a['case'],a['seed'],a['variant']],'b':[b['series'],b['case'],b['seed'],b['variant']],'seconds':overlap})
(R/'RUN_AUDIT.json').write_text(json.dumps({'included':names,'completed_rows':len(intervals),'cpu_overlap_conflicts':conflicts,'scope':'Recorded runs only; compilation, old diagnostics and unrelated external processes excluded.','final_solution_diversity':diversity},indent=2));print('runs',len(intervals),'overlapping CPU pairs',len(conflicts))
