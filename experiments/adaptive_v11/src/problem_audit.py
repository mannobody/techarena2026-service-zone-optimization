"""Fresh hand calculations against primary validator; no solver tuning or quality trial."""
from pathlib import Path
import copy,hashlib,json,os,sys
R=Path(__file__).resolve().parents[1];ROOT=R.parents[1];os.sched_setaffinity(0,{14,15});sys.path.insert(0,str(ROOT/'task'))
from validate_solution import Instance,OpenedOffice,validate_solution
S=lambda x,y,r=10,t=():dict(x=x,y=y,reward=r,tasks=list(t))
O=lambda x,y,c=0,m=20:dict(x=x,y=y,cost=c,maxSize=m)
def I(s,o,w=(),D=None,A=20,alpha=0):return dict(sites=s,offices=o,workers=list(w),distances=D if D is not None else[[0]*len(s)for _ in o],maxDifference=A,balanceCoefficient=alpha)
def sol(*xs):return[dict(officeId=o,sites=list(s),workers=list(w))for o,s,w in xs]
a=[]
def check(name,i,s,e):
 v=validate_solution(Instance.model_validate(i),[OpenedOffice.model_validate(x)for x in s]);assert v==e,(name,v,e)
 a.append(copy.deepcopy(dict(name=name,instance=i,solution=s,expected=e,official=v)))
check('profitable',I([S(1,0)],[O(0,0,2)],D=[[3]]),sol((0,[0],[])),5)
check('unprofitable',I([S(1,0)],[O(0,0,2)],D=[[13]]),sol((0,[0],[])),-5)
check('empty',I([S(1,0)],[O(0,0,2)]),[],0)
i=I([S(-2,0,10,[0]*4),S(2,0,10,[0])],[O(-3,0,2),O(3,0,3)],[[0],[0]],A=0)
check('open_two_offices_cost5',i,sol((0,[0],[0]),(1,[1],[1])),15)
i['balanceCoefficient']=100;check('equal_site_count_unequal_task_load',i,sol((0,[0],[0]),(1,[1],[1])),-285)
b=I([S(-2,0,20,[0]*4),S(2,0,20,[0]),S(3,1,1,[0]*3)],[O(-3,0),O(4,0)],[[0],[0]],D=[[0,99,99],[99,0,6]],alpha=10,A=1)
check('before_negative',b,sol((0,[0],[0]),(1,[1],[1])),10)
check('negative_site_reduces_penalty',b,sol((0,[0],[0]),(1,[1,2],[1])),35)
check('capacity_counts_sites',I([S(1,0,10,[0]*20)],[O(0,0,m=1)],[[0]]),sol((0,[0],[0])),10)
check('capacity_violation',I([S(1,0),S(2,0)],[O(0,0,m=1)]),sol((0,[0,1],[])),'Office capacity exceeded')
check('site_count_imbalance',b|{'maxDifference':0},sol((0,[0],[0]),(1,[1,2],[1])),'Site-count imbalance')
check('actual_worker_required',i,sol((0,[0],[])),'Missing skills')
c=I([S(1,0),S(0,1)],[O(-1,0),O(0,-1)])
check('crossing_without_input_point_allowed',c,sol((0,[0],[]),(1,[1],[])),20)
check('unassigned_site_on_both_boundaries',c|{'sites':c['sites']+[S(0,0)],'distances':[[0,0,0],[0,0,0]]},sol((0,[0],[]),(1,[1],[])),'Hull conflict')
check('closed_office_on_both_boundaries',c|{'offices':c['offices']+[O(0,0)],'distances':c['distances']+[[0,0]]},sol((0,[0],[]),(1,[1],[])),'Hull conflict')
check('worker_cannot_be_shared',I([S(-1,0,10,[0]),S(1,0,10,[1])],[O(-2,0),O(2,0)],[[0,1]]),sol((0,[0],[0]),(1,[1],[0])),'Duplicate worker')
(R/'PROBLEM_AUDIT.json').write_text(json.dumps(dict(primary_sources={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()for p in[ROOT/'task/Techarena.pdf',ROOT/'task/validate_solution.py']},direction='maximize',formula='reward-distance-open_cost-alpha*(max_task_load-min_task_load)',geometry='all input sites and offices, covers includes boundaries; hull intersections without shared input points allowed',tests=a),indent=2))
print('Primary hand checks:',len(a),'passed')
