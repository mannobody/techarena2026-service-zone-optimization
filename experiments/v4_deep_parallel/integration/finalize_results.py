"""Summarize complete frozen comparisons; retain every pair and failure."""
import json
import re
import statistics
from pathlib import Path
from summarize import summary

R = Path(__file__).resolve().parent
series = [('holdout60', 'holdout_primary60', 72),
          ('holdout280', 'holdout_confirmation280', 12),
          ('development280', 'hybrid_280', 24),
          ('open60', 'open60', 20)]
results = {}
for label, directory, expected in series:
    path = R / 'logs' / directory
    data = summary(path)
    assert data['completed_marker'] and data['runs'] == expected
    rows = json.loads((path / 'results.json').read_text())
    keys = [(r['case'], r['seed'], r['variant']) for r in rows]
    assert len(keys) == len(set(keys))
    spec = json.loads((path / 'MANIFEST.json').read_text())['spec']
    expected_keys = {(case, seed, variant) for case in spec['cases']
                     for seed in spec['seeds'] for variant in spec['variants']}
    assert set(keys) == expected_keys
    by_key = {(r['case'], r['seed'], r['variant']): r for r in rows}
    assert all(by_key[case, seed, 'v4']['affinity'] == by_key[case, seed, 'hybrid']['affinity']
               for case in spec['cases'] for seed in spec['seeds'])
    data['runtime'] = {}
    for variant in ['v4', 'hybrid']:
        rs = [r for r in rows if r['variant'] == variant]
        memory_matches = [re.search(r'rss_kb=(\d+)', r['resource']) for r in rs]
        mem = [int(m[1]) / 1024 for m in memory_matches if m]
        data['runtime'][variant] = {'runs': len(rs), 'successful': sum(r['success'] for r in rs),
                                   'max_wall': max(r['wall'] for r in rs),
                                   'median_wall': statistics.median(r['wall'] for r in rs),
                                   'max_rss_mib': max(mem) if mem else None,
                                   'missing_rss_records': sum(m is None for m in memory_matches),
                                   'nonzero_exit': sum(r['rc'] != 0 for r in rs),
                                   'timeout': sum(r['timeout'] for r in rs),
                                   'invalid': sum(not r['valid'] for r in rs),
                                   'wall_exceeded': sum(r['wall'] > spec['seconds']+3 for r in rs),
                                   'error_log': sum(r['error_log'] for r in rs),
                                   'wrong_or_missing_nt': sum(r['actual_nt'] != 2 for r in rs)}
    results[label] = data
    (R / f'{label.upper()}_SUMMARY.json').write_text(json.dumps(data, indent=2))
(R / 'FINAL_RESULTS.json').write_text(json.dumps(results, indent=2))

lines = ['# Frozen hybrid versus exact server v4', '',
         'All percentages are descriptive paired objective changes. These are not hidden-test scores.',
         'Each pair uses identical CPU affinity, NT=2, and the same total time budget.', '',
         '| Series | Successful runs | Pairs | Mean Δ% | Median Δ% | Worst Δ% | Best Δ% | SD Δ% | W/T/L |',
         '|---|---:|---:|---:|---:|---:|---:|---:|---:|']
for name, data in results.items():
    v = data['variants']['hybrid']
    vals = ' | '.join(f'{v[k]:+.6f}' for k in ['mean_pct', 'median_pct', 'min_pct', 'max_pct', 'stdev_pct'])
    lines.append(f'| {name} | {data["successful"]}/{data["runs"]} | {v["pairs"]} | {vals} | {v["wins"]}/{v["ties"]}/{v["losses"]} |')
lines += ['', '## Runtime and process status', '',
          '| Series | Variant | Max wall (s) | Median wall (s) | Peak RSS (MiB) | RE / timeout / invalid / wrong NT / wall / error log |',
          '|---|---|---:|---:|---:|---|']
for name, data in results.items():
    for variant, rt in data['runtime'].items():
        errors = '/'.join(str(rt[k]) for k in ['nonzero_exit','timeout','invalid','wrong_or_missing_nt','wall_exceeded','error_log'])
        rss = f'{rt["max_rss_mib"]:.2f}' if rt['max_rss_mib'] is not None else 'missing'
        lines.append(f'| {name} | {variant} | {rt["max_wall"]:.3f} | {rt["median_wall"]:.3f} | {rss} | {errors} |')
for name, data in results.items():
    v = data['variants']['hybrid']
    lines += ['', f'## {name}: per-instance results', '',
              '| Class | Seeds | Baseline median | Candidate median | Ratio of medians Δ% | Mean paired Δ% | Worst paired Δ% |',
              '|---|---:|---:|---:|---:|---:|---:|']
    for case, c in sorted(v['cases'].items()):
        def fmt(x): return 'n/a (zero baseline)' if x is None else f'{x:+.6f}'
        lines.append(f'| {case} | {c["pairs"]} | {c["baseline_median"]:.6f} | {c["candidate_median"]:.6f} | {fmt(c["median_objective_ratio_pct"])} | {fmt(c["paired_mean_pct"])} | {fmt(c["paired_min_pct"])} |')
    lines += ['', f'Percent mean uses {v["nonzero_reference_pairs"]}/{v["pairs"]} nonzero-reference pairs.']
lines += ['', '## Interpretation limits', '',
          'The primary holdout contains 12 fresh generated instances with three solver seeds each,',
          'not 36 independent instances. The TL280 confirmation reuses six of those fresh instances',
          'with a new solver seed. Development TL280 uses six earlier development instances and',
          'two new solver seeds. Open examples are compatibility checks, not tuning inputs.',
          'Source and binary were frozen before holdout generation and were not changed afterward.',
          'CPU type is controlled within pairs; full-machine frequency/power effects remain.']
(R / 'RESULTS_TABLE.md').write_text('\n'.join(lines)+'\n')
print(json.dumps({k: {x: v['variants']['hybrid'][x] for x in ['pairs','mean_pct','median_pct','min_pct','wins','ties','losses']}
                  for k,v in results.items()}, indent=2))
