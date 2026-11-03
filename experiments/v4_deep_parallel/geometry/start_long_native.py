import json,time,sys,subprocess
from pathlib import Path
R=Path(__file__).resolve().parent;ROOT=R.parents[2]
spec=dict(destination=str((R/'logs/v4_anti600').relative_to(ROOT)),seconds=600,cpu_pairs=[[6,7]],cases={'anti':str((R/'inputs/dev_anti.json').relative_to(ROOT))},seeds=[713],variants={'v4':dict(binary='experiments/v4_deep_parallel/shared/v4',env={'DBG':'1'})},snapshots=[60,120,280,450])
(R/'LONG_NATIVE600.json').write_text(json.dumps(spec,indent=2))
while True:
 p=R/'logs/isolated_tail280/results.json'
 if p.exists() and len(json.loads(p.read_text()))==24:break
 time.sleep(2)
raise SystemExit(subprocess.call([sys.executable,str(ROOT/'experiments/v4_deep_parallel/shared/run_blocks.py'),str(R/'LONG_NATIVE600.json')]))
