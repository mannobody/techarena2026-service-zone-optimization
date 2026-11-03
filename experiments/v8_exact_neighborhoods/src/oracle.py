"""Independent exhaustive oracle: enumerate worker assignments FIRST, then sites.
No halfplanes, candidate lists, hull-separation or skill-sum approximations.
Geometry via official Shapely; objective/capacity/count/load independently computed.
"""
import itertools,json,math,random,sys,time
from pathlib import Path
from shapely import MultiPoint,Point
R=Path(__file__).resolve().parents[1];ROOT=R.parents[1];sys.path.insert(0,str(ROOT/'task'))
from validate_solution import Instance,OpenedOffice,validate_solution

def official(d,sol):return validate_solution(Instance.model_validate(d),[OpenedOffice.model_validate(x) for x in sol])
def enumerate_all(d,inc=None,selected=None,ops=None,kind='structure'):
    n=len(d['sites']);m=len(d['offices']);nw=len(d['workers']);A=d['maxDifference'];alpha=d['balanceCoefficient']
    assert alpha>=0 and all(o['cost']>=0 for o in d['offices'])
    selected=list(range(n)) if selected is None else selected;ops=list(range(m)) if ops is None else ops
    old={s:r['officeId'] for r in inc or [] for s in r['sites']};oldops={r['officeId'] for r in inc or []}
    # Explicit worker allocations; a worker covers any number of tasks, but only
    # in its single assigned office. Cache all resulting sets with certificates.
    certificates={}
    for wa in itertools.product(range(-1,m),repeat=nw):
        have=[set() for _ in range(m)]
        for w,o in enumerate(wa):
            if o>=0:have[o].update(d['workers'][w])
        key=tuple(frozenset(v) for v in have);certificates.setdefault(key,wa)
    xy=[(s['x'],s['y']) for s in d['sites']]+[(o['x'],o['y']) for o in d['offices']];points=list(map(Point,xy))
    hullcache={};best=-math.inf;bestsol=[];valid=0;tested=0;crossings=0
    for path in itertools.product([-1]+ops,repeat=len(selected)):
        assignment=[old.get(s,-1) for s in range(n)]
        for s,o in zip(selected,path):assignment[s]=o
        mem={o:[s for s,q in enumerate(assignment) if q==o] for o in range(m)};active=[o for o in range(m) if mem[o]]
        if kind=='geometry' and set(active)!=oldops:continue
        if any(len(mem[o])>d['offices'][o]['maxSize'] for o in active):continue
        counts=[len(mem[o]) for o in active]
        if counts and max(counts)-min(counts)>A:continue
        tested+=1;need=[frozenset(k for s in mem[o] for k in d['sites'][s]['tasks']) for o in range(m)]
        wa=next((cert for have,cert in certificates.items() if all(need[o]<=have[o] for o in range(m))),None)
        if wa is None:continue
        covers=[];hulls=[]
        for o in active:
            key=(o,tuple(mem[o]))
            if key not in hullcache:
                h=MultiPoint([xy[n+o]]+[xy[s] for s in mem[o]]).convex_hull
                hullcache[key]=(h,{q for q,p in enumerate(points) if h.covers(p)})
            h,c=hullcache[key];hulls.append(h);covers.append(c)
        if any(a&b for a,b in itertools.combinations(covers,2)):continue
        valid+=1
        if any(a.intersects(b) for a,b in itertools.combinations(hulls,2)):crossings+=1
        loads=[sum(len(d['sites'][s]['tasks']) for s in mem[o]) for o in active]
        val=sum(d['sites'][s]['reward']-d['distances'][o][s] for o in active for s in mem[o])-sum(d['offices'][o]['cost'] for o in active)-alpha*(max(loads)-min(loads) if loads else 0)
        if val>best:
            best=val;bestsol=[dict(officeId=o,sites=mem[o],workers=[w for w,q in enumerate(wa) if q==o]) for o in active]
    v=official(d,bestsol);assert isinstance(v,(float,int)) and abs(v-best)<1e-6,(v,best)
    return dict(value=best,solution=bestsol,valid_assignments=valid,tested=tested,valid_crossings=crossings)

def instance(xy,oxy,D=None,tasks=None,workers=None,cost=1,A=10,alpha=0,cap=10):
    return dict(sites=[dict(x=x,y=y,reward=10,tasks=tasks[i] if tasks else [0]) for i,(x,y) in enumerate(xy)],
        offices=[dict(x=x,y=y,cost=cost,maxSize=cap) for x,y in oxy],workers=[[0] for _ in oxy] if workers is None else workers,
        distances=D if D is not None else [[0 for _ in xy] for _ in oxy],maxDifference=A,balanceCoefficient=alpha)

def fixtures():
    d=instance([(2,0),(0,2)],[(-2,0),(0,-2)],[[0,30],[30,0]],A=0)
    sol=[dict(officeId=i,sites=[i],workers=[i]) for i in range(2)]
    cases={'cross_segments':(d,sol,18)}
    d=instance([(3,-1),(0,3),(-3,2),(3,2)],[(-3,-1),(0,-2)],[[0,0,30,30],[30,30,0,0]],A=0)
    sol=[dict(officeId=0,sites=[0,1],workers=[0]),dict(officeId=1,sites=[2,3],workers=[1])]
    cases['cross_triangles']=(d,sol,38)
    for name,q in [('unassigned_witness',(0,0)),('boundary_witness',(0,0))]:
        d=instance([(2,0),(0,2),q],[(-2,0),(0,-2)],[[0,30,30],[30,0,30]])
        sol=[dict(officeId=i,sites=[i],workers=[i]) for i in range(2)]
        cases[name]=(d,sol,'Hull conflict')
    d=instance([(2,0),(0,2)],[(-2,0),(0,-2),(0,0)],[[0,30],[30,0],[30,30]])
    cases['closed_office_witness']=(d,[dict(officeId=i,sites=[i],workers=[i]) for i in range(2)],'Hull conflict')
    d=instance([(1,0),(2,0)],[(-1,0),(3,0)],[[0,30],[30,0]])
    cases['disjoint_collinear']=(d,[dict(officeId=i,sites=[i],workers=[i]) for i in range(2)],18)
    d=instance([(2,0),(1,0)],[(-1,0),(3,0)],[[0,30],[30,0]])
    cases['overlap_collinear']=(d,[dict(officeId=i,sites=[i],workers=[i]) for i in range(2)],'Hull conflict')
    d=instance([(0,0),(0,0)],[(-1,0),(1,0)])
    cases['coincident_boundary']=(d,[dict(officeId=i,sites=[i],workers=[i]) for i in range(2)],'Hull conflict')
    # A=0, a two-site opening package with one rare worker reassignment.
    d=instance([(-3,0),(-2,1),(2,1),(3,0)],[(-4,0),(4,0)],[[0,0,9,9],[9,9,0,0]],tasks=[[0],[0],[1],[1]],workers=[[0,1],[1]],A=0,cost=3)
    cases['joint_open_workers']=(d,[dict(officeId=0,sites=[0,1,2,3],workers=[0])],None)
    # Single count/load changes fail; full exchange changes two workers and both sites.
    d=instance([(-2,1),(2,1)],[(-3,0),(3,0)],[[9,0],[0,9]],tasks=[[0],[1]],workers=[[0],[1]],A=0)
    cases['joint_exchange']=(d,[dict(officeId=i,sites=[i],workers=[i]) for i in range(2)],None)
    # Per-skill counts hold, but all workers cannot cover all three offices jointly.
    d=instance([(-4,1),(0,1),(4,1)],[(-4,0),(0,0),(4,0)],tasks=[[0,1],[1,2],[0,2]],workers=[[0,1],[1,2],[0,2]],A=0)
    cases['skill_counts_insufficient']=(d,[],0)
    return cases

def run():
    out=R/'logs/oracle';out.mkdir(exist_ok=False); records=[]
    for name,(d,sol,expect) in fixtures().items():
        (R/'inputs'/f'{name}.json').write_text(json.dumps(d));(R/'solutions'/f'{name}.json').write_text(json.dumps(sol))
        v=official(d,sol)
        if expect is not None:assert v==expect,(name,v,expect)
        if isinstance(v,str):sol=[]
        r=enumerate_all(d);records.append(dict(case=name,fixture_validation=v,oracle=r))
    rng=random.Random(20261020)
    for i in range(30):
        n=rng.randrange(2,6);m=rng.randrange(1,4);nw=rng.randrange(0,4)
        xy=[(rng.randrange(-3,4),rng.randrange(-3,4)) for _ in range(n+m)]
        d=instance(xy[:n],xy[n:],[[rng.randrange(0,13) for s in range(n)] for o in range(m)],
            tasks=[[rng.randrange(3) for k in range(rng.randrange(0,4))] for s in range(n)],
            workers=[rng.sample(range(3),rng.randrange(1,4)) for w in range(nw)],
            cost=rng.randrange(0,7),A=rng.randrange(0,n+1),alpha=rng.choice([0,.1,10,100]),cap=rng.randrange(0,n+1))
        name=f'random{i:02d}';(R/'inputs'/f'{name}.json').write_text(json.dumps(d));r=enumerate_all(d)
        records.append(dict(case=name,fixture_validation=None,oracle=r))
    (out/'results.json').write_text(json.dumps(records,indent=2))
    print(json.dumps(dict(cases=len(records),valid_crossings=sum(r['oracle']['valid_crossings'] for r in records))))

if __name__=='__main__':run()
