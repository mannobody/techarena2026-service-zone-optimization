"""Supplemental six-seed variance analysis; does not reweight primary results."""
import json
import statistics
from pathlib import Path

R = Path(__file__).resolve().parent
assert (R / 'logs/inst4_variance60/COMPLETE.json').exists()
rows = []
for directory in ['open60', 'inst4_variance60']:
    for row in json.loads((R / 'logs' / directory / 'results.json').read_text()):
        if row['case'] == 'inst4':
            rows.append(row | {'source_directory': directory})
assert len(rows) == 12 and all(r['success'] and r['actual_nt'] == 2 for r in rows)
by = {(r['seed'], r['variant']): r for r in rows}
assert set(by) == {(seed, variant) for seed in range(1602, 1608) for variant in ['v4', 'hybrid']}
pairs = []
for seed in range(1602, 1608):
    b, c = by[seed, 'v4'], by[seed, 'hybrid']
    assert b['affinity'] == c['affinity']
    delta = c['objective']-b['objective']
    pairs.append({'seed': seed, 'v4': b['objective'], 'hybrid': c['objective'],
                  'delta': delta, 'pct': 100*delta/abs(b['objective']),
                  'affinity': b['affinity'], 'source_directory': b['source_directory']})
values = [p['pct'] for p in pairs]
bm, cm = statistics.median(p['v4'] for p in pairs), statistics.median(p['hybrid'] for p in pairs)
m = {'successful_runs': 12, 'pairs': pairs, 'mean_pct': statistics.mean(values),
     'median_paired_pct': statistics.median(values), 'stdev_pct': statistics.stdev(values),
     'min_pct': min(values), 'max_pct': max(values),
     'baseline_median': bm, 'candidate_median': cm,
     'median_objective_ratio_pct': 100*(cm-bm)/abs(bm),
     'wins': sum(p['delta']>1e-7 for p in pairs),
     'ties': sum(abs(p['delta'])<=1e-7 for p in pairs),
     'losses': sum(p['delta']<-1e-7 for p in pairs),
     'scope': 'One known open instance. Four extra seeds were registered after observing variation in first two. No runtime tuning.'}
(R / 'INST4_POOLED6.json').write_text(json.dumps(m, indent=2))
print(json.dumps({k:v for k,v in m.items() if k != 'pairs'}, indent=2))
