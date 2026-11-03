import json
from pathlib import Path
R=Path(__file__).resolve().parent;ROOT=R.parents[2];b=json.loads((R/'BASELINE280.json').read_text())
s=dict(destination=str((R/'logs/full60_dev').relative_to(ROOT)),seconds=60,cpu_pairs=[[0,5],[1,2],[3,4]],cases=b['cases'],seeds=[711,712],variants={'v4':dict(binary='experiments/v4_deep_parallel/shared/v4'),'count':dict(binary=str((R/'bin/candidate_v3').relative_to(ROOT)),env={'GEO_SPLIT':'5'}),'pool':dict(binary=str((R/'bin/candidate_v3').relative_to(ROOT)),env={'GEO_SPLIT':'2'}),'both':dict(binary=str((R/'bin/candidate_v3').relative_to(ROOT)),env={'GEO_SPLIT':'7'})})
(R/'FULL60_DEV.json').write_text(json.dumps(s,indent=2))
