"""Exact brute-force packing of the15 zones from two incumbents, offline only."""
import json,sys,time
from pathlib import Path
from shapely.geometry import Point,MultiPoint
R=Path(__file__).resolve().parent;ROOT=R.parents[2];sys.path.insert(0,str(ROOT/'task'));from validate_solution import validate
I=json.loads((R/'inputs/anti.json').read_text());P=[Point(z['x'],z['y']) for z in I['sites']]+[Point(z['x'],z['y']) for z in I['offices']];ns=len(I['sites']);assert all(len(set(w))<=1 for w in I['workers']);nsk=1+max(k for w in I['workers'] for k in w);Nk=[sum(k in w for w in I['workers']) for k in range(nsk)];zones=[]
for seed in [1101,1102]:
 for z in json.loads((R/f'logs/screen60/anti_{seed}_v4.solution.json').read_text()):
  o=z['officeId'];sites=z['sites'];h=MultiPoint([P[x] for x in sites]+[P[ns+o]]).convex_hull;cover=sum(1<<x for x,p in enumerate(P) if h.covers(p));need=[int(any(k in I['sites'][x]['tasks'] for x in sites)) for k in range(nsk)]
  zones.append({'seed':seed,'office':o,'sites':sites,'cover':cover,'count':len(sites),'load':sum(len(I['sites'][x]['tasks']) for x in sites),'need':need,'profit':sum(I['sites'][x]['reward']-I['distances'][o][x] for x in sites)-I['offices'][o]['cost']})
n=len(zones);best=(0,[]);nodes=0;feasible=0;start=time.monotonic()
def dfs(k,cover,counts,loads,need,profit,selected):
 global best,nodes,feasible
 nodes+=1
 if k==n:
  feasible+=1;f=profit-(I['balanceCoefficient']*(max(loads)-min(loads)) if loads else 0)
  if f>best[0]:best=(f,selected[:])
  return
 dfs(k+1,cover,counts,loads,need,profit,selected)
 z=zones[k]
 if cover&z['cover']:return
 cs=counts+[z['count']]
 if max(cs)-min(cs)>I['maxDifference']:return
 ne=[x+y for x,y in zip(need,z['need'])]
 if any(x>y for x,y in zip(ne,Nk)):return
 dfs(k+1,cover|z['cover'],cs,loads+[z['load']],ne,profit+z['profit'],selected+[k])
dfs(0,0,[],[],[0]*nsk,0,[])
used=set();sol=[]
for k in best[1]:
 z=zones[k];ws=[]
 for sk in range(nsk):
  if z['need'][sk]:
   w=next(w for w,skills in enumerate(I['workers']) if w not in used and sk in skills);used.add(w);ws.append(w)
 sol.append({'officeId':z['office'],'sites':z['sites'],'workers':ws})
p=R/'logs/zone_pool.solution.json';p.write_text(json.dumps(sol));val=validate(R/'inputs/anti.json',p);assert not isinstance(val,str) and abs(val-best[0])<1e-7
pairs=[(a,b) for a in range(n) for b in range(a+1,n) if zones[a]['seed']!=zones[b]['seed']]
report={'candidate_zones':n,'nodes':nodes,'feasible_packings':feasible,'seconds':time.monotonic()-start,'objective':best[0],'official_objective':val,'selected':[{k:z[k] for k in ['seed','office','count','load','profit']} for i in best[1] for z in [zones[i]]],'cross_basin_pairs':len(pairs),'cross_basin_geometric_conflicts':sum(bool(zones[a]['cover']&zones[b]['cover']) for a,b in pairs),'scope':'Exact only among these15 intact incumbent zones; no reshaping or new sites/offices.'};(R/'ZONE_POOL.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
