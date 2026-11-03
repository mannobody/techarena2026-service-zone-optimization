"""Causal final-stage diagnostic from identical mature checkpoints, no tuning."""
import hashlib
import json
import os
import random
import subprocess
import sys
import time
from pathlib import Path

R = Path(__file__).resolve().parent
ROOT = R.parents[2]
sys.path.insert(0, str(ROOT / 'task'))
from validate_solution import validate

while not (R / 'PACKAGE_CHECK_COMPLETE.json').exists():
    time.sleep(2)
os.sched_setaffinity(0, {20, 21})
d = R / 'logs/tail_competition'
d.mkdir(exist_ok=False)
bins = {}
for name, flags in [('v4', []), ('hybrid', ['-DPOST_HYBRID'])]:
    binary = R / 'bin' / f'post_tail_{name}'
    with (d / f'build_{name}.log').open('w') as out:
        subprocess.run(['g++', '-O3', '-std=c++17', '-pthread', *flags,
                        str(R / 'src/post_tail.cpp'), '-o', str(binary)],
                       stdout=out, stderr=subprocess.STDOUT, check=True)
    bins[name] = binary
paths = [R / 'src/post_tail.cpp', R / 'src/hybrid_frozen.cpp',
         ROOT / 'experiments/v4_local_search/baseline/frozen_v4.cpp', *bins.values()]
manifest = {'seconds': 3, 'NT': 2, 'post_seed': 1601, 'affinity': [20, 21],
            'purpose': 'fixed checkpoint comparison, not full solver comparison or retuning',
            'hashes': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}}
(d / 'MANIFEST.json').write_text(json.dumps(manifest, indent=2))
rows = []
for case in ['alphabig', 'tightA', 'multiskill', 'anti', 'large', 'huge']:
    inp = R / 'inputs' / f'{case}.json'
    for seed in [1301, 1302]:
        inc = R / 'logs/mature_v4_280' / f'{case}_{seed}_v4.solution.json'
        base = validate(inp, inc)
        variants = [('v4_boundary', 'v4', 0), ('batch_boundary', 'hybrid', 0), ('geometry_joint_boundary', 'hybrid', 1)]
        random.Random(f'{case}:{seed}').shuffle(variants)
        for label, binary, mode in variants:
            output = d / f'{case}_{seed}_{label}.solution.json'
            start = time.monotonic()
            p = subprocess.run([str(bins[binary]), str(inp), str(inc), str(output), '3', str(mode)],
                               env={'PATH': os.environ['PATH'], 'NT': '2', 'SEED': '1601'},
                               capture_output=True, timeout=15)
            wall = time.monotonic() - start
            (d / f'{case}_{seed}_{label}.stderr').write_bytes(p.stderr)
            value = validate(inp, output)
            ok = p.returncode == 0 and wall <= 6 and not isinstance(value, str)
            rows.append({'case': case, 'checkpoint_seed': seed, 'variant': label,
                         'baseline_checkpoint': base, 'objective_or_error': value,
                         'gain': value-base if ok else None, 'rc': p.returncode,
                         'wall': wall, 'success': ok,
                         'input_sha256': hashlib.sha256(inp.read_bytes()).hexdigest(),
                         'checkpoint_sha256': hashlib.sha256(inc.read_bytes()).hexdigest()})
            (d / 'results.json').write_text(json.dumps(rows, indent=2))
            print(len(rows), '/36', case, seed, label, rows[-1]['gain'], ok, flush=True)
(d / 'COMPLETE.json').write_text(json.dumps({'runs': len(rows), 'successful': sum(r['success'] for r in rows)}, indent=2))
assert len(rows) == 36 and all(r['success'] for r in rows)
