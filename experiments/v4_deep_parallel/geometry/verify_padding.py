import json,itertools,sys,hashlib
from pathlib import Path
R=Path(__file__).resolve().parent;ROOT=R.parents[2];sys.path.insert(0,str(ROOT/'task'));from validate_solution import validate
p=R/'inputs/padding_witness.json';d=json.loads(p.read_text());n=len(d['sites']);m=len(d['offices']);best=-1e300;besta=None;feasible=0
for a in itertools.product(range(-1,m),repeat=n):
 mem=[[x for x,o in enumerate(a) if o==q] for q in range(m)];ops=[o for o in range(m) if mem[o]];counts=[len(mem[o]) for o in ops]
 if any(len(mem[o])>d['offices'][o]['maxSize'] for o in ops) or (counts and max(counts)-min(counts)>d['maxDifference']):continue
 intervals=[(min([d['offices'][o]['x']]+[d['sites'][x]['x'] for x in mem[o]]),max([d['offices'][o]['x']]+[d['sites'][x]['x'] for x in mem[o]])) for o in ops];intervals.sort()
 if any(intervals[i][1]>=intervals[i+1][0] for i in range(len(intervals)-1)):continue
 feasible+=1;v=sum(d['sites'][x]['reward']-d['distances'][o][x] for x,o in enumerate(a) if o>=0)
 if v>best:best=v;besta=a
rows={q:validate(p,R/'logs'/f'witness_{q}.solution.json') for q in ['v4','padding']}
out=dict(enumerated=(m+1)**n,feasible=feasible,optimum=best,assignment=besta,native_values=rows,input_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),native_binary_sha256=hashlib.sha256((R/'bin/post_padding').read_bytes()).hexdigest());(R/'logs/padding_oracle.json').write_text(json.dumps(out,indent=2));print(out)
assert best==135 and rows['v4']==130 and rows['padding']==135
