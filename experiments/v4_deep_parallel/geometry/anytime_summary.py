import json,sys
from pathlib import Path
R=Path(__file__).resolve().parent;root=R.parents[2];p=R/'logs/v4_anti600/results.json';rows=json.loads(p.read_text());r=rows[0];d=json.loads((R/'inputs/dev_anti.json').read_text());seq=[]
for snap in r['snapshots']+[dict(target_seconds=600,file=str((R/'logs/v4_anti600/anti_713_v4.solution.json').relative_to(root)),objective=r['objective'],valid=r['valid'])]:
 if not snap.get('valid'):continue
 s=json.loads((root/snap['file']).read_text());a={x:o['officeId'] for o in s for x in o['sites']};seq.append(dict(seconds=snap['target_seconds'],objective=snap['objective'],offices=[o['officeId'] for o in s],counts=[len(o['sites']) for o in s],loads=[sum(len(d['sites'][x]['tasks']) for x in o['sites']) for o in s],assignment=a))
for i in range(1,len(seq)):
 a,b=seq[i-1]['assignment'],seq[i]['assignment'];seq[i]['changed_assignments']=sum(a.get(x)!=b.get(x) for x in set(a)|set(b));seq[i]['gain']=seq[i]['objective']-seq[i-1]['objective']
for s in seq:del s['assignment']
result=dict(run_success=r['success'],seed=r['seed'],affinity=r['affinity'],wall=r['wall'],sequence=seq,caveat='Internal anytime trajectory, not an equal-budget comparison with TL280: phase budgets and stopping/finishing differ.');(R/'ANYTIME600.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
