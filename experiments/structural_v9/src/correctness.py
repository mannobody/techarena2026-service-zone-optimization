"""Independent assignment enumeration and official-validator hand calculations."""
import itertools,json,math,os,random,subprocess,sys,time
from pathlib import Path
from shapely import MultiPoint,Point
R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
sys.path.insert(0,str(ROOT/'task'))
from validate_solution import Instance,OpenedOffice,validate_solution,validate
S=lambda x,y,r=10,t=():dict(x=x,y=y,reward=r,tasks=list(t))
O=lambda x,y,c=0,m=20:dict(x=x,y=y,cost=c,maxSize=m)
def inst(s,o,w=(),D=None,A=20,alpha=0):
    if D is None:D=[[0 for _ in s]for _ in o]
    return dict(sites=s,offices=o,workers=list(w),distances=D,maxDifference=A,balanceCoefficient=alpha)
def sol(*offices):return [dict(officeId=o,sites=list(s),workers=list(w)) for o,s,w in offices]
def official(i,s):return validate_solution(Instance.model_validate(i),[OpenedOffice.model_validate(o)for o in s])
def oracle(i):
    """Enumerate site->office labels, independent of the C++ zone-master DFS.
    Precompute Shapely footprints; enumerate worker->office allocations exactly.
    """
    n=len(i['sites']);m=len(i['offices']);nw=len(i['workers'])
    pts=[Point(s['x'],s['y'])for s in i['sites']]+[Point(o['x'],o['y'])for o in i['offices']]
    masks={};zskill={};loads={};profit={}
    for o in range(m):
        for mask in range(1,1<<n):
            xs=[x for x in range(n)if mask>>x&1]
            if len(xs)>i['offices'][o]['maxSize']:continue
            h=MultiPoint([pts[x]for x in xs]+[pts[n+o]]).convex_hull
            masks[o,mask]=sum(1<<p for p,pt in enumerate(pts)if h.covers(pt))
            zskill[o,mask]=frozenset(t for x in xs for t in i['sites'][x]['tasks'])
            loads[o,mask]=sum(len(i['sites'][x]['tasks'])for x in xs)
            profit[o,mask]=sum(i['sites'][x]['reward']-i['distances'][o][x]for x in xs)-i['offices'][o]['cost']
    teams=set()
    for a in itertools.product(range(-1,m),repeat=nw):
        teams.add(tuple(frozenset(k for w in range(nw)if a[w]==o for k in i['workers'][w])for o in range(m)))
    best=0;certificate=[];feasible=0
    for labels in itertools.product(range(-1,m),repeat=n):
        chosen=[sum(1<<x for x in range(n)if labels[x]==o)for o in range(m)]
        opened=[o for o in range(m)if chosen[o]]
        if not opened:continue
        counts=[mask.bit_count()for mask in chosen if mask]
        if max(counts)-min(counts)>i['maxDifference']:continue
        if any((o,chosen[o])not in masks for o in opened):continue
        used=0;ok=True
        for o in opened:
            c=masks[o,chosen[o]]
            if c&used:ok=False;break
            used|=c
        if not ok:continue
        needs=[zskill.get((o,chosen[o]),frozenset())for o in range(m)]
        if not any(all(needs[o]<=p[o]for o in opened)for p in teams):continue
        feasible+=1;ld=[loads[o,chosen[o]]for o in opened]
        v=sum(profit[o,chosen[o]]for o in opened)-i['balanceCoefficient']*(max(ld)-min(ld))
        if v>best:best=v;certificate=list(labels)
    return dict(objective=best,site_labels=certificate,feasible=feasible)
def main():
    dest=R/'logs/correctness';dest.mkdir(exist_ok=False)
    hand=[]
    def check(name,i,s,expect):
        v=official(i,s);ok=v==expect if isinstance(expect,str)else isinstance(v,(int,float))and abs(v-expect)<1e-8
        assert ok,(name,v,expect)
        hand.append(dict(name=name,instance=i,solution=s,expected=expect,official=v))
    check('profitable',inst([S(1,0)], [O(0,0,2)],D=[[3]]),sol((0,[0],[])),5)
    check('unprofitable',inst([S(1,0)], [O(0,0,2)],D=[[13]]),sol((0,[0],[])),-5)
    check('empty',inst([S(1,0)], [O(0,0,2)]),[],0)
    a=inst([S(-2,0,10,[0]*4),S(2,0,10,[0])],[O(-3,0,2),O(3,0,3)],[[0],[0]],alpha=0,A=0)
    check('extra_office_cost',a,sol((0,[0],[0]),(1,[1],[1])),15)
    a['balanceCoefficient']=100
    check('task_not_site_balance',a,sol((0,[0],[0]),(1,[1],[1])),-285)
    b=inst([S(-2,0,20,[0]*4),S(2,0,20,[0]),S(3,1,1,[0]*3)],[O(-3,0),O(4,0)],[[0],[0]],D=[[0,99,99],[99,0,6]],alpha=10,A=1)
    check('before_negative',b,sol((0,[0],[0]),(1,[1],[1])),10)
    check('negative_improves_global_balance',b,sol((0,[0],[0]),(1,[1,2],[1])),35)
    check('site_capacity',inst([S(1,0,10,[0]*20)],[O(0,0,m=1)],[[0]]),sol((0,[0],[0])),10)
    check('capacity_violation',inst([S(1,0),S(2,0)],[O(0,0,m=1)]),sol((0,[0,1],[])),'Office capacity exceeded')
    check('site_count_imbalance',b|{'maxDifference':0},sol((0,[0],[0]),(1,[1,2],[1])),'Site-count imbalance')
    check('real_worker_needed',a,sol((0,[0],[])),'Missing skills')
    cross=inst([S(1,0),S(0,1)],[O(-1,0),O(0,-1)])
    check('crossing_segments_allowed',cross,sol((0,[0],[]),(1,[1],[])),20)
    free=cross|{'sites':cross['sites']+[S(0,0)],'distances':[[0,0,0],[0,0,0]]}
    check('free_point_on_boundaries',free,sol((0,[0],[]),(1,[1],[])),'Hull conflict')
    closed=cross|{'offices':cross['offices']+[O(0,0)],'distances':cross['distances']+[[0,0]]}
    check('closed_office_on_boundaries',closed,sol((0,[0],[]),(1,[1],[])),'Hull conflict')
    check('workers_cannot_be_shared',inst([S(-1,0,10,[0]),S(1,0,10,[1])],[O(-2,0),O(2,0)],[[0,1]]),sol((0,[0],[0]),(1,[1],[0])),'Duplicate worker')
    (dest/'hand.json').write_text(json.dumps(hand,indent=2))
    rows=[]
    cases={x['name']:x['instance']for x in hand if x['name']in ['crossing_segments_allowed','negative_improves_global_balance']}
    for seed in range(36):
        r=random.Random(910000+seed);n=r.randint(3,7);m=r.randint(2,3);nw=r.randint(0,5)
        sites=[S(r.randrange(9),r.randrange(9),r.randrange(1,21),[r.randrange(3)for _ in range(r.randrange(5))])for _ in range(n)]
        offices=[O(r.randrange(-2,11),r.randrange(-2,11),r.randrange(0,7),r.randrange(1,n+1))for _ in range(m)]
        w=[r.sample(range(3),r.randrange(1,4))for _ in range(nw)]
        cases[f'oracle_{seed:02}']=inst(sites,offices,w,[[r.randrange(0,24)for _ in range(n)]for _ in range(m)],r.randrange(n+1),r.choice([0,0.1,5,100]))
    for name,i in cases.items():
        path=R/'inputs'/f'{name}.json';path.write_text(json.dumps(i));expected=oracle(i)
        out=dest/f'{name}.solution.json';err=dest/f'{name}.stderr'
        with err.open('w')as f:
            p=subprocess.run(['taskset','-c','14,15',str(R/'artifacts/candidate'),str(path),str(out),'2'],env={'PATH':os.environ['PATH'],'NT':'2','SEED':'901'},stderr=f,timeout=4)
        v=validate(path,out);log=err.read_text();complete='full=1 complete=1'in log
        ok=p.returncode==0 and isinstance(v,(int,float))and abs(v-expected['objective'])<1e-7 and complete
        rows.append(dict(name=name,oracle=expected,official=v,complete=complete,rc=p.returncode,ok=ok))
        if not ok:print(json.dumps(rows[-1]),flush=True)
    (dest/'oracle.json').write_text(json.dumps(rows,indent=2))
    print(json.dumps(dict(hand=len(hand),oracle=len(rows),passed=sum(r['ok']for r in rows))))
    assert all(r['ok']for r in rows)
if __name__=='__main__':main()
