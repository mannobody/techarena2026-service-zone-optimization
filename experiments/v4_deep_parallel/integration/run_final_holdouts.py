"""Run preregistered holdouts when the owning laboratories release their CPUs."""
import concurrent.futures
import hashlib
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

R = Path(__file__).resolve().parent
ROOT = R.parents[2]
runner = ROOT / 'experiments/v4_deep_parallel/shared/run_blocks.py'


def primary():
    marker = R.parent / 'search/CPU_RELEASED.json'
    while not marker.exists():
        time.sleep(2)
    released = json.loads(marker.read_text())
    assert set(released['released_cpus']) == set(range(8, 16))
    subprocess.run(['taskset', '-c', '8-15', sys.executable, str(R / 'generate_holdout.py')], check=True)
    paths = [ROOT / 'tools/gen.py', R / 'generate_holdout.py', R / 'FINAL_FREEZE.json',
             R / 'HOLDOUT_PREREGISTRATION.json']
    provenance = {'generated_utc': datetime.now(timezone.utc).isoformat(),
                  'hashes': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}}
    (R / 'HOLDOUT_GENERATOR_PROVENANCE.json').write_text(json.dumps(provenance, indent=2))
    print('Starting untouched primary TL60 holdout on released search CPUs.', flush=True)
    subprocess.run([sys.executable, str(runner), str(R / 'HOLDOUT_PRIMARY60.json')], check=True)


def confirmation():
    while not (R / 'logs/hybrid_280/COMPLETE.json').exists() or not (R / 'HOLDOUT_CONFIRMATION280.json').exists():
        time.sleep(2)
    print('Starting untouched TL280 confirmation on released root CPUs.', flush=True)
    subprocess.run([sys.executable, str(runner), str(R / 'HOLDOUT_CONFIRMATION280.json')], check=True)


with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
    futures = [executor.submit(primary), executor.submit(confirmation)]
    for future in concurrent.futures.as_completed(futures):
        future.result()
print('Both frozen holdout series completed.', flush=True)
