import json
from oracle import R,instance,official
xy=[(-3,i/10+1) for i in range(6)]+[(3,i/10+1) for i in range(6)]
d=instance(xy,[(-4,0),(4,0)],[[0]*6+[9]*6,[9]*6+[0]*6],A=0,cost=3,cap=12)
inc=[dict(officeId=0,sites=list(range(12)),workers=[0])]
sol=[dict(officeId=0,sites=list(range(6)),workers=[0]),dict(officeId=1,sites=list(range(6,12)),workers=[1])]
assert official(d,inc)==63 and official(d,sol)==114
for name,data,incumbent in [('large_A0_open',d,inc)]:
    (R/'inputs'/f'{name}.json').write_text(json.dumps(data));(R/'solutions'/f'{name}.json').write_text(json.dumps(incumbent))
d=instance([(0,1),(2,1),(4,0)],[(0,0),(2,0)],[[0,100,0],[100,0,1]],A=1,cap=2)
inc=[dict(officeId=i,sites=[i],workers=[i]) for i in range(2)]
assert official(d,inc)==18
(R/'inputs/fill_geo_fallback.json').write_text(json.dumps(d));(R/'solutions/fill_geo_fallback.json').write_text(json.dumps(inc))
print('Barrier cases saved: A0 opening 63->114, geometry fallback 18->27.')
