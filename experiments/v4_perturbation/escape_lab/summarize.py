import pathlib,json,re,statistics,sys,itertools
root=pathlib.Path(__file__).resolve().parents[3];lab=pathlib.Path(__file__).resolve().parent
dest=pathlib.Path(sys.argv[1]);dest=root/dest if not dest.is_absolute() else dest
spec=json.loads((dest/'MANIFEST.json').read_text())['spec'];rows=json.loads((dest/'results.json').read_text())
expected=set(itertools.product(spec['cases'],spec['seeds'],spec['variants']));keys=[(r['case'],r['seed'],r['variant']) for r in rows]
assert len(set(keys))==len(keys) and set(keys)==expected
lookup={k:r for k,r in zip(keys,rows)};out={'runs':len(rows),'success':sum(r['success'] for r in rows),'seconds':spec['seconds'],'variants':{},'trace':{}}
for variant in spec['variants']:
 pairs=[];trace=[]
 for case,seed in itertools.product(spec['cases'],spec['seeds']):
  b=lookup[case,seed,'v4'];r=lookup[case,seed,variant];assert b['affinity']==r['affinity']==[14,15]
  if b['success'] and r['success']:
   delta=r['objective']-b['objective'];pct=delta/max(1e-12,abs(b['objective']))*100
   pairs.append({'case':case,'seed':seed,'baseline':b['objective'],'objective':r['objective'],'delta':delta,'pct':pct})
  log=(dest/f'{case}_{seed}_{variant}.stderr').read_text()
  for line in log.splitlines():
   if line.startswith('ESCAPE '):
    rec={k:float(v) for k,v in re.findall(r'(\w+)=([-+\d.eE]+)',line)};rec.update(case=case,seed=seed);trace.append(rec)
 vals=[p['pct'] for p in pairs];wtl=[sum(p['delta']>1e-9*max(1,abs(p['baseline'])) for p in pairs),sum(abs(p['delta'])<=1e-9*max(1,abs(p['baseline'])) for p in pairs),sum(p['delta']< -1e-9*max(1,abs(p['baseline'])) for p in pairs)]
 out['variants'][variant]={'pairs':pairs,'mean_pct':statistics.mean(vals) if vals else None,'median_pct':statistics.median(vals) if vals else None,'min_pct':min(vals) if vals else None,'max_pct':max(vals) if vals else None,'wtl':wtl}
 sums={k:sum(t.get(k,0) for t in trace) for k in ['ticks','plateau_ticks','episodes','kicks','failed_kicks','improvements','improved_episodes','same_max','accepted','tabu_reject','escape_seconds','recovery_seconds','changed_assignment','changed_office','changed_hull','changed_worker','gain_profit','gain_cost','gain_penalty']}
 sums['plateau_tick_fraction']=sums['plateau_ticks']/max(1,sums['ticks']);sums['episode_improvement_probability']=sums['improved_episodes']/max(1,sums['episodes']);sums['records']=trace
 out['trace'][variant]=sums
(lab/(dest.name.upper()+'_SUMMARY.json')).write_text(json.dumps(out,indent=2))
print(json.dumps({k:{a:v[a] for a in ['mean_pct','median_pct','min_pct','max_pct','wtl']} for k,v in out['variants'].items()},indent=2));print('success',out['success'],'/',out['runs'])
