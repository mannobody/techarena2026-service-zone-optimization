"""Complete local core+subset model, CP-SAT vs SCIP vs native B&B.
All masks are enumerated; bounds are conditional on fixed cores/domains.
Model-building and footprint computation count towards wall time.
"""
import json,time,subprocess,itertools,math
from pathlib import Path
import numpy as np
from shapely import MultiPoint,points,covers
from ortools.sat.python import cp_model
from pyscipopt import Model,quicksum
from bench import V,H

def prepare(data,sol,q):
 n=len(data['sites']);by={r['officeId']:r for r in sol};ops=list(by)
 if len(ops)<2:return None
 xy=np.array([(p['x'],p['y']) for p in data['sites']+data['offices']]);ps=points(xy)
 # Pick the nearest pair of active office centroids, then sites nearest the midpoint.
 cent={o:xy[by[o]['sites']].mean(axis=0) for o in ops}
 a,b=min(itertools.combinations(ops,2),key=lambda p:np.linalg.norm(cent[p[0]]-cent[p[1]]));target=[a,b];center=(cent[a]+cent[b])/2
 owner={s:o for o,r in by.items() for s in r['sites']};rem={o:len(r['sites']) for o,r in by.items()};xs=[]
 for x in sorted(range(n),key=lambda x:np.linalg.norm(xy[x]-center)):
  o=owner.get(x,-1)
  if o>=0 and (o not in target or rem[o]<=1):continue
  xs.append(x)
  if o>=0:rem[o]-=1
  if len(xs)>=q:break
 core={o:[x for x in r['sites'] if x not in xs] for o,r in by.items()}
 outside=set()
 for o in ops:
  if o not in target:
   hull=MultiPoint(xy[core[o]+[n+o]]).convex_hull;outside.update(np.flatnonzero(covers(hull,ps)).tolist())
 cols=[]
 for o in target:
  for mask in range(1<<len(xs)):
   ss=core[o]+[x for j,x in enumerate(xs) if mask>>j&1]
   if len(ss)>data['offices'][o]['maxSize']:continue
   need=set(k for x in ss for k in data['sites'][x]['tasks'])
   if any(not any(k in w for w in data['workers']) for k in need):continue
   hull=MultiPoint(xy[ss+[n+o]]).convex_hull;fp=set(np.flatnonzero(covers(hull,ps)).tolist())
   if fp&outside:continue
   cols.append(dict(o=o,mask=mask,ss=ss,fp=fp,need=need,count=len(ss),load=sum(len(data['sites'][x]['tasks']) for x in ss),profit=sum(data['sites'][x]['reward']-data['distances'][o][x] for x in ss)-data['offices'][o]['cost']))
 return target,xs,core,cols

def solve(data,sol,prep,kind,seconds=2):
 target,xs,core,cols=prep;by={r['officeId']:r for r in sol};ops=list(by);nw=len(data['workers'])
 if kind=='cp':
  m=cp_model.CpModel();bv=lambda name:m.new_bool_var(name);add=m.add;su=sum
 else:
  m=Model();m.hideOutput();m.setIntParam('parallel/maxnthreads',1);bv=lambda name:m.addVar(vtype='B',name=name);add=lambda c: None if c is True else m.addCons(c);su=quicksum
 y=[bv(f'y{j}') for j in range(len(cols))];u={(o,w):bv(f'u{o}_{w}') for o in ops for w in range(nw)}
 for o in target:add(su(y[j] for j,c in enumerate(cols) if c['o']==o)==1)
 for w in range(nw):add(su(u[o,w] for o in ops)<=1)
 for j,c in enumerate(cols):
  for k in c['need']:add(y[j]<=su(u[c['o'],w] for w,ks in enumerate(data['workers']) if k in ks))
 for o in ops:
  if o not in target:
   for k in set(k for x in core[o] for k in data['sites'][x]['tasks']):add(su(u[o,w] for w,ks in enumerate(data['workers']) if k in ks)>=1)
 # Shared point footprint constraints also prohibit assigning one site twice.
 occupancy={}
 for j,c in enumerate(cols):
  for p in c['fp']:occupancy.setdefault(p,[]).append(j)
 seen=set()
 for indices in occupancy.values():
  key=tuple(indices)
  if key in seen or len({cols[j]['o'] for j in key})<2:continue
  seen.add(key);add(su(y[j] for j in key)<=1)
 sizes={o:su(c['count']*y[j] for j,c in enumerate(cols) if c['o']==o) if o in target else len(core[o]) for o in ops}
 loads={o:su(c['load']*y[j] for j,c in enumerate(cols) if c['o']==o) if o in target else sum(len(data['sites'][x]['tasks']) for x in core[o]) for o in ops}
 for a,b in itertools.combinations(ops,2):add(sizes[a]-sizes[b]<=data['maxDifference']);add(sizes[b]-sizes[a]<=data['maxDifference'])
 T=sum(len(s['tasks']) for s in data['sites'])
 if kind=='cp':hi=m.new_int_var(0,T,'hi');lo=m.new_int_var(0,T,'lo')
 else:hi=m.addVar(lb=0,ub=T);lo=m.addVar(lb=0,ub=T)
 for o in ops:add(hi>=loads[o]);add(lo<=loads[o])
 add(hi>=lo)
 # Float objective supported by installed OR-Tools; verify original objective externally.
 objective=su(c['profit']*y[j] for j,c in enumerate(cols))-data['balanceCoefficient']*(hi-lo)
 if kind=='cp':
  m.maximize(objective);solver=cp_model.CpSolver();solver.parameters.max_time_in_seconds=seconds;solver.parameters.num_search_workers=1;solver.parameters.random_seed=7
  status=solver.solve(m);name=solver.status_name(status);value=lambda v:solver.value(v)
  have=status in (cp_model.OPTIMAL,cp_model.FEASIBLE);nodes=solver.num_branches;bound=solver.best_objective_bound
 else:
  m.setObjective(objective,'maximize');m.setRealParam('limits/time',seconds);m.optimize();name=str(m.getStatus());have=m.getBestSol() is not None;value=m.getVal;nodes=m.getNNodes();bound=m.getDualbound()
 answer=sol
 if have:
  chosen={c['o']:c['ss'] for j,c in enumerate(cols) if value(y[j])>.5}
  answer=[dict(officeId=o,sites=chosen.get(o,core[o]),workers=[w for w in range(nw) if value(u[o,w])>.5]) for o in ops]
 score=V.validate_solution(V.Instance.model_validate(data),[V.OpenedOffice.model_validate(r) for r in answer]);assert not isinstance(score,str),score
 return dict(score=score,status=name,nodes=nodes,conditional_bound_excludes_fixed_profit=bound,solution=answer)

if __name__=='__main__':
 log=H/'logs/cp_compare_v2';log.mkdir();rows=[]
 for case in ['alphabig0','anti1','tightA0','multiskill0','latent0','large0']:
  inp=H/'data/train'/f'{case}.json';data=json.loads(inp.read_text());sol=json.loads((H/'logs/screen_v1'/f'{case}_1_base.json').read_text())
  for q in [6,10]:
   t=time.perf_counter();prep=prepare(data,sol,q);build=time.perf_counter()-t
   if prep is None:continue
   target,xs,core,cols=prep;asg=[-1]*len(data['sites'])
   for r in sol:
    for x in r['sites']:asg[x]=r['officeId']
   # Native oracle branches across all active offices, so restrict outside domains
   # by using only pair-active solutions? Instead an explicit ops suffix supported below.
   ap=log/f'{case}_{q}.asg';ap.write_text(' '.join(map(str,asg))+f' {len(xs)} '+' '.join(map(str,xs))+' '+str(len(target))+' '+' '.join(map(str,target)))
   st=time.perf_counter();p=subprocess.run([str(H/'artifacts/oracle_pair'),str(inp),str(ap),'1'],capture_output=True,text=True,check=True);native=json.loads(p.stdout);nw=time.perf_counter()-st
   for kind in ['cp','scip']:
    st=time.perf_counter();result=solve(data,sol,prep,kind);wall=time.perf_counter()-st
    row=dict(case=case,q=q,method=kind,columns=len(cols),build=build,solve_wall=wall,total_wall=build+wall,native=native,native_wall=nw,**result);rows.append(row)
    assert result['score']<=native['score']+1e-5*max(1,abs(native['score'])) or native['stopped'],row
    print(case,q,kind,result['score'],native['score'],round(build+wall,4),round(nw,4),flush=True)
   (log/'results.json').write_text(json.dumps(rows,indent=2))
