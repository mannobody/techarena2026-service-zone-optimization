#!/bin/sh
set -eu
cd .
lab=experiments/v4_perturbation/escape_lab
while [ ! -f "$lab/logs/screen60/COMPLETE.json" ]; do sleep 1; done
while [ ! -f experiments/v4_perturbation/shared/logs/checkpoint280/COMPLETE.json ]; do sleep 1; done
taskset -c 14,15 python3 - <<'PY'
from pathlib import Path
import json
lab=Path('experiments/v4_perturbation/escape_lab');s=json.loads((lab/'SCREEN60.json').read_text());dev=json.loads(Path('experiments/v4_perturbation/shared/DEV_INPUTS.json').read_text())
classes=['anti','tightA','alphabig','multiskill','cluster','huge'];s.update(destination=str(lab/'logs/mature280'),seeds=[2301,2302],order_seed=871033)
s['cases']={c:dev[c]['path'] for c in classes};s['checkpoints']={c:f'experiments/v4_perturbation/shared/logs/checkpoint280/{c}_1902_v4.solution.json' for c in classes}
(lab/'MATURE280.json').write_text(json.dumps(s,indent=2))
PY
NT=2 taskset -c 14,15 .venv/bin/python experiments/v4_perturbation/shared/run_blocks.py "$lab/MATURE280.json" > "$lab/logs/mature280.log" 2>&1
taskset -c 14,15 python3 "$lab/summarize.py" "$lab/logs/mature280" > "$lab/logs/summary280.log"
sh "$lab/run_diagnostic.sh"
