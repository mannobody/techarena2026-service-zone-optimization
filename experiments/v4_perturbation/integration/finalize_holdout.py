"""Finalize one budget only after all mandatory variance extensions complete."""
import json,math,random,statistics,sys
from pathlib import Path
from verify_freeze import verify
I=Path(__file__).resolve().parent
R=I.parent
ROOT=R.parents[1]
sys.path.insert(0,str(R/'shared'))
from analyze import analyze,describe

def finalize(seconds):
    decision=json.loads((I/f'HOLDOUT{seconds}_DECISION.json').read_text())
    summaries=[]
    for suffix in ['', '_VARIANCE']:
        sp=I/f'HOLDOUT{seconds}{suffix}.json'
        if not sp.exists():
            assert suffix and not decision['variance_extension_reasons']
            continue
        spec=json.loads(sp.read_text());d=ROOT/spec['destination']
        verify(sp,json.loads((d/'MANIFEST.json').read_text()))
        summary=analyze(d)
        assert all(summary['hash_audit'].values())
        summaries.append(summary)
    combined={}
    for key in summaries[0]['comparisons']:
        pairs=sum([s['comparisons'][key]['pairs'] for s in summaries],[])
        assert len({(x['case'],x['seed']) for x in pairs})==len(pairs)
        classes=sorted({x['case'] for x in pairs})
        bycase={c:describe([x['pct'] for x in pairs if x['case']==c and x.get('pct') is not None]) for c in classes}
        means=[x['mean'] for x in bycase.values() if x['n']]
        rng=random.Random(351)
        boots=sorted(statistics.mean(rng.choices(means,k=len(means))) for _ in range(10000)) if means else []
        combined[key]={'pairs':pairs,'by_case':bycase,
            'pair_distribution_descriptive_only':describe([x['pct'] for x in pairs if x.get('pct') is not None]),
            'input_weighted_mean':statistics.mean(means) if means else None,
            'input_mean_distribution':describe(means),
            'input_bootstrap95_mean':[boots[249],boots[9749]] if boots else None,
            'wtl':{k:sum(x.get('result')==k for x in pairs) for k in ['win','tie','loss']},
            'failed_pairs':sum(not x['success'] for x in pairs)}
    total=sum(s['runs'] for s in summaries);success=sum(s['success'] for s in summaries)
    c=combined['candidate_vs_v4'];o=combined['candidate_vs_off']
    checks={'primary_criteria_pass':decision['primary_criteria_pass'],
        'all_primary_and_extra_runs_successful':total==success,
        'freeze_and_record_hash_checks_pass':True,
        'all_percentage_pairs_defined_finite':all(p.get('pct') is not None and math.isfinite(p['pct']) for v in combined.values() for p in v['pairs']),
        'combined_input_weighted_mean_at_least_0.1':c['input_weighted_mean'] is not None and c['input_weighted_mean']>=.1,
        'combined_pair_median_nonnegative':c['pair_distribution_descriptive_only'].get('median',-1)>=0,
        'combined_every_input_median_nonnegative':all(x.get('median',-1)>=0 for x in c['by_case'].values()),
        'combined_worst_at_least_minus1':c['pair_distribution_descriptive_only'].get('min',-1e99)>=-1,
        'combined_bootstrap_lower_nonnegative':bool(c['input_bootstrap95_mean']) and c['input_bootstrap95_mean'][0]>=0,
        'combined_mean_vs_off_nonnegative':o['input_weighted_mean'] is not None and o['input_weighted_mean']>=0}
    result={'seconds':seconds,'runs':total,'success':success,'checks':checks,
        'accepted_at_this_budget':all(checks.values()),'comparisons':combined,
        'note':'Primary and extras remain separately reported. Combined mean gives each input equal weight; individual-pair distribution is descriptive only. No failed run is removed.'}
    out=I/f'HOLDOUT{seconds}_FINAL.json';assert not out.exists();out.write_text(json.dumps(result,indent=2))
    print(json.dumps({k:v for k,v in result.items() if k!='comparisons'},indent=2))
    paths=[I/f'HOLDOUT{t}_FINAL.json' for t in [60,280]]
    if all(p.exists() for p in paths):
        results=[json.loads(p.read_text()) for p in paths]
        (I/'FINAL_DECISION.json').write_text(json.dumps({'accepted':all(x['accepted_at_this_budget'] for x in results),
            'budgets':{x['seconds']:x['checks'] for x in results},
            'independent_inputs':12,'note':'TL280 reuses six of the12 inputs. Passing this gate would still require final contract/record audit; it does not predict hidden-server superiority.'},indent=2))

if __name__=='__main__':finalize(int(sys.argv[1]))
