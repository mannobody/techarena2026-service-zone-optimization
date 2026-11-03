"""Independent counterexamples for invalid dominance and office-set bounds."""
import itertools,json
from bench import H,V
S=lambda x,y,r:dict(x=x,y=y,reward=r,tasks=[])
O=lambda x,y:dict(x=x,y=y,cost=0,maxSize=1)
def val(d,rows):return V.validate_solution(V.Instance.model_validate(d),[V.OpenedOffice.model_validate(r) for r in rows])
d=dict(sites=[S(2,0,10),S(-1,0,6),S(1,0,6)],offices=[O(-2,0),O(-1,1),O(1,1)],workers=[],distances=[[0,100,100],[100,0,100],[100,100,0]],maxDifference=3,balanceCoefficient=0)
f={}
for allowed in [(0,),(0,1),(0,2),(0,1,2)]:
 best=0
 for a in itertools.product([-1,*allowed],repeat=3):
  rows=[dict(officeId=o,sites=[s for s in range(3) if a[s]==o],workers=[]) for o in allowed if o in a]
  x=val(d,rows)
  if not isinstance(x,str):best=max(best,x)
 f[str(allowed)]=best
assert list(f.values())==[10,10,10,12],f
(H/'data/oracle/non_submodular_offices.json').write_text(json.dumps(d))
d2=dict(sites=[S(0,.1,0),S(2,.1,0),S(1,1,1),S(1,-1,1),S(.8,.8,10)],offices=[dict(x=0,y=0,cost=0,maxSize=3),dict(x=2,y=0,cost=0,maxSize=3)],workers=[],distances=[[0]*5,[0]*5],maxDifference=5,balanceCoefficient=0)
checks={}
for pick in [2,3]:
 for future in [False,True]:
  rows=[dict(officeId=0,sites=[0,pick],workers=[]),dict(officeId=1,sites=[1]+([4] if future else []),workers=[])]
  checks[f'{pick}_{future}']=val(d2,rows)
assert checks=={'2_False':1.,'2_True':'Hull conflict','3_False':1.,'3_True':11.},checks
(H/'data/oracle/count_dominance.json').write_text(json.dumps(d2))
(H/'logs/pruning_witnesses.json').write_text(json.dumps(dict(office_values=f,count_dominance=checks),indent=2));print(f,checks)
