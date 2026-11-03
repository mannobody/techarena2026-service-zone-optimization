from pathlib import Path
import json,time,sys
lab=Path(__file__).resolve().parent
(lab/'POLISH_SUPERSEDED.json').write_text(json.dumps({'time':time.time(),'reason':'Parent replaced native-polish repair with bounded boundary(q24) plus boundary-without-kick attribution control before any quality run or freeze. Source and preliminary compiled binary preserved; no benchmark uses this build.','quality_runs':0},indent=2))
# Deliberately stop the retired shell dispatcher before it creates/runs a spec.
sys.exit(75)
