import itertools,json,sys
from fractions import Fraction
from shapely import MultiPoint,Point
from oracle import R,instance,official,enumerate_all
from mip import improve

dest=R/'logs/extra_cases';dest.mkdir(exist_ok=False);rows=[]
d=instance([(0,-1),(2,-1),(4,-1),(6,-1),(0,3)],[(0,0),(2,0),(4,0),(6,0)],
    [[0,100,100,100,0],[100,0,100,100,1],[100,100,0,100,2],[100,100,100,0,3]],A=1)
for o in range(3):d['offices'][o]['maxSize']=1
d['offices'][3]['maxSize']=2
inc=[dict(officeId=o,sites=[o],workers=[o]) for o in range(4)]
assert official(d,inc)==36
(R/'inputs/fourth_office.json').write_text(json.dumps(d));(R/'solutions/fourth_office.json').write_text(json.dumps(inc))
oracle=enumerate_all(d,inc=inc,selected=[4]);assert oracle['value']==43
from legacy_mip import improve as legacy
for backend in ['scip','highs']:
    old=legacy(d,inc,seconds=3,budget=1,backend=backend,selected=[4]);new=improve(d,inc,[4],backend=backend,seconds=3,export=R/'models'/f'fourth_{backend}')
    assert old['value']==36 and new['value']==43
    rows.append(dict(case='fourth_office',backend=backend,legacy=old,full=new,oracle=oracle['value']))

d=instance([(-3,1),(3,1),(3,2)],[(-3,0),(3,0)],[[0,1000,1000],[1000,0,5]],
    tasks=[[0]*10,[0],[0]*9],A=1,alpha=10)
for s,reward in zip(d['sites'],[200,100,0]):s['reward']=reward
inc=[dict(officeId=0,sites=[0],workers=[0]),dict(officeId=1,sites=[1],workers=[1])]
assert official(d,inc)==208
(R/'inputs/negative_profit_balance.json').write_text(json.dumps(d));(R/'solutions/negative_profit_balance.json').write_text(json.dumps(inc))
oracle=enumerate_all(d);assert oracle['value']==293
for backend in ['scip','highs']:
    v=improve(d,inc,[2],kind='geometry',backend=backend,seconds=3,export=R/'models'/f'negative_profit_{backend}')
    assert v['value']==293;rows.append(dict(case='negative_profit_balance',backend=backend,result=v,oracle=293))

# Strict per-skill counts are only necessary: two workers cannot staff three
# disjoint offices even when each required skill has an available worker.
workers=[[0,1],[1,2]];needs=[{0},{1},{2}]
assert all(sum(k in r for r in needs)<=sum(k in w for w in workers) for k in range(3))
feasible=any(all(r<={k for w,q in enumerate(a) if q==o for k in workers[w]} for o,r in enumerate(needs))
    for a in itertools.product(range(-1,3),repeat=2))
assert not feasible;rows.append(dict(case='skill_counts_insufficient',counts_pass=True,exact_staffing=False))

# Independent geometry oracle via Caratheodory, exact rational predicates; no
# common hull algorithm with GEOS or native monotone chain. Includes boundaries.
def cross(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
def covers(vertices,p):
    if p in vertices:return True
    for a,b in itertools.combinations(vertices,2):
        if cross(a,b,p)==0 and min(a[0],b[0])<=p[0]<=max(a[0],b[0]) and min(a[1],b[1])<=p[1]<=max(a[1],b[1]):return True
    for a,b,c in itertools.combinations(vertices,3):
        if cross(a,b,c)==0:continue
        z=[cross(a,b,p),cross(b,c,p),cross(c,a,p)]
        if min(z)>=0 or max(z)<=0:return True
    return False
checks=0
records=json.loads((R/'logs/oracle/results.json').read_text())
for row in records:
    d=json.loads((R/'inputs'/f"{row['case']}.json").read_text());xy=[(x['x'],x['y']) for x in d['sites']+d['offices']]
    for size in range(1,min(4,len(xy))+1):
        for ids in itertools.combinations(range(len(xy)),size):
            verts=[xy[i] for i in ids];h=MultiPoint(verts).convex_hull
            for p in xy:
                assert covers(verts,p)==h.covers(Point(p)),(row['case'],ids,p);checks+=1
# Explicit binary64 near-boundary and subnormal probes.
sets=[[(0.,0.),(1.,1.),(2.,2.+2**-50)],[(0.,0.),(2**-500,0.),(0.,2**-500)]]
for verts in sets:
    h=MultiPoint(verts).convex_hull
    for p in verts+[(0.5,0.5),(2**-501,2**-501)]:
        exact=lambda v:tuple(Fraction(x) for x in v)
        result=covers(list(map(exact,verts)),exact(p));geos=h.covers(Point(p))
        rows.append(dict(case='numeric_probe',vertices=verts,point=p,exact=result,geos=geos));checks+=1
rows.append(dict(case='independent_geometry',checks=checks))
(dest/'results.json').write_text(json.dumps(rows,indent=2));print(json.dumps(dict(records=len(rows),geometry_checks=checks)))
