import collections,hashlib,json,random,statistics,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
dest=Path(sys.argv[1]);rows=json.loads((dest/'results.json').read_text());complete=json.loads((dest/'COMPLETE.json').read_text())
f=json.loads((R/'FREEZE.json').read_text())
assert complete['completed']==complete['expected']
for p,h in f['files'].items():assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h,p
groups=collections.defaultdict(dict)
for r in rows:groups[r['case'],r['seed']][r['variant']]=r
def comparison(candidate,baseline):
    by=collections.defaultdict(list);pairs=[];invalid=[];undefined=[];details=[]
    for (case,seed),g in groups.items():
        if candidate not in g or baseline not in g:continue
        c,b=g[candidate],g[baseline]
        if not c['success'] or not b['success']:invalid.append(dict(case=case,seed=seed))
        if b['objective'] is None or c['objective'] is None or b['objective']==0:
            undefined.append(dict(case=case,seed=seed));continue
        delta=100*(c['objective']-b['objective'])/abs(b['objective']);by[case].append(delta);pairs.append(delta)
        details.append(dict(case=case,seed=seed,baseline=b['objective'],candidate=c['objective'],delta_pct=delta))
    means=[statistics.mean(v) for v in by.values()];rng=random.Random(792);boot=[]
    for i in range(10000):boot.append(statistics.mean(rng.choices(means,k=len(means))))
    boot.sort()
    return dict(pairs=len(pairs),independent_inputs=len(by),input_weighted_mean=statistics.mean(means),median=statistics.median(pairs),worst=min(pairs),
        WTL=[sum(x>1e-7 for x in pairs),sum(abs(x)<=1e-7 for x in pairs),sum(x< -1e-7 for x in pairs)],
        bootstrap95=[boot[249],boot[9749]],invalid_pairs=invalid,undefined=undefined,
        by_input={k:dict(mean=statistics.mean(v),median=statistics.median(v),worst=min(v)) for k,v in by.items()},details=details)
contrasts=[('candidate','v4'),('candidate','v8'),('candidate','off'),('off','v4')]
if any(r['variant']=='fill_only' for r in rows):contrasts += [('fill_only','off'),('worker_only','off'),('fill_only','v4'),('worker_only','v4')]
summary={f'{a}_vs_{b}':comparison(a,b) for a,b in contrasts};main=summary['candidate_vs_v4']
criteria=dict(all_runs_successful=all(r['success'] for r in rows),all_results_valid=all(r['valid'] for r in rows),
    wall_within_nominal_plus_point1=all(r['within_nominal_plus_0.1'] for r in rows),
    mean_vs_v4_at_least_point1=main['input_weighted_mean']>=.1,
    median_nonnegative=main['median']>=-1e-7,every_input_median_nonnegative=all(v['median']>=-1e-7 for v in main['by_input'].values()),
    worst_at_least_minus1=main['worst']>=-1,bootstrap_lower_nonnegative=main['bootstrap95'][0]>=0,
    mean_vs_off_nonnegative=summary['candidate_vs_off']['input_weighted_mean']>=0,
    mean_vs_v8_nonnegative=summary['candidate_vs_v8']['input_weighted_mean']>=0,
    all_percentages_defined=all(not r['undefined'] for r in summary.values()))
result=dict(complete=complete,accepted_this_budget=all(criteria.values()),criteria=criteria,summary=summary,
    max_wall=max(r['wall'] for r in rows),external_budget_stops=sum(r.get('hard_stopped',False) for r in rows),
    inferred_internal_watchdog_stops=sum(r.get('watchdog_exit_inferred',False) for r in rows),
    max_nominal_overrun=max(r.get('nominal_overrun',0) for r in rows))
(dest/'EVALUATION.json').write_text(json.dumps(result,indent=2))
for k,v in summary.items():print(k,json.dumps({kk:vv for kk,vv in v.items() if kk not in ['by_input','details']}))
print('accepted',result['accepted_this_budget'],'failed',[k for k,v in criteria.items() if not v])
