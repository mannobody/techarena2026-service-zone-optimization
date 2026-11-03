"""Envelope-choice MILP with grouped integer counts and perspective prefix-profit hypographs."""
from regions import *
import collections,json
import highspy

def improve(I,inc,regions,base,seconds=55,checkpoint=None,fixed_open=False):
 start=time.perf_counter();before=value(I,inc);assert not isinstance(before,str),before
 by={r['officeId']:r for r in inc};have={o:set(k for w in r['workers'] for k in I.workers[w]) for o,r in by.items()};ops=sorted({e['o'] for e in regions});obj=[];lb=[];ub=[];integer=[];warm=[]
 def var(c=0,l=0,u=1,z=False,w=0):
  j=len(obj);obj.append(float(c));lb.append(float(l));ub.append(float(u));integer.append(highspy.HighsVarType.kInteger if z else highspy.HighsVarType.kContinuous);warm.append(float(w));return j
 rows=[];rl=[];ru=[]
 def row(terms,l=-highspy.kHighsInf,u=highspy.kHighsInf):
  d=collections.defaultdict(float)
  for j,a in terms:d[j]+=a
  rows.append([(j,a) for j,a in d.items() if a]);rl.append(float(l));ru.append(float(u))
 z=[var(z=True,w=base.get(e['o'])==i) for i,e in enumerate(regions)];y={o:var(I.cost[o],l=int(fixed_open and o in by),z=True,w=o in by) for o in ops}
 groups={}
 for e,r in enumerate(regions):
  for s in r['sites']:
   if set(I.sites[s]['tasks'])<=have.get(r['o'],set()):groups.setdefault((e,r['o'],int(I.tasks[s]),()),[]).append(s)
 q={};qoffice=collections.defaultdict(list)
 for k,ss in groups.items():
  e,o,t,skills=k;ss.sort(key=lambda s:(-float(I.profit[o,s]),s));n=sum(s in by.get(o,{}).get('sites',[]) for s in ss) if base.get(o)==e else 0
  q[k]=var(u=len(ss),z=True,w=n);qoffice[o].append(k);row([(q[k],1),(z[e],-len(ss))],u=0)
  v=var(c=-1,l=-highspy.kHighsInf,u=highspy.kHighsInf,w=sum(float(I.profit[o,s]) for s in ss[:n]))
  prefix=0.
  for j,s in enumerate(ss):
   p=float(I.profit[o,s])
   if j==0 or p!=float(I.profit[o,ss[j-1]]):row([(v,1),(q[k],-p),(z[e],-(prefix-j*p))],u=0)
   prefix+=p
  # Perspective hypograph: exact top-q for z=1 and the convex hull for fractional z.
 profiles={}
 u={}
 oldloads=[sum(int(I.tasks[s]) for s in r['sites']) for r in inc];oldcounts=[len(r['sites']) for r in inc]
 T=max([1]+[sum(int(I.tasks[s]) for s in e['sites']) for e in regions]);hi=var(I.alpha,u=T,w=max(oldloads,default=0));lo=var(-I.alpha,u=T,w=min(oldloads,default=0));ch=var(u=I.n,w=max(oldcounts,default=0));cl=var(u=I.n,w=min(oldcounts,default=0))
 for o in ops:
  row([(z[e],1) for e,r in enumerate(regions) if r['o']==o]+[(y[o],-1)],0,0)
  cnt=[(q[k],1) for k in qoffice[o]];load=[(q[k],k[2]) for k in qoffice[o]]
  row(cnt+[(y[o],-I.cap[o])],u=0);row(cnt+[(y[o],-1)],l=0)
  row(cnt+[(ch,-1)],u=0);row([(j,-a) for j,a in cnt]+[(cl,1),(y[o],I.n)],u=I.n)
  row(load+[(hi,-1)],u=0);row([(j,-a) for j,a in load]+[(lo,1),(y[o],T)],u=T)
 row([(lo,1),(hi,-1)],u=0);row([(cl,1),(ch,-1)],u=0);row([(ch,1),(cl,-1)],u=I.a)
 cover=collections.defaultdict(list)
 for e,r in enumerate(regions):
  for p in r['footprint']:cover[p].append(e)
 conflicts=set(tuple(es) for es in cover.values() if len(es)>1 and len({regions[e]['o'] for e in es})>1)
 for es in conflicts:row([(z[e],1) for e in es],u=1)
 m=highspy.HighsModel();lp=m.lp_;lp.num_col_=len(obj);lp.num_row_=len(rows);lp.col_cost_=obj;lp.col_lower_=lb;lp.col_upper_=ub;lp.integrality_=integer;lp.row_lower_=rl;lp.row_upper_=ru
 starts=[0];inds=[];vals=[]
 for r in rows:
  for j,a in r:inds.append(j);vals.append(a)
  starts.append(len(inds))
 lp.a_matrix_.format_=highspy.MatrixFormat.kRowwise;lp.a_matrix_.start_=np.asarray(starts,np.int32);lp.a_matrix_.index_=np.asarray(inds,np.int32);lp.a_matrix_.value_=np.asarray(vals,float)
 h=highspy.Highs();h.setOptionValue('output_flag',False);h.setOptionValue('threads',1);h.setOptionValue('random_seed',1);h.setOptionValue('mip_rel_gap',1e-8);assert h.passModel(m)==highspy.HighsStatus.kOk
 h.setSolution(len(warm),np.arange(len(warm),dtype=np.int32),np.asarray(warm,float));best=inc;bestval=before;invalid=[];timeline=[];selected=[]
 def save(v):
  nonlocal best,bestval,selected
  chosen={o:[] for o in ops};staff={o:list(by.get(o,{}).get('workers',[])) for o in ops}
  for k,ss in groups.items():
   n=round(v[q[k]])
   if abs(v[q[k]]-n)>1e-4 or n<0 or n>len(ss):return
   chosen[k[1]].extend(ss[:n])
  for p,ws in profiles.items():
   need=[o for o in ops if v[u[o,p]]>.5]
   if len(need)>len(ws):return
   for o,w in zip(need,ws):staff[o].append(w)
  ans=[dict(officeId=o,sites=sorted(chosen[o]),workers=staff[o]) for o in ops if chosen[o]];score=value(I,ans)
  if isinstance(score,str):invalid.append(score);return
  if score>bestval+1e-8:
   best,bestval=ans,score;selected=[dict(index=e,o=r['o'],tag=r['tag']) for e,r in enumerate(regions) if v[z[e]]>.5];timeline.append(dict(seconds=time.perf_counter()-start,value=score))
   if checkpoint:
    p=Path(checkpoint);tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(dict(solution=best,value=bestval,before=before,selected=selected,timeline=timeline,status='checkpoint')));tmp.replace(p)
 h.cbMipImprovingSolution.subscribe(lambda e:save(e.data_out.mip_solution));prep=time.perf_counter()-start
 h.setOptionValue('time_limit',max(.001,seconds-prep));h.run();sol=h.getSolution()
 if sol.value_valid:save(sol.col_value)
 info=h.getInfo()
 return dict(solution=best,value=bestval,before=before,status=str(h.getModelStatus()),seconds=time.perf_counter()-start,prep_seconds=prep,groups=len(groups),regions=len(regions),variables=len(obj),rows=len(rows),packing_rows=len(conflicts),nodes=info.mip_node_count,bound=-info.mip_dual_bound,gap=info.mip_gap,invalid=invalid,timeline=timeline,selected=selected)
