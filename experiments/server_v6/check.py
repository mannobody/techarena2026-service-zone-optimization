"""Build the actual v6 ZIP and verify its runtime and no-argument file contract."""
import json
import os
import re
import shutil
import subprocess
import sys
import time
import zipfile

from build import HERE, ROOT, RESEARCH, ZIP_SHA, sha

sys.path.insert(0, str(ROOT / 'task'))
from validate_solution import validate


def main():
    archive = ROOT / 'dist/case03_cpp_server_v6_O3.zip'
    assert sha(archive) == ZIP_SHA
    logs = HERE / 'logs/package_check'
    logs.mkdir(parents=True, exist_ok=False)
    rebuild = logs / 'rebuild'
    rebuild.mkdir()
    with zipfile.ZipFile(archive) as z:
        assert sorted(z.namelist()) == ['Makefile', 'main.cpp']
        for name in z.namelist():
            (rebuild / name).write_bytes(z.read(name))
    with (logs / 'build.log').open('w') as log:
        subprocess.run(['make', 'build'], cwd=rebuild, stdout=log, stderr=subprocess.STDOUT, check=True)
    normalized = {}
    for label, binary in [('v6', rebuild / 'solution'), ('frozen', RESEARCH / 'bin/hybrid_frozen')]:
        target = logs / f'{label}.normalized'
        subprocess.run(['objcopy', '--strip-all', '--remove-section=.note.gnu.build-id', str(binary), str(target)], check=True)
        normalized[label] = sha(target)
    assert normalized['v6'] == normalized['frozen'], 'Runtime differs from the benchmarked candidate'
    spec = json.loads((RESEARCH / 'HYBRID_SYNTHETIC.json').read_text())
    cpus = sorted(os.sched_getaffinity(0))[:2]
    assert len(cpus) == 2
    os.sched_setaffinity(0, set(cpus))
    clean = {k: v for k, v in os.environ.items() if k in ('PATH', 'HOME', 'LANG', 'LD_LIBRARY_PATH')}
    env = clean | {'NT': '2', 'TL': '3', 'SEED': '1400'}
    results = []
    for case, inp in spec['cases'].items():
        work = logs / case
        work.mkdir()
        shutil.copyfile(ROOT / inp, work / 'instance.json')
        start = time.monotonic()
        try:
            p = subprocess.run([str(rebuild / 'solution')], cwd=work, env=env, capture_output=True, timeout=13)
            rc, stderr, timeout = p.returncode, p.stderr, False
        except subprocess.TimeoutExpired as exc:
            rc, stderr, timeout = None, exc.stderr or b'', True
        wall = time.monotonic() - start
        (logs / f'{case}.stderr').write_bytes(stderr)
        value = validate(work / 'instance.json', work / 'solution.json')
        valid = not isinstance(value, str)
        files = sorted(p.name for p in work.iterdir())
        nt = re.search(rb'threads=(\d+)', stderr)
        actual_nt = int(nt[1]) if nt else None
        early = case in {'edge_empty', 'edge_no_offices'} and actual_nt is None
        ok = rc == 0 and not timeout and wall <= 6 and valid and files == ['instance.json', 'solution.json'] and (actual_nt == 2 or early) and not re.search(rb'error:|VERIFY|INVALID', stderr)
        results.append({'case': case, 'input_sha256': sha(ROOT / inp), 'rc': rc, 'timeout': timeout, 'wall': wall,
                        'valid': valid, 'objective_or_error': value, 'actual_nt': actual_nt,
                        'early_return_without_workers': early, 'files': files, 'success': bool(ok)})
        (logs / 'results.json').write_text(json.dumps(results, indent=2) + '\n')
        print(case, 'OK' if ok else 'FAIL', flush=True)
    report = {'zip_sha256': sha(archive), 'source_sha256': sha(rebuild / 'main.cpp'),
              'binary_sha256': sha(rebuild / 'solution'), 'normalized_sha256': normalized,
              'same_compiled_runtime': True, 'expected': len(spec['cases']), 'completed': len(results),
              'passed': sum(r['success'] for r in results), 'file_contract': 'no arguments; instance.json -> solution.json',
              'affinity': cpus, 'seconds': 3, 'quality_reference': 'experiments/v4_deep_parallel/integration/FINAL_RESULTS.json'}
    (HERE / 'CHECK.json').write_text(json.dumps(report, indent=2) + '\n')
    assert len(results) == 28 and all(r['success'] for r in results)
    print('v6: runtime identical to frozen candidate; 28/28 file-contract and validity checks passed.')


if __name__ == '__main__':
    main()
