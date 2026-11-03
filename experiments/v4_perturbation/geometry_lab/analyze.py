import json,re,statistics,sys,os,hashlib
from pathlib import Path
from shapely.geometry import MultiPoint
R=Path(__file__).resolve().parent;ROOT=R.parents[2]
os.sched_setaffinity(0,{12,13})
def info(inp,sol):
 a=[-1]*len(inp['sites']);w=[-1]*len(inp['workers']);h={};counts={};loads={};reward=distance=cost=0
 for row in sol:
  o=row['officeId'];sites=row['sites'];counts[o]=len(sites);loads[o]=sum(len(inp['sites'][x]['tasks']) for x in sites)
  p=inp['offices'][o];coords=[(p['x'],p['y'])]
  for x in sites:
   a[x]=o;p=inp['sites'][x];reward+=p['reward'];distance+=inp['distances'][o][x];coords.append((p['x'],p['y']))
  hull=MultiPoint(coords).convex_hull
  h[o]=sorted(hull.exterior.coords if hull.geom_type=='Polygon' else hull.coords)
  for x in row['workers']:w[x]=o
  cost+=inp['offices'][o]['cost']
 penalty=inp['balanceCoefficient']*(max(loads.values())-min(loads.values())) if loads else 0
 return {'asg':a,'workers':w,'hulls':h,'counts':counts,'loads':loads,'objective':reward-distance-cost-penalty,'reward':reward,'distance':distance,'cost':cost,'imbalance_penalty':penalty}
def stats(v):
 return {'n':len(v),'mean':statistics.mean(v) if v else None,'median':statistics.median(v) if v else None,'min':min(v) if v else None,'max':max(v) if v else None,'stddev':statistics.pstdev(v) if v else None}
for series in sys.argv[1:]:
 dest=R/'logs'/series;manifest=json.loads((dest/'MANIFEST.json').read_text());spec=manifest['spec'];rows=json.loads((dest/'results.json').read_text());initial={};out=[]
 for c,p in spec['cases'].items():
  inp=json.loads((ROOT/p).read_text());s=json.loads((ROOT/spec['checkpoints'][c]).read_text());initial[c]=(inp,info(inp,s))
 for r in rows:
  inp,base=initial[r['case']];prefix=dest/f"{r['case']}_{r['seed']}_{r['variant']}";sol=info(inp,json.loads(prefix.with_suffix('.solution.json').read_text()));text=prefix.with_suffix('.stderr').read_text()
  diagnostics=[]
  for match in re.finditer(r'geometry tid=.*?first_improvement=[-0-9.]+',text):
   diagnostics.append({k:float(v) for k,v in re.findall(r'(\w+)=([-0-9.]+)',match[0])})
  out.append(r|{'checkpoint_objective':base['objective'],'gain':sol['objective']-base['objective'],'gain_pct':100*(sol['objective']-base['objective'])/max(1,abs(base['objective'])),
  'gain_per_wall_second':(sol['objective']-base['objective'])/r['wall'],'assignment_changes':sum(a!=b for a,b in zip(base['asg'],sol['asg'])),'worker_changes':sum(a!=b for a,b in zip(base['workers'],sol['workers'])),'office_changes':len(set(base['counts'])^set(sol['counts'])),
  'hull_changes':sum(base['hulls'].get(o)!=sol['hulls'].get(o) for o in set(base['hulls'])|set(sol['hulls'])),
  'decomposition':{k:sol[k] for k in ['objective','reward','distance','cost','imbalance_penalty','counts','loads']},'decomposition_delta':{k:sol[k]-base[k] for k in ['reward','distance','cost','imbalance_penalty']},'endpoint_diagnostics':diagnostics})
 control='lns' if 'lns' in spec['variants'] else 'boundary';paired={};by={(r['case'],r['seed'],r['variant']):r for r in out}
 for var in spec['variants']:
  if var==control:continue
  vals=[]
  for r in out:
   if r['variant']!=var:continue
   b=by.get((r['case'],r['seed'],control))
   if b and b['success'] and r['success']:vals.append(100*(r['objective']-b['objective'])/max(1,abs(b['objective'])))
  paired[var]=stats(vals)|{'wins':sum(v>1e-7 for v in vals),'ties':sum(abs(v)<=1e-7 for v in vals),'losses':sum(v< -1e-7 for v in vals)}
 aggregated={}
 for var in spec['variants']:
  rr=[r for r in out if r['variant']==var];dd=[d for r in rr for d in r['endpoint_diagnostics']]
  aggregated[var]={'success':sum(r['success'] for r in rr),'runs':len(rr),'gains_pct':stats([r['gain_pct'] for r in rr]),'positive_final_runs':sum(r['gain']>1e-7 for r in rr),'wall':stats([r['wall'] for r in rr]),'diagnostics_sums':{k:sum(d.get(k,0) for d in dd)for k in ['attempts','accepted','hull_changed','freed_points','workers_changed','recoveries','improved','returned_same','unrecovered','perturb_seconds','recovery_seconds','loss_sum','gain_sum']}}
 summary={'series':series,'complete':(dest/'COMPLETE.json').exists(),'rows':out,'control':control,'paired_against_control':paired,'aggregated':aggregated,
 'diagnostics_caveat':'per-thread improvement, recovery and same-state counts use recovery endpoints; native LNS may publish a better intermediate solution. Final validated objective is global best encountered. Recovery_seconds is endpoint observation latency, not exact first passage time.'}
 (R/(series.upper()+'_SUMMARY.json')).write_text(json.dumps(summary,indent=2));print(series,json.dumps(paired,indent=2));print('aggregated',json.dumps(aggregated,indent=2))
