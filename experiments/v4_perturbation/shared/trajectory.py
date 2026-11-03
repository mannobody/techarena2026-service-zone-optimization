"""Observe flat incumbent intervals; these are not local-optimality proofs."""
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from analyze import compare,ROOT
R=Path(__file__).resolve().parents[1]
allrows=[]
for name in ('checkpoint60','checkpoint280'):
 d=R/'shared/logs'/name
 if not (d/'COMPLETE.json').exists():continue
 m=json.loads((d/'MANIFEST.json').read_text());rows=json.loads((d/'results.json').read_text())
 for r in rows:
  inp=ROOT/m['spec']['cases'][r['case']]
  snaps=[(x['observed_seconds'],ROOT/x['file']) for x in r['snapshots'] if x.get('valid')]
  snaps.append((r['wall'],d/f"{r['case']}_{r['seed']}_v4.solution.json"))
  segments=[]
  for (ta,a),(tb,b) in zip(snaps,snaps[1:]):
   c=compare(inp,a,b);flat=abs(c['delta']['objective'])<=1e-9*max(1,abs(c['base']['objective']))
   segments.append({'from':ta,'to':tb,'seconds':tb-ta,'flat_objective':flat,'identical_assignments':c['assignment_changes']==0,'configuration':c})
  allrows.append({'series':name,'case':r['case'],'segments':segments})
segments=[s for x in allrows for s in x['segments']]
out={'note':'Snapshot-observed incumbent plateaus; publication is monotone, but unchanged incumbent does not imply stagnant internal state or proved local maximum. Snapshot durations exclude input prefix before first sample.','runs':allrows,'intervals':len(segments),'flat_intervals':sum(s['flat_objective'] for s in segments),'flat_seconds':sum(s['seconds'] for s in segments if s['flat_objective']),'observed_seconds':sum(s['seconds'] for s in segments)}
(R/'shared/TRAJECTORIES.json').write_text(json.dumps(out,indent=2))
print({k:v for k,v in out.items() if k!='runs'})
