"""Read-only retrospective score audit; no solver runs or historical file edits."""
from pathlib import Path
import csv, hashlib, json, statistics

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
def read(p):
    return json.loads((ROOT / p).read_text())
def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

source = ROOT / 'experiments/milp_v5_boundaries/artifacts/native_safe.cpp'
assert sha(source) == '4144e63be49b938ca4885562dfd87bfdec78e46c8b3bd2ee9d32907997ff7bee'
series = 'experiments/milp_v5_boundaries/logs/safe_holdout60/results.json'
raw = read(series)
assert raw['config']['exe'] == 'native_safe'
assert raw['config']['seconds'] == 60 and raw['config']['threads'] == 2
rows = raw['results']
assert len(rows) == 60 and all(x['rc'] == 0 and x['error'] is None for x in rows)
by = {(x['case'], x['seed'], x['variant']): x for x in rows}
pairs, cases = [], []
for case in sorted({x['case'] for x in rows}):
    pp = []
    for seed in [201, 202, 203]:
        old, new = by[case, seed, 'base'], by[case, seed, 'candidate']
        assert old['input'] == new['input']
        inp = Path(new['input'])
        p = dict(case=case, seed=seed, input=str(inp.relative_to(ROOT)),
                 input_sha256=sha(inp), old_model='v5', old_score=old['score'],
                 v52_score=new['score'], v52_percent=100*(new['score']-old['score'])/abs(old['score']),
                 seconds=60, threads=2, source_series=series)
        pairs.append(p); pp.append(p)
    cases.append(dict(case=case, mean_v52_percent=statistics.mean(p['v52_percent'] for p in pp),
                      negative_seeds=[dict(seed=p['seed'], percent=p['v52_percent']) for p in pp if p['v52_percent'] < -1e-7],
                      input=pp[0]['input'], input_sha256=pp[0]['input_sha256']))

# Distinct package campaigns, not a randomized paired comparison.
pkg = read('experiments/milp_v5_boundaries/logs/package_safe60_v2/results.json')
index = {sha(Path(x['input'])): x for x in pkg}
oldpkg = read('experiments/server_v4/logs/package60/results.json')
package_pairs = []
for x in oldpkg:
    b = index.get(sha(Path(x['input'])))
    if b is None:
        continue
    assert x['seconds'] == b['seconds'] == 60 and x['threads'] == b['threads'] == 2
    assert x['seed'] == b['seed'] == 101
    package_pairs.append(dict(case=x['case'], input=x['input'], old_score=x['score'],
                              v52_score=b['score'], delta=b['score']-x['score']))

# These are ports of historical methods on the v5.2 base, NOT pure historical binaries.
long_series = 'experiments/submission_1668601_v12/logs/development280/results.json'
long = read(long_series)
idx = {(x['case'], x['seed'], x['variant']): x for x in long}
ports = []
for x in long:
    if x['variant'] not in ['hybrid', 'plateau']:
        continue
    b = idx[x['case'], x['seed'], 'submission']
    assert x['valid'] and b['valid'] and x['success'] and b['success']
    assert x['affinity'] == b['affinity']
    if x['official'] > b['official'] + 1e-7:
        ports.append(dict(case=x['case'], seed=x['seed'], port=x['variant'],
                          parent_method='v6' if x['variant']=='hybrid' else 'v8',
                          old_port_score=x['official'], v52_score=b['official'],
                          v52_percent=100*(b['official']-x['official'])/abs(x['official']),
                          seconds=280, threads=2, source_series=long_series,
                          pure_historical_binary=False))

result = dict(v52_source_sha256=sha(source), no_new_benchmarks=True,
              direct_v5=dict(pairs=pairs, cases=cases, highs='Enabled by original runner LD_LIBRARY_PATH',
                             randomized_pinned=False, matched_input_seed_budget=True),
              v4_package=dict(pairs=package_pairs, negative=[p for p in package_pairs if p['delta'] < -1e-7],
                              scope='26 edge/precision/crossing checks; separate campaigns, no general-quality conclusion'),
              historical_method_ports=ports,
              gaps=['No comparable complete direct v5.2 versus v2/v3 general-quality campaign located.',
                    'v7 is an exact copy of v4, not an independent algorithm.',
                    'No pure v6/v8 versus v5.2 paired TL280 campaign located; port data are explicitly separate.',
                    'Names such as huge0 are not input identities; compare paths/hashes.',
                    'Rejected early v5.2 and SIGSEGV coop revision are excluded from final safe-v5.2 statistics.'])
(OUT / 'AUDIT.json').write_text(json.dumps(result, ensure_ascii=False, indent=2))
with (OUT / 'V5_PAIRS.csv').open('w') as f:
    w=csv.DictWriter(f, fieldnames=list(pairs[0]));w.writeheader();w.writerows(pairs)
print(json.dumps(dict(direct_pairs=len(pairs), negative_pairs=sum(p['v52_percent'] < -1e-7 for p in pairs),
                      negative_case_means=[c for c in cases if c['mean_v52_percent'] < 0],
                      v4_package_pairs=len(package_pairs), v4_package_losses=sum(p['delta'] < -1e-7 for p in package_pairs),
                      ports=ports), ensure_ascii=False, indent=2))
