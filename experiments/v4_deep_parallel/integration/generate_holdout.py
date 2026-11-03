"""Generate the preregistered inputs only after exact source/binary freeze.

Does not run a solver. Refuses to overwrite earlier holdout inputs.
"""
import hashlib
import json
import random
import sys
from pathlib import Path

R = Path(__file__).resolve().parent
ROOT = R.parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
import gen

freeze = json.loads((R / 'FINAL_FREEZE.json').read_text())
assert hashlib.sha256((ROOT / freeze['source']).read_bytes()).hexdigest() == freeze['sha256']
assert hashlib.sha256((R / 'bin/hybrid_frozen').read_bytes()).hexdigest() == freeze['binary_sha256']
plan = json.loads((R / 'HOLDOUT_PREREGISTRATION.json').read_text())
d = R / 'inputs/holdout'
d.mkdir(exist_ok=False)
cases, records = {}, []
for j, name in enumerate(plan['classes']):
    seed = 751000 + 100 * j
    params = gen.SUITE[name][1](random.Random(seed))
    p = d / f'{name}.json'
    gen.gen2(seed, str(p), **params)
    cases[name] = str(p.relative_to(ROOT))
    records.append({'case': name, 'generator_seed': seed, 'parameters': params,
                    'path': cases[name], 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()})
(R / 'HOLDOUT_INPUTS.json').write_text(json.dumps(records, indent=2))
variants = {'v4': {'binary': 'experiments/v4_deep_parallel/shared/v4'},
            'hybrid': {'binary': str((R / 'bin/hybrid_frozen').relative_to(ROOT))}}
for name in ('primary60', 'confirmation280'):
    spec = plan[name]
    output = {'destination': str((R / 'logs' / f'holdout_{name}').relative_to(ROOT)),
              'seconds': spec['seconds'], 'cpu_pairs': spec['cpu_pairs'],
              'cases': {c: cases[c] for c in spec['classes']},
              'seeds': spec['solver_seeds'], 'variants': variants}
    (R / f'HOLDOUT_{name.upper()}.json').write_text(json.dumps(output, indent=2))
print('Generated', len(records), 'untouched inputs after freeze; no solver was run.')
