from pathlib import Path
import random,itertools,json
from milp import Instance,improve,value
H=Path(__file__).resolve().parent;rows=[]
for seed in range(251000,251040):
 r=random.Random(seed);n=12;m=3;sites=[];profits=[];off=[];inc=[]
 for o in range(m):
  off.append(dict(x=10*o,y=0,cost=r.randrange(12),maxSize=4));ss=[]
  for j in range(4):
   ss.append(len(sites));sites.append(dict(x=10*o+.1+j*.01,y=.1+j*j*.01,reward=100,tasks=[0]*r.randrange(5)));profits.append(r.randrange(-30,90))
  inc.append(dict(officeId=o,sites=ss,workers=[o]))
 A=r.choice([0,1,12]);alpha=r.choice([0,.5,7,30]);data=dict(sites=sites,offices=off,workers=[[0] for _ in range(m)],distances=[[100-profits[s] if s//4==o else 1000 for s in range(n)] for o in range(m)],maxDifference=A,balanceCoefficient=alpha);I=Instance(data);best=0
 for mask in range(1<<n):
  counts=[0]*m;loads=[0]*m;score=0
  for s in range(n):
   if mask>>s&1:counts[s//4]+=1;loads[s//4]+=len(sites[s]['tasks']);score+=profits[s]
  ops=[o for o in range(m) if counts[o]]
  if not ops:continue
  if max(counts[o] for o in ops)-min(counts[o] for o in ops)>A:continue
  score-=sum(off[o]['cost'] for o in ops)+alpha*(max(loads[o] for o in ops)-min(loads[o] for o in ops));best=max(best,score)
 ans=improve(I,inc,60,'assigned');assert ans['rejected'] is None and ans['status']=='optimal' and abs(ans['value']-best)<1e-6,(seed,best,ans)
 rows.append(dict(seed=seed,expected=best,value=ans['value'],seconds=ans['seconds'],data=data))
(H/'logs/milp_oracle.json').write_text(json.dumps(rows,indent=2));print(len(rows),'MILP / exhaustive subset matches')
