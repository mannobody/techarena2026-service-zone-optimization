"""Independent enumeration of entire assignments; never uses candidate internals."""
import json,random,itertools,subprocess,sys,os,time,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];ROOT=R.parents[1];sys.path.insert(0,str(ROOT/'task'));from validate_solution import validate
os.sched_setaffinity(0,{14,15});d=R/'logs/specialists_v3';d.mkdir(exist_ok=False);exe=R/'artifacts/v3/candidate'
while not (R/'artifacts/v3/COMPILED.json').exists():time.sleep(1)

def brute(a):
 ns=len(a['sites']);no=len(a['offices']);best=0.;available=set(k for w in a['workers']for k in w)
 for asg in itertools.product(range(-1,no),repeat=ns):
  mem=[[s for s,o in enumerate(asg)if o==i]for i in range(no)];opened=[o for o,m in enumerate(mem)if m]
  if any(len(mem[o])>a['offices'][o]['maxSize']for o in opened):continue
  if opened and max(len(mem[o])for o in opened)-min(len(mem[o])for o in opened)>a['maxDifference']:continue
  if any(any(k not in available for k in a['sites'][s]['tasks'])for s,o in enumerate(asg)if o>=0):continue
  # These generated instances have universal workers and >=no workers, or only one office.
  footprints=[];good=True
  points=[s['x']if a.get('_axis','x')=='x'else s['y']for s in a['sites']]+[o['x']if a.get('_axis','x')=='x'else o['y']for o in a['offices']]
  for o in opened:
   ends=[points[s]for s in mem[o]]+[points[ns+o]];lo,hi=min(ends),max(ends);foot={i for i,p in enumerate(points)if lo<=p<=hi}
   if any(foot&prev for prev in footprints):good=False;break
   footprints.append(foot)
  if not good:continue
  loads=[sum(len(a['sites'][s]['tasks'])for s in mem[o])for o in opened]
  obj=sum(a['sites'][s]['reward']-a['distances'][o][s]for s,o in enumerate(asg)if o>=0)-sum(a['offices'][o]['cost']for o in opened)-(a['balanceCoefficient']*(max(loads)-min(loads))if loads else 0)
  best=max(best,obj)
 return best

rows=[];rng=random.Random(11007)
for family,count in [('line',48),('single',32)]:
 for index in range(count):
  ns=3+index%4;no=2+index%3 if family=='line'else 1
  axis='y'if index%3==0 else'x';coords=[rng.randrange(-2,9)for _ in range(ns+no)]
  point=lambda t:dict(x=0 if axis=='y'else t,y=t if axis=='y'else 2*t+1)
  S=[dict(**point(coords[s]),reward=rng.randrange(1,16),tasks=[0]*(1+s%3))for s in range(ns)]
  O=[dict(**point(coords[ns+o]),cost=rng.randrange(9),maxSize=rng.randrange(ns+1))for o in range(no)]
  W=[[0,1]for _ in range(no)]
  if family=='single'and index%4==0:S[-1]['tasks']=[2]
  a=dict(sites=S,offices=O,workers=W,distances=[[rng.randrange(13)for _ in S]for o in O],maxDifference=ns if family=='line'else 0,balanceCoefficient=0 if family=='line'else rng.randrange(7),_axis=axis)
  expected=brute(a);inp=d/f'{family}_{index}.json';inp.write_text(json.dumps({k:v for k,v in a.items()if not k.startswith('_')}));out=d/f'{family}_{index}.solution.json';err=d/f'{family}_{index}.stderr'
  with err.open('w')as f:p=subprocess.run([str(exe),str(inp),str(out),'2'],stderr=f,env=dict(PATH=os.environ['PATH']),timeout=4)
  value=validate(inp,out);method='single_office_exact'if family=='single'else'collinear_interval_exact'
  row=dict(case=f'{family}_{index}',expected=expected,official=value,rc=p.returncode,route=method in err.read_text(),valid=isinstance(value,(int,float)),match=isinstance(value,(int,float))and abs(value-expected)<1e-7);rows.append(row)
  assert row['match']and row['valid']and row['route']and p.returncode==0,row
# Preconditions: each perturbation must reject the 1D exact route.
a=dict(sites=[dict(x=i,y=2*i,reward=10,tasks=[0])for i in range(20)],offices=[dict(x=i*6,y=i*12,cost=1,maxSize=10)for i in range(3)],workers=[[0]for _ in range(3)],distances=[[abs(i-o*6)for i in range(20)]for o in range(3)],maxDifference=20,balanceCoefficient=0)
import copy
for mode in ['near_line','balance','count','workers']:
 b=copy.deepcopy(a)
 if mode=='near_line':b['sites'][10]['y']+=1e-10
 if mode=='balance':b['balanceCoefficient']=1
 if mode=='count':b['maxDifference']=0
 if mode=='workers':b['workers']=[[0]]
 inp=d/(mode+'.json');inp.write_text(json.dumps(b));out=d/(mode+'.solution.json');err=d/(mode+'.stderr')
 with err.open('w')as f:p=subprocess.run([str(exe),str(inp),str(out),'1'],env=dict(PATH=os.environ['PATH']),stderr=f,timeout=4)
 v=validate(inp,out);row=dict(case=mode,rc=p.returncode,official=v,rejected_exact='method=collinear_interval_exact'not in err.read_text(),valid=isinstance(v,(int,float)));rows.append(row);assert row['rejected_exact']and row['valid']and p.returncode==0,row
(d/'results.json').write_text(json.dumps(rows,indent=2));print(json.dumps(dict(cases=len(rows),oracle_matches=80,guard_rejections=4,valid=sum(x['valid']for x in rows))),flush=True)
