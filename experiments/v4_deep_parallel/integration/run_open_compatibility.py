"""Open examples are compatibility/regression checks, never tuning inputs."""
import subprocess
import sys
import time
from pathlib import Path

R = Path(__file__).resolve().parent
ROOT = R.parents[2]
while not (R / 'logs/holdout_confirmation280/COMPLETE.json').exists():
    time.sleep(2)
subprocess.run([sys.executable, str(ROOT / 'experiments/v4_deep_parallel/shared/run_blocks.py'),
                str(R / 'OPEN60.json')], check=True)
