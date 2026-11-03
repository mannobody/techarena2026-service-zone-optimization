"""HiGHS version of assigned-pool, fixed-staff selection; warm-start from native DP."""
from pathlib import Path
import time,json
import numpy as np
import highspy
from milp import Instance,value

def improve(I,inc,seconds=58,warm_extra=None,checkpoint_path=None):
 start=time.perf_counter();before=value(I,inc);ops=[r['officeId'] for r in inc];by={r['officeId']:r for r in inc};owner={s:r['officeId'] for r in inc for s in r['sites']};sites=list(owner);idx={s:i for i,s in enumerate(sites)};n=len(sites);K=len(ops);hi=n+K;lo=hi+1;N=lo+1;pool={o:[s for s in sites if owner[s]==o] for o in ops};z={o:n+j for j,o in enumerate(ops)}
 if not K:return dict(solution=inc,value=before,before=before,seconds=0,status='empty')
 T=max(1,max(sum(int(I.tasks[s]) for s in pool[o]) for o in ops));rows=[];lower=[];upper=[]
 def row(terms,lb=-highspy.kHighsInf,ub=highspy.kHighsInf):rows.append(terms);lower.append(lb);upper.append(ub)
 for o in ops:
  cnt=[(idx[s],1.) for s in pool[o]];load=[(idx[s],float(I.tasks[s])) for s in pool[o]]
  row(cnt+[(z[o],-float(I.cap[o]))],ub=0);row(cnt+[(z[o],-1.)],lb=0)
  for p in ops:
   if p!=o:row(cnt+[(idx[s],-1.) for s in pool[p]]+[(z[o],float(I.cap[o])),(z[p],float(I.cap[o]))],ub=float(I.a+2*I.cap[o]))
  row(load+[(hi,-1.)],ub=0);row([(i,-v) for i,v in load]+[(lo,1.),(z[o],float(T))],ub=T)
 row([(lo,1.),(hi,-1.)],ub=0)
 model=highspy.HighsModel();lp=model.lp_;lp.num_col_=N;lp.num_row_=len(rows);lp.col_cost_=[-float(I.profit[owner[s],s]) for s in sites]+[float(I.cost[o]) for o in ops]+[I.alpha,-I.alpha];lp.col_lower_=[0.]*N;lp.col_upper_=[1.]*(n+K)+[float(T)]*2;lp.row_lower_=lower;lp.row_upper_=upper;lp.integrality_=[highspy.HighsVarType.kInteger]*(n+K)+[highspy.HighsVarType.kContinuous]*2
 starts=[0];indices=[];vals=[]
 for r in rows:
  for i,v in r:indices.append(i);vals.append(v)
  starts.append(len(indices))
 lp.a_matrix_.format_=highspy.MatrixFormat.kRowwise;lp.a_matrix_.start_=np.array(starts,dtype=np.int32);lp.a_matrix_.index_=np.array(indices,dtype=np.int32);lp.a_matrix_.value_=np.array(vals,dtype=np.float64)
 h=highspy.Highs();h.setOptionValue('output_flag',False);h.setOptionValue('threads',1);h.setOptionValue('mip_rel_gap',1e-9);assert h.passModel(model)==highspy.HighsStatus.kOk
 warm=warm_extra or inc;selected={s for r in warm for s in r['sites']};opened={r['officeId'] for r in warm};loads=[sum(int(I.tasks[s]) for s in r['sites']) for r in warm];x=[float(s in selected) for s in sites]+[float(o in opened) for o in ops]+[float(max(loads,default=0)),float(min(loads,default=0))];h.setSolution(N,np.arange(N,dtype=np.int32),np.array(x))
 best=warm;bestval=value(I,best)
 def save(vals):
  nonlocal best,bestval
  ans=[]
  for o in ops:
   ss=[s for s in pool[o] if vals[idx[s]]>.5]
   if ss:ans.append(dict(officeId=o,sites=ss,workers=by[o]['workers']))
  score=value(I,ans)
  if isinstance(score,str) or score<bestval-1e-7:return
  best,bestval=ans,score
  if checkpoint_path:
   p=Path(checkpoint_path);tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(dict(solution=best,value=bestval,before=before,seconds=time.perf_counter()-start,status='checkpoint')));tmp.replace(p)
 if checkpoint_path:h.cbMipImprovingSolution.subscribe(lambda e:save(e.data_out.mip_solution))
 prep=time.perf_counter()-start;h.setOptionValue('time_limit',max(.001,seconds-prep));h.run();sol=h.getSolution()
 if sol.value_valid:save(sol.col_value)
 info=h.getInfo();return dict(solution=best,value=bestval,before=before,seconds=time.perf_counter()-start,prep_seconds=prep,status=str(h.getModelStatus()),nodes=info.mip_node_count,bound=-info.mip_dual_bound,gap=info.mip_gap,candidates=n)
