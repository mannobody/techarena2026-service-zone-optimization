import json,os
from pathlib import Path
os.sched_setaffinity(0,{12,13})
R=Path(__file__).resolve().parent;ROOT=R.parents[2];SH=R.parent/'shared';rows=[]
for suffix,seed,times in [('60',1901,[10,30,50]),('280',1902,[60,120,200,260])]:
 d=SH/'logs'/('checkpoint'+suffix);manifest=json.loads((d/'MANIFEST.json').read_text())
 for case,path in manifest['spec']['cases'].items():
  inst=json.loads((ROOT/path).read_text());records=[]
  for t in times+[int(suffix)]:
   f=d/(f'{case}_{seed}_v4'+(f'.t{t}' if t!=int(suffix)else'')+'.solution.json')
   if not f.exists():continue
   s=json.loads(f.read_text());a=[-1]*len(inst['sites']);o=[];load=[];reward=distance=cost=0
   for z in s:
    office=z['officeId'];o.append(office);load.append(sum(len(inst['sites'][x]['tasks'])for x in z['sites']));cost+=inst['offices'][office]['cost']
    for x in z['sites']:a[x]=office;reward+=inst['sites'][x]['reward'];distance+=inst['distances'][office][x]
   penalty=inst['balanceCoefficient']*(max(load)-min(load))if load else 0
   r={'time':t,'objective':reward-distance-cost-penalty,'offices':sorted(o),'load_range':max(load)-min(load)if load else 0}
   if records:r['assignment_changes_since_previous']=sum(x!=y for x,y in zip(prev,a));r['objective_change_since_previous']=r['objective']-records[-1]['objective']
   prev=a;records.append(r)
  rows.append({'checkpoint_seconds':int(suffix),'seed':seed,'case':case,'observed_snapshots':records})
(R/'PLATEAU.json').write_text(json.dumps(rows,indent=2))
