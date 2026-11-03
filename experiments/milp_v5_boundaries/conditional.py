"""Exact aggregated conditional MILP: counts by (office, task count, skill set).
For a fixed safe territory, selecting k identical-resource sites means top k profit.
Research only. All outputs independently checked by the official validator.
"""
from pathlib import Path
import sys,time,json,collections
import numpy as np
import highspy
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H.parent/'dp_milp'))
from milp import Instance,value

def territory(I,inc):
 return {r['officeId']:[s for s in I.column(r['officeId'],r['sites']).footprint if s<I.n and I.servable[s]] for r in inc}

def improve(I,inc,seconds=58,mode='assigned',checkpoint=None,pools=None,fixed_open=False):
 start=time.perf_counter();before=value(I,inc);assert not isinstance(before,str),before
 by={r['officeId']:r for r in inc};joint=mode=='joint';pools=pools if pools is not None else ({o:list(r['sites']) for o,r in by.items()} if mode=='assigned' else territory(I,inc))
 if not joint:
  have={o:set(k for w in by.get(o,{}).get('workers',[]) for k in I.workers[w]) for o in pools}
  pools={o:[s for s in ss if set(I.sites[s]['tasks'])<=have[o]] for o,ss in pools.items()}
 pools={o:ss for o,ss in pools.items() if ss and I.cap[o]>0};ops=sorted(pools)
 if not ops:return dict(solution=inc,value=before,before=before,status='empty',seconds=time.perf_counter()-start,groups=0)
 groups={}
 for o in ops:
  for s in pools[o]:
   if I.servable[s]:groups.setdefault((o,int(I.tasks[s]),tuple(sorted(set(I.sites[s]['tasks']))) if joint else ()),[]).append(s)
 keys=list(groups)
 for key in keys:groups[key].sort(key=lambda s:(-I.profit[key[0],s],s))
 N=0;obj=[];lower=[];upper=[];integ=[]
 def var(cost=0,lb=0,ub=1,integer=False):
  nonlocal N
  j=N;N+=1;obj.append(float(cost));lower.append(float(lb));upper.append(float(ub));integ.append(highspy.HighsVarType.kInteger if integer else highspy.HighsVarType.kContinuous);return j
 q={k:var(ub=len(groups[k]),integer=True) for k in keys};v={k:var(cost=-1,lb=-highspy.kHighsInf,ub=highspy.kHighsInf) for k in keys};y={o:var(cost=I.cost[o],lb=int(fixed_open and o in by),integer=True) for o in ops}
 T=max(1,max(sum(int(I.tasks[s]) for s in pools[o]) for o in ops));hi=var(cost=I.alpha,ub=T);lo=var(cost=-I.alpha,ub=T)
 profiles=collections.defaultdict(list)
 for w,ss in enumerate(I.workers):profiles[tuple(sorted(set(ss)))].append(w)
 u={(o,p):var(integer=True) for o in ops for p in profiles if p} if joint else {}
 rows=[];rl=[];ru=[]
 def row(terms,lb=-highspy.kHighsInf,ub=highspy.kHighsInf):
  d=collections.defaultdict(float)
  for j,a in terms:d[j]+=a
  rows.append([(j,a) for j,a in d.items() if a]);rl.append(float(lb));ru.append(float(ub))
 for k in keys:
  xs=[var(cost=-float(I.profit[k[0],s])) for s in groups[k]]
  obj[v[k]]=0;lower[v[k]]=upper[v[k]]=0
  row([(j,1) for j in xs]+[(q[k],-1)],lb=0,ub=0)
  if joint:
   for skill in k[2]:row([(q[k],1)]+[(u[k[0],p],-len(groups[k])) for p in profiles if skill in p],ub=0)
 for o in ops:
  cnt=[(q[k],1) for k in keys if k[0]==o];load=[(q[k],k[1]) for k in keys if k[0]==o]
  row(cnt+[(y[o],-I.cap[o])],ub=0);row(cnt+[(y[o],-1)],lb=0)
  for p in ops:
   if p!=o:row(cnt+[(q[k],-1) for k in keys if k[0]==p]+[(y[o],I.cap[o]),(y[p],I.cap[o])],ub=I.a+2*I.cap[o])
  row(load+[(hi,-1)],ub=0);row([(j,-a) for j,a in load]+[(lo,1),(y[o],T)],ub=T)
 row([(lo,1),(hi,-1)],ub=0)
 if joint:
  for p,ws in profiles.items():
   if p:row([(u[o,p],1) for o in ops],ub=len(ws))
  for (o,p),j in u.items():row([(j,1),(y[o],-1)],ub=0)
 model=highspy.HighsModel();lp=model.lp_;lp.num_col_=N;lp.num_row_=len(rows);lp.col_cost_=obj;lp.col_lower_=lower;lp.col_upper_=upper;lp.integrality_=integ;lp.row_lower_=rl;lp.row_upper_=ru
 starts=[0];idx=[];vals=[]
 for r in rows:
  for j,a in r:idx.append(j);vals.append(a)
  starts.append(len(idx))
 lp.a_matrix_.format_=highspy.MatrixFormat.kRowwise;lp.a_matrix_.start_=np.array(starts,np.int32);lp.a_matrix_.index_=np.array(idx,np.int32);lp.a_matrix_.value_=np.array(vals,float)
 h=highspy.Highs();h.setOptionValue('output_flag',False);h.setOptionValue('threads',1);h.setOptionValue('mip_rel_gap',1e-8);h.setOptionValue('random_seed',1);assert h.passModel(model)==highspy.HighsStatus.kOk
 old={(r['officeId'],s) for r in inc for s in r['sites']};warm=np.zeros(N)
 for k in keys:
  count=sum((k[0],s) in old for s in groups[k]);warm[q[k]]=count;warm[v[k]]=0
 for o in ops:warm[y[o]]=int(o in by)
 loads=[sum(int(I.tasks[s]) for s in r['sites']) for r in inc];warm[hi]=max(loads,default=0);warm[lo]=min(loads,default=0)
 for (o,p),j in u.items():warm[j]=int(any(w in by.get(o,{}).get('workers',[]) for w in profiles[p]))
 known=np.array(list(q.values())+list(y.values())+list(u.values())+[hi,lo],dtype=np.int32);h.setSolution(len(known),known,warm[known])
 best=inc;bestval=before;invalid=[]
 def save(vals):
  nonlocal best,bestval
  chosen={o:[] for o in ops}
  for k in keys:
   x=float(vals[q[k]])
   if abs(x-round(x))>1e-4:return
   chosen[k[0]].extend(groups[k][:max(0,min(len(groups[k]),round(x)))])
  staff={o:list(by.get(o,{}).get('workers',[])) for o in ops}
  if joint:
   staff={o:[] for o in ops}
   for p,ws in profiles.items():
    need=[o for o in ops if (o,p) in u and vals[u[o,p]]>.5]
    if len(need)>len(ws):return
    for o,w in zip(need,ws):staff[o].append(w)
  ans=[dict(officeId=o,sites=sorted(chosen[o]),workers=staff[o]) for o in ops if chosen[o]];score=value(I,ans)
  if isinstance(score,str):invalid.append(score);return
  if score>bestval+1e-8:
   best,bestval=ans,score
   if checkpoint:
    p=Path(checkpoint);tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(dict(solution=best,value=bestval,before=before,status='checkpoint',seconds=time.perf_counter()-start,groups=len(keys),candidates=sum(map(len,pools.values())))));tmp.replace(p)
 h.cbMipImprovingSolution.subscribe(lambda e:save(e.data_out.mip_solution))
 prep=time.perf_counter()-start;h.setOptionValue('time_limit',max(.001,seconds-prep));h.run();sol=h.getSolution()
 if sol.value_valid:save(sol.col_value)
 info=h.getInfo();return dict(solution=best,value=bestval,before=before,seconds=time.perf_counter()-start,prep_seconds=prep,status=str(h.getModelStatus()),groups=len(keys),candidates=sum(map(len,pools.values())),variables=N,rows=len(rows),nodes=info.mip_node_count,bound=-info.mip_dual_bound,gap=info.mip_gap,invalid=invalid,mode=mode)
