import json,math
from pathlib import Path
R=Path(__file__).resolve().parent
xs=[1,2,4,9,21,22,6,7];off=[0,10,20]
profits=[[10,10,0,0,-100,-100,100,-100],[-100,-100,10,10,-100,-100,-100,-5],[-100,-100,-100,-100,10,10,-100,-100]]
d=dict(sites=[dict(x=x,y=0,reward=100,tasks=[]) for x in xs],offices=[dict(x=x,y=0,cost=0,maxSize=2) for x in off],workers=[],distances=[[100-p for p in a] for a in profits],maxDifference=0,balanceCoefficient=0)
s=[dict(officeId=o,sites=[2*o,2*o+1],workers=[]) for o in range(3)]
(R/'inputs/padding_witness.json').write_text(json.dumps(d));(R/'inputs/padding_witness.solution.json').write_text(json.dumps(s))
