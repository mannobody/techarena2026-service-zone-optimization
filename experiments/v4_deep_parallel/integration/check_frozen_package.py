"""After the root benchmark releases CPU20/21, verify the exact ZIP build.

That pair has exactly one two-variant block in HYBRID_280.json. No other lab
owns it. Waiting does not occupy a solver core.
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
import zipfile
from pathlib import Path

R = Path(__file__).resolve().parent
ROOT = R.parents[2]
sys.path.insert(0, str(ROOT / 'task'))
from validate_solution import validate

spec = json.loads((R / 'HYBRID_280.json').read_text())
assert len(spec['cases']) * len(spec['seeds']) == 12 and len(spec['cpu_pairs']) == 7
assert spec['cpu_pairs'][-1] == [20, 21] and len(spec['variants']) == 2
rows_path = R / 'logs/hybrid_280/results.json'
while True:
    rows = json.loads(rows_path.read_text()) if rows_path.exists() else []
    if sum(r['affinity'] == [20, 21] for r in rows) == 2:
        break
    time.sleep(2)
os.sched_setaffinity(0, {20, 21})
manifest = json.loads((R / 'PACKAGE.json').read_text())
for name, sha in manifest['files'].items():
    assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == sha
archive = next(ROOT / f for f in manifest['files'] if f.endswith('.zip'))
d = R / 'artifacts/zip_rebuild'
d.mkdir(exist_ok=False)
with zipfile.ZipFile(archive) as z:
    assert sorted(z.namelist()) == ['Makefile', 'main.cpp']
    for name in z.namelist():
        (d / name).write_bytes(z.read(name))
assert (d / 'main.cpp').read_bytes() == (R / 'src/hybrid_frozen.cpp').read_bytes()
with (R / 'logs/package_build.log').open('w') as out:
    subprocess.run(['make', 'build'], cwd=d, stdout=out, stderr=subprocess.STDOUT, check=True)
freeze = json.loads((R / 'FINAL_FREEZE.json').read_text())
actual_sha = hashlib.sha256((d / 'solution').read_bytes()).hexdigest()
build = {'binary_sha256': actual_sha, 'frozen_binary_sha256': freeze['binary_sha256'],
         'byte_identical_binary': actual_sha == freeze['binary_sha256']}
# ELF STT_FILE and linker build-id may differ merely because the package source
# is named main.cpp. Compare copies with only this non-runtime metadata removed.
normalized = []
for label, binary in [('frozen', R / 'bin/hybrid_frozen'), ('package', d / 'solution')]:
    out = d / f'{label}.normalized'
    subprocess.run(['objcopy', '--strip-all', '--remove-section=.note.gnu.build-id', str(binary), str(out)], check=True)
    normalized.append(hashlib.sha256(out.read_bytes()).hexdigest())
build['normalized_sha256'] = dict(zip(['frozen', 'package'], normalized))
build['identical_after_removing_symbol_table_and_build_id'] = normalized[0] == normalized[1]
(R / 'PACKAGE_BUILD.json').write_text(json.dumps(build, indent=2))
assert normalized[0] == normalized[1], 'Compiled runtime differs: inspect before quality claims.'

test_spec = json.loads((R / 'HYBRID_SYNTHETIC.json').read_text())
test_spec.update(destination=str((R / 'logs/frozen_synthetic').relative_to(ROOT)),
                 cpu_pairs=[[20, 21]], variants={'hybrid': {'binary': str((d / 'solution').relative_to(ROOT))}})
test_path = R / 'FROZEN_SYNTHETIC.json'
test_path.write_text(json.dumps(test_spec, indent=2))
subprocess.run([sys.executable, str(ROOT / 'experiments/v4_deep_parallel/shared/run_blocks.py'), str(test_path)], check=True)
rows = json.loads((R / 'logs/frozen_synthetic/results.json').read_text())
exceptions = {'edge_empty', 'edge_no_offices'}
audit = []
for r in rows:
    normal = r['rc'] == 0 and not r['timeout'] and r['wall'] <= 6 and r['valid'] and not r['error_log']
    early = r['case'] in exceptions and r['actual_nt'] is None
    ok = normal and (r['actual_nt'] == 2 or early)
    audit.append({'case': r['case'], 'success': ok, 'raw_success': r['success'],
                  'known_early_return_before_thread_creation': early})
(R / 'FROZEN_SYNTHETIC_AUDIT.json').write_text(json.dumps(audit, indent=2))
assert len(audit) == 28 and all(x['success'] for x in audit)

contracts = R / 'logs/frozen_contract'
contracts.mkdir(exist_ok=False)
results = []
for case in ['edge_empty', 'edge_no_offices', 'edge_same_point', 'edge_collinear', 'edge_A0', 'edge_multiskill']:
    dest = contracts / case
    dest.mkdir()
    shutil.copyfile(ROOT / 'results/local/synth' / f'{case}.json', dest / 'instance.json')
    start = time.monotonic()
    p = subprocess.run([str(d / 'solution')], cwd=dest, capture_output=True, timeout=15,
                       env={'PATH': os.environ['PATH'], 'NT': '2', 'TL': '2', 'SEED': '1400'})
    wall = time.monotonic() - start
    (contracts / f'{case}.stderr').write_bytes(p.stderr)
    value = validate(dest / 'instance.json', dest / 'solution.json')
    files = sorted(x.name for x in dest.iterdir())
    results.append({'case': case, 'rc': p.returncode, 'wall': wall, 'files': files,
                    'objective_or_error': value,
                    'success': p.returncode == 0 and wall <= 5 and not isinstance(value, str)
                    and files == ['instance.json', 'solution.json']})
(contracts / 'results.json').write_text(json.dumps(results, indent=2))
assert all(r['success'] for r in results)
(R / 'PACKAGE_CHECK_COMPLETE.json').write_text(json.dumps({'synthetic': len(audit), 'contract': len(results), **build}, indent=2))
print('Frozen ZIP: identical compiled runtime, 28 synthetic and 6 file-contract cases passed.', flush=True)
