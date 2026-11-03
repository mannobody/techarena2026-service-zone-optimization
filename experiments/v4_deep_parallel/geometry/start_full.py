import time,json,subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parent;ROOT=R.parents[2]
while True:
 p=R/'logs/baseline280/results.json'
 if p.exists():
  rows=json.loads(p.read_text())
  if len(rows)==6:
   assert all(r['success'] for r in rows);break
 time.sleep(5)
raise SystemExit(subprocess.call([sys.executable,str(ROOT/'experiments/v4_deep_parallel/shared/run_blocks.py'),str(R/'FULL60_DEV.json')]))
