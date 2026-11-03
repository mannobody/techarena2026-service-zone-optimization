import json,subprocess
from bench import H,V
rows=[]
for blocker in [False,True]:
 xy=[(-.9,-.9),(-.9,.9),(1,1),(1,-1)]+([(0,0)] if blocker else [])
 data=dict(sites=[dict(x=x,y=y,reward=1 if i<2 else 10,tasks=[]) for i,(x,y) in enumerate(xy)],offices=[dict(x=-1,y=y,cost=0,maxSize=2) for y in [-1,1]],workers=[],distances=[[0,20,0,20]+([100] if blocker else []),[20,0,20,0]+([100] if blocker else [])],maxDifference=0,balanceCoefficient=0)
 p=H/'data/oracle'/f'cross_balance_{blocker}.json';p.write_text(json.dumps(data));a=p.with_suffix('.asg');a.write_text('0 1 -1 -1'+(' -1' if blocker else '')+' 2 2 3')
 result=json.loads(subprocess.check_output([str(H/'artifacts/oracle'),str(p),str(a),'1'],text=True));expected=2 if blocker else 22
 assert result['valid'] and result['score']==expected,result
 solution=[dict(officeId=o,sites=[o] if blocker else [o,o+2],workers=[]) for o in range(2)]
 score=V.validate_solution(V.Instance.model_validate(data),[V.OpenedOffice.model_validate(r) for r in solution]);assert score==expected
 rows.append(dict(blocker=blocker,expected=expected,input=str(p),native=result,official_score=score))
(H/'logs/cross_balance_witness.json').write_text(json.dumps(rows,indent=2));print(rows)
