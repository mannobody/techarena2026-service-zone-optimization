"""Apply the preregistered acceptance and variance rules without changing a solver.

Primary results remain primary. Extra seeds never replace unfavorable observations.
Run after each completed primary holdout; output specs are immutable.
"""
import json, math, statistics, sys, time
from pathlib import Path

R = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(R/'shared'))
from analyze import analyze, describe
from verify_freeze import verify

def write_new(path, value):
    content = json.dumps(value, indent=2)
    if path.exists():
        assert json.loads(path.read_text()) == json.loads(content), f'refusing overwrite: {path}'
    else:
        path.write_text(content)

def evaluate(seconds):
    specpath = R/'integration'/f'HOLDOUT{seconds}.json'
    spec = json.loads(specpath.read_text())
    root = R.parents[1]
    verify(specpath,json.loads((root/spec['destination']/'MANIFEST.json').read_text()))
    summary = analyze(root/spec['destination'])
    write_new(R/'integration'/f'HOLDOUT{seconds}_SUMMARY.json', summary)
    candidate = summary['comparisons']['candidate_vs_v4']
    off = summary['comparisons']['candidate_vs_off']
    stats = candidate['distribution_valid_outputs_including_failed_processes']
    counts={key:{'expected':len(x['pairs']), 'defined_finite':sum(p.get('pct') is not None and math.isfinite(p['pct']) for p in x['pairs'])} for key,x in summary['comparisons'].items()}
    checks = {
        'all_processes_successful': summary['runs'] == summary['success'],
        'all_hash_checks_pass': all(summary['hash_audit'].values()),
        'all_percentage_pairs_defined_finite':all(x['expected']==x['defined_finite'] for x in counts.values()),
        'mean_at_least_0.1_percent': stats.get('mean', -1e99) >= .1,
        'median_nonnegative': stats.get('median', -1e99) >= 0,
        'every_input_median_nonnegative': all(x.get('median', -1) >= 0 for x in candidate['by_case'].values()),
        'worst_at_least_minus_1_percent': stats.get('min', -1e99) >= -1,
        'input_bootstrap_lower95_nonnegative': bool(candidate['instance_bootstrap95_mean']) and candidate['instance_bootstrap95_mean'][0] >= 0,
        'mean_vs_off_nonnegative': off['distribution_valid_outputs_including_failed_processes'].get('mean', -1e99) >= 0,
    }
    # Check both required comparator contrasts, conservatively applying the
    # predeclared paired-delta variability rule to either of them.
    reasons = {}
    for comparison in ['candidate_vs_v4', 'candidate_vs_off', 'off_vs_v4']:
        for case, x in summary['comparisons'][comparison]['by_case'].items():
            if x.get('sample_sd', 0) > .5 or x.get('max', 0)-x.get('min', 0) > 1:
                reasons.setdefault(case, []).append({'comparison':comparison,'sample_sd':x['sample_sd'],'range':x['max']-x['min']})
    decision = {'seconds': seconds, 'checks': checks, 'primary_criteria_pass':all(checks.values()),
                'percentage_pair_counts':counts,
                'variance_extension_reasons':reasons,
                'note':'Provisional primary decision only. Final acceptance also checks every extension run, all freeze hashes and both budgets. Multiple seeds of one input are not independent instances.'}
    write_new(R/'integration'/f'HOLDOUT{seconds}_DECISION.json', decision)
    if reasons:
        extra = dict(spec)
        extra['destination'] = f'experiments/v4_perturbation/integration/logs/holdout{seconds}_variance'
        extra['cases'] = {k:v for k,v in spec['cases'].items() if k in reasons}
        extra['seeds'] = [2104,2105] if seconds == 60 else [2203,2204]
        extra['order_seed'] = 422
        write_new(R/'integration'/f'HOLDOUT{seconds}_VARIANCE.json', extra)
    print(json.dumps(decision, indent=2))

if __name__ == '__main__':
    evaluate(int(sys.argv[1]))
