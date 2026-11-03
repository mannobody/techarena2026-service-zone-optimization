"""Dimensionless instance features. No solution, file name, seed or input signature."""
import math,statistics,collections

def features(a):
 S=a['sites'];O=a['offices'];W=a['workers'];D=a['distances'];ns=len(S);no=len(O);nw=len(W)
 avg=lambda v:sum(v)/len(v)if v else 0.
 cv=lambda v:math.sqrt(avg([(x-avg(v))**2 for x in v]))/max(abs(avg(v)),1e-12)if v else 0.
 rewards=[s['reward']for s in S];tasks=[len(s['tasks'])for s in S];nsk=max([k+1 for s in S for k in s['tasks']]+[k+1 for w in W for k in w]+[1]);Nk=[sum(k in w for w in W)for k in range(nsk)]
 serv=[all(Nk[k]>0 for k in s['tasks'])for s in S];cap=[max(0,o['maxSize'])for o in O]
 scale=max(avg([abs(x)for x in rewards]),1e-12)
 f=dict(ns=ns,no=no,nw=nw,nsk=nsk,log_ns=math.log1p(ns),sites_per_office=ns/max(1,no),workers_per_office=nw/max(1,no),workers_per_skill_office=nw/max(1,no*nsk),min_skill_offices=min(Nk,default=0)/max(1,no),multiskill_fraction=avg([len(set(w))>1 for w in W]),unservable_fraction=1-avg(serv)if S else 0,task_mean=avg(tasks),task_cv=cv(tasks),reward_cv=cv(rewards),capacity_ratio=sum(cap)/max(1,ns),capacity_cv=cv(cap),count_slack=a['maxDifference']/max(1,ns/max(1,no)),balance_pressure=a['balanceCoefficient']*max(1,avg(tasks))/scale,cost_ratio=avg([o['cost']for o in O])*no/max(scale*ns,1e-12))
 nearest=[];positive=[];bestprofits=[];gap=[];pos_mass=[]
 xy=[];dist=[];agree=0
 for s,site in enumerate(S):
  p=sorted((site['reward']-D[o][s],o)for o in range(no))
  if not p:continue
  bestprofits.append(max(0,p[-1][0]));positive.append(sum(v>0 for v,_ in p)/no);gap.append((p[-1][0]-p[-2][0])/scale if no>1 else 0)
  nearest.append(p[-1][0]>0 and serv[s]);pos_mass.append(sum(v>0 and cap[o]>0 for v,o in p))
  e=[math.hypot(site['x']-o['x'],site['y']-o['y'])for o in O]
  agree+=int(min(range(no),key=e.__getitem__)==min(range(no),key=lambda o:D[o][s]))
  xy.extend(e);dist.extend(D[o][s]for o in range(no))
 mx=avg(xy);my=avg(dist);xx=sum((x-mx)**2 for x in xy);yy=sum((x-my)**2 for x in dist)
 f.update(geo_distance_corr=sum((x-mx)*(y-my)for x,y in zip(xy,dist))/math.sqrt(xx*yy)if xx*yy>1e-24 else 0.,nearest_agreement=agree/max(1,ns),profitable_fraction=avg(nearest),positive_pair_fraction=avg(positive),positive_offices_per_site=avg(pos_mass),best_profit_ratio=avg(bestprofits)/scale,profit_gap_ratio=avg(gap))
 points=[(s['x'],s['y'])for s in S];mx=avg([x for x,y in points]);my=avg([y for x,y in points]);xx=avg([(x-mx)**2 for x,y in points]);yy=avg([(y-my)**2 for x,y in points]);xy=avg([(x-mx)*(y-my)for x,y in points]);delta=math.sqrt((xx-yy)**2+4*xy*xy)
 f['anisotropy']=(xx+yy-delta)/max(xx+yy+delta,1e-24)
 return f
