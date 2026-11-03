# Independent enumeration of the cardinality reduction underlying GEO_SPLIT=5.
# Positive rewards, a fixed separator, fixed skills, alpha=0, nonempty offices.
import itertools,random,json
from pathlib import Path
rng=random.Random(711);results=[]
for i in range(2000):
 A=rng.randrange(5);fixed=[rng.randrange(1,7) for _ in range(rng.randrange(4))]
 if fixed and max(fixed)-min(fixed)>A:continue
 rewards=[[rng.uniform(.1,10) for _ in range(rng.randrange(1,7))] for _ in range(2)];caps=[rng.randrange(1,8) for _ in range(2)]
 lim=min(fixed)+A if fixed else 100
 n=[min(caps[j],lim,len(rewards[j]),len(rewards[1-j])+A) for j in range(2)]
 def feasible(a,b):v=fixed+[a,b];return a>0 and b>0 and max(v)-min(v)<=A
 def val(a,b):return sum(sorted(rewards[0],reverse=True)[:a])+sum(sorted(rewards[1],reverse=True)[:b])
 oracle=max((val(a,b) for a in range(1,min(caps[0],len(rewards[0]))+1) for b in range(1,min(caps[1],len(rewards[1]))+1) if feasible(a,b)),default=None)
 found=val(*n) if feasible(*n) else None
 # Capacities of the opposite side also constrain available count.
 n2=[min(caps[j],lim,len(rewards[j]),min(caps[1-j],lim,len(rewards[1-j]))+A) for j in range(2)]
 corrected=val(*n2) if feasible(*n2) else None
 results.append(dict(i=i,oracle=oracle,found=found,corrected=corrected))
summary=dict(cases=len(results),mismatch=sum(r['oracle'] is not None and (r['found'] is None or abs(r['oracle']-r['found'])>1e-8) for r in results),corrected_mismatch=sum(r['oracle']!=r['corrected'] and (r['oracle'] is None or r['corrected'] is None or abs(r['oracle']-r['corrected'])>1e-8) for r in results))
R=Path(__file__).resolve().parent;(R/'logs/count_oracle.json').write_text(json.dumps(dict(summary=summary,results=results),indent=2));print(summary)
