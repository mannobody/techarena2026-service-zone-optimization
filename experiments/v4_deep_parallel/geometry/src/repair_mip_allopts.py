"""Restricted reassignment MIP with exact conditional geometry via monotone cuts.
Research only: SCIP and HiGHS solve the SAME rows; no fixed safe envelopes.
Geometry is checked on every input point using the official validator's Shapely
semantics. A rejected integer solution yields a supporting-set conflict cut.
"""
import json,time,sys,itertools,collections,math
from pathlib import Path
import numpy as np
import shapely
from shapely import MultiPoint,Point
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT/'task'))
from validate_solution import Instance,OpenedOffice,validate_solution

def score(data,sol):return validate_solution(Instance.model_validate(data),[OpenedOffice.model_validate(x) for x in sol])

def choose_sites(data,inc,budget):
 n=len(data['sites']);m=len(data['offices']);by={r['officeId']:r for r in inc};assigned={s:r['officeId'] for r in inc for s in r['sites']}
 if budget>=n:return list(range(n))
 def p(o,s):return data['sites'][s]['reward']-data['distances'][o][s]
 queues=[]
 for o,r in by.items():
  v=r['sites'];profit=sorted(v,key=lambda s:(-max([p(q,s)-p(o,s) for q in range(m) if q!=o]+[0]),s))
  load=sorted(v,key=lambda s:(len(data['sites'][s]['tasks']),s));q=[]
  for a,b,c in itertools.zip_longest(profit,load,reversed(load)):
   for s in (a,b,c):
    if s is not None and s not in q:q.append(s)
  queues.append(q)
 selected=[];assigned_budget=budget*2//3
 for i in range(max([len(q) for q in queues]+[0])):
  for q in queues:
   if i<len(q) and len(selected)<assigned_budget:selected.append(q[i])
 free=[s for s in range(n) if s not in assigned]
 free.sort(key=lambda s:(-max([p(o,s) for o in range(m)]+[0]),s))
 selected+=free[:budget-len(selected)]
 if len(selected)<budget:
  selected+= [s for s in assigned if s not in selected][:budget-len(selected)]
 return sorted(selected)


def choose_peel(data,inc,budget,pair_index=0):
 # Free successive hull layers of an adjacent pair, then nearby free sites.
 n=len(data['sites']);m=len(data['offices']);by={r['officeId']:r for r in inc};ops=sorted(by)
 if len(ops)<2:return choose_sites(data,inc,budget)
 xy=[(s['x'],s['y']) for s in data['sites']]+[(o['x'],o['y']) for o in data['offices']]
 hull={o:MultiPoint([xy[n+o]]+[xy[s] for s in by[o]['sites']]).convex_hull for o in ops}
 pairs=sorted(itertools.combinations(ops,2),key=lambda ab:(hull[ab[0]].distance(hull[ab[1]]),ab))
 pair=pairs[pair_index%len(pairs)];remaining={o:list(by[o]['sites']) for o in pair};selected=[];limit=budget*2//3
 while len(selected)<limit and any(remaining.values()):
  changed=False
  for o in pair:
   if not remaining[o] or len(selected)>=limit:continue
   h=MultiPoint([xy[n+o]]+[xy[s] for s in remaining[o]]).convex_hull
   vertices=set(h.exterior.coords if h.geom_type=='Polygon' else h.coords)
   layer=[s for s in remaining[o] if xy[s] in vertices]
   layer.sort(key=lambda s:(min(math.dist(xy[s],xy[t]) for t in by[pair[1] if o==pair[0] else pair[0]]['sites']),s))
   for x in layer:
    if len(selected)>=limit:break
    selected.append(x);remaining[o].remove(x);changed=True
  if not changed:break
 old={s for r in inc for s in r['sites']};free=[s for s in range(n) if s not in old]
 free.sort(key=lambda s:(min(hull[o].distance(Point(xy[s])) for o in pair),-max(data['sites'][s]['reward']-data['distances'][o][s] for o in pair),s))
 selected+=free[:budget-len(selected)]
 if len(selected)<budget:selected+=[s for o in pair for s in remaining[o]][:budget-len(selected)]
 return sorted(selected)

class Linear:
 def __init__(self):self.cost=[];self.lb=[];self.ub=[];self.integer=[];self.warm=[];self.rows=[]
 def var(self,c=0,lb=0,ub=1,integer=True,w=0):
  j=len(self.cost);self.cost.append(float(c));self.lb.append(float(lb));self.ub.append(float(ub));self.integer.append(integer);self.warm.append(float(w));return j
 def row(self,terms,lb=-math.inf,ub=math.inf):
  d=collections.defaultdict(float)
  for j,a in terms:d[j]+=a
  self.rows.append((dict((j,a) for j,a in d.items() if a),float(lb),float(ub)))

class Backend:
 def __init__(self,L,name):
  self.L=L;self.name=name
  if name=='highs':
   import highspy
   self.api=highspy;h=highspy.Highs();h.setOptionValue('output_flag',False);h.setOptionValue('threads',1);h.setOptionValue('mip_rel_gap',1e-9);h.setOptionValue('random_seed',1)
   model=highspy.HighsModel();p=model.lp_;p.num_col_=len(L.cost);p.num_row_=len(L.rows);p.col_cost_=L.cost;p.col_lower_=L.lb;p.col_upper_=L.ub;p.integrality_=[highspy.HighsVarType.kInteger if b else highspy.HighsVarType.kContinuous for b in L.integer]
   p.row_lower_=[r[1] for r in L.rows];p.row_upper_=[r[2] for r in L.rows];starts=[0];indices=[];values=[]
   for d,l,u in L.rows:indices.extend(d);values.extend(d.values());starts.append(len(indices))
   p.a_matrix_.format_=highspy.MatrixFormat.kRowwise;p.a_matrix_.start_=np.asarray(starts,np.int32);p.a_matrix_.index_=np.asarray(indices,np.int32);p.a_matrix_.value_=np.asarray(values,float)
   assert h.passModel(model)==highspy.HighsStatus.kOk;self.solver=h
  else:
   from pyscipopt import Model,quicksum
   self.sum=quicksum;m=Model();m.hideOutput();m.setIntParam('parallel/maxnthreads',1);m.setIntParam('randomization/randomseedshift',1);m.setRealParam('limits/gap',1e-9)
   self.vars=[m.addVar(vtype='I' if z else 'C',lb=l,ub=u,obj=c) for c,l,u,z in zip(L.cost,L.lb,L.ub,L.integer)];m.setMinimize();self.solver=m
   for row in L.rows:self._sciprow(row)
  self.warm(L.warm)
 def _sciprow(self,row):
  d,l,u=row;e=self.sum(a*self.vars[j] for j,a in d.items())
  if math.isfinite(l):self.solver.addCons(e>=l)
  if math.isfinite(u):self.solver.addCons(e<=u)
 def warm(self,values):
  if self.name=='highs':self.solver.setSolution(len(values),np.arange(len(values),dtype=np.int32),np.asarray(values,float))
  else:
   m=self.solver;m.freeTransform();s=m.createSol()
   for v,x in zip(self.vars,values):m.setSolVal(s,v,x)
   m.addSol(s)
 def cut(self,indices):
  if self.name=='highs':self.solver.addRow(-self.api.kHighsInf,len(indices)-1,len(indices),np.asarray(indices,np.int32),np.ones(len(indices)))
  else:self.solver.freeTransform();self._sciprow(({j:1 for j in indices},-math.inf,len(indices)-1))
 def solve(self,seconds):
  if self.name=='highs':
   h=self.solver;h.setOptionValue('time_limit',max(.001,seconds));h.run();v=h.getSolution();info=h.getInfo();status=str(h.getModelStatus());valid=v.value_valid and info.primal_solution_status==2
   return (list(v.col_value) if valid else None,status,-info.mip_dual_bound,int(info.mip_node_count),status=='HighsModelStatus.kOptimal')
  m=self.solver;m.setRealParam('limits/time',m.getSolvingTime()+max(.001,seconds));m.optimize();s=m.getBestSol();status=str(m.getStatus())
  return ([m.getSolVal(s,v) for v in self.vars] if s else None,status,-m.getDualbound(),m.getNNodes(),status=='optimal')

def improve(data,inc,seconds=10,budget=24,backend='highs',joint=True,selected=None):
 t0=time.perf_counter();before=score(data,inc);assert not isinstance(before,str),before
 n=len(data['sites']);m=len(data['offices']);selected=choose_sites(data,inc,budget) if selected is None else sorted(selected);chosen=set(selected)
 old={s:r['officeId'] for r in inc for s in r['sites']};by={r['officeId']:r for r in inc};fixed={o:[s for s,q in old.items() if q==o and s not in chosen] for o in range(m)}
 coords=[(s['x'],s['y']) for s in data['sites']]+[(o['x'],o['y']) for o in data['offices']];points=shapely.points(coords);tasks=[len(s['tasks']) for s in data['sites']];alpha=data['balanceCoefficient'];A=data['maxDifference'];T=max(1,sum(tasks));L=Linear()
 profiles=collections.defaultdict(list)
 for w,skills in enumerate(data['workers']):profiles[tuple(sorted(set(skills)))].append(w)
 have={o:{k for w in by.get(o,{}).get('workers',[]) for k in data['workers'][w]} for o in range(m)}
 y={o:L.var(c=data['offices'][o]['cost'],lb=bool(fixed[o]),ub=1 if joint or o in by else 0,w=o in by) for o in range(m)}
 x={};p=lambda o,s:data['sites'][s]['reward']-data['distances'][o][s]
 for s in selected:
  opts=list(range(m))
  if s in old and old[s] not in opts:opts.append(old[s])
  if m:
   near=min(range(m),key=lambda o:math.dist(coords[s],coords[n+o]))
   if near not in opts:opts.append(near)
  for o in opts:
   if not joint and (o not in by or not set(data['sites'][s]['tasks'])<=have[o]):continue
   x[s,o]=L.var(c=-p(o,s),w=old.get(s)==o)
  L.row([(j,1) for (ss,o),j in x.items() if ss==s],ub=1)
 u={(o,pr):L.var(w=any(w in by.get(o,{}).get('workers',[]) for w in ws)) for o in range(m) for pr,ws in profiles.items() if pr} if joint else {}
 if joint:
  for pr,ws in profiles.items():
   if pr:L.row([(u[o,pr],1) for o in range(m)],ub=len(ws))
  for (o,pr),j in u.items():L.row([(j,1),(y[o],-1)],ub=0)
  for o in range(m):
   required={k for s in fixed[o] for k in data['sites'][s]['tasks']}
   for k in required:L.row([(u[o,pr],1) for pr in profiles if k in pr],lb=1)
   for (s,q),j in x.items():
    if q==o:
     for k in set(data['sites'][s]['tasks']):L.row([(j,1)]+[(u[o,pr],-1) for pr in profiles if k in pr],ub=0)
 oldloads=[sum(tasks[s] for s in r['sites']) for r in inc];oldcounts=[len(r['sites']) for r in inc]
 hi=L.var(c=alpha,ub=T,integer=False,w=max(oldloads,default=0));lo=L.var(c=-alpha,ub=T,integer=False,w=min(oldloads,default=0));ch=L.var(ub=n,integer=False,w=max(oldcounts,default=0));cl=L.var(ub=n,integer=False,w=min(oldcounts,default=0))
 for o in range(m):
  sz=len(fixed[o]);ld=sum(tasks[s] for s in fixed[o]);cnt=[(j,1) for (s,q),j in x.items() if q==o];load=[(j,tasks[s]) for (s,q),j in x.items() if q==o]
  L.row(cnt+[(y[o],-data['offices'][o]['maxSize'])],ub=-sz);L.row(cnt+[(y[o],-1)],lb=-sz)
  L.row(cnt+[(ch,-1)],ub=-sz);L.row([(j,-a) for j,a in cnt]+[(cl,1),(y[o],n)],ub=n+sz)
  L.row(load+[(hi,-1)],ub=-ld);L.row([(j,-a) for j,a in load]+[(lo,1),(y[o],T)],ub=T+ld)
 L.row([(lo,1),(hi,-1)],ub=0);L.row([(cl,1),(ch,-1)],ub=0);L.row([(ch,1),(cl,-1)],ub=A)
 constant=sum(p(o,s) for o,ss in fixed.items() for s in ss);B=Backend(L,backend);prep=time.perf_counter()-t0
 best=inc;bestvalue=before;cuts=set();iterations=0;status='unrun';bound=math.inf;optimal=False;events=[];nodes=0;support_sizes=[]
 while time.perf_counter()-t0<seconds:
  vals,status,ub,nn,opt=B.solve(seconds-(time.perf_counter()-t0));iterations+=1;nodes+=nn;bound=ub+constant
  if vals is None:break
  if any(abs(vals[j]-round(vals[j]))>1e-5 for j,z in enumerate(L.integer) if z):status='fractional_incumbent';break
  mem={o:fixed[o]+[s for (s,q),j in x.items() if q==o and vals[j]>.5] for o in range(m)};active=[o for o in range(m) if mem[o]]
  covered={o:np.flatnonzero(shapely.covers(MultiPoint([coords[n+o]]+[coords[s] for s in mem[o]]).convex_hull,points)) for o in active};owner={};conflicts=[]
  for o in active:
   for q in covered[o]:
    if int(q) in owner:conflicts.append((owner[int(q)],o,int(q)))
    else:owner[int(q)]=o
  if conflicts:
   added=0
   for a,b,q in conflicts[:16]:
    support=[]
    for o in [a,b]:
     variable=[s for s in mem[o] if s in chosen];core=[coords[n+o]]+[coords[s] for s in fixed[o]]
     for s in list(variable):
      trial=[z for z in variable if z!=s]
      if MultiPoint(core+[coords[z] for z in trial]).convex_hull.covers(Point(coords[q])):variable=trial
     support.extend(x[s,o] for s in variable)
     if not fixed[o]:support.append(y[o])
    key=tuple(sorted(set(support)));assert key,'fixed incumbent geometry conflict'
    if key not in cuts:cuts.add(key);B.cut(key);added+=1;support_sizes.append(len(key))
    if time.perf_counter()-t0>=seconds:break
   events.append({'iteration':iterations,'conflicts':len(conflicts),'added':added,'bound':bound,'seconds':time.perf_counter()-t0})
   if not added:status='duplicate_cut_stall';break
   B.warm(L.warm);continue
  staff={o:list(by.get(o,{}).get('workers',[])) for o in active}
  if joint:
   staff={o:[] for o in active}
   for pr,ws in profiles.items():
    if not pr:continue
    need=[o for o in active if vals[u[o,pr]]>.5]
    for o,w in zip(need,ws):staff[o].append(w)
  sol=[dict(officeId=o,sites=sorted(mem[o]),workers=staff[o]) for o in active];v=score(data,sol)
  if isinstance(v,str):status='invalid:'+v;break
  if v>=bestvalue-1e-7:best=sol;bestvalue=v
  optimal=opt;break
 return {'solution':best,'value':bestvalue,'before':before,'gain':bestvalue-before,'conditional_optimal':optimal,'bound':bound,'status':status,'seconds':time.perf_counter()-t0,'prep':prep,'iterations':iterations,'nodes':nodes,'cuts':len(cuts),'max_cut_support':max(support_sizes,default=0),'variables':len(L.cost),'rows':len(L.rows),'selected':selected,'backend':backend,'joint':joint,'events':events}

if __name__=='__main__':
 import argparse
 a=argparse.ArgumentParser();a.add_argument('instance');a.add_argument('incumbent');a.add_argument('output');a.add_argument('--seconds',type=float,default=10);a.add_argument('--budget',type=int,default=24);a.add_argument('--backend',choices=['scip','highs'],default='highs');a.add_argument('--fixed-workers',action='store_true');a.add_argument('--selection',choices=['profit','peel'],default='profit');a.add_argument('--pair-index',type=int,default=0);q=a.parse_args()
 data=json.loads(Path(q.instance).read_text());inc=json.loads(Path(q.incumbent).read_text());selected=choose_peel(data,inc,q.budget,q.pair_index) if q.selection=='peel' else None
 result=improve(data,inc,q.seconds,q.budget,q.backend,not q.fixed_workers,selected);result['selection']=q.selection;result['pair_index']=q.pair_index;Path(q.output).write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k not in ('solution','events','selected')}))
