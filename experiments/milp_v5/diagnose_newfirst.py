from pathlib import Path
import json,time
from envelopes_newfirst import expand
from grouped_flow import Instance,improve
H=Path(__file__).resolve().parent;D=H/'logs/reopen_newfirst60';D.mkdir();I=Instance.read(H.parent/'dp_milp/data/full_holdout/large0.json');inc=json.loads((H.parent/'dp_milp/logs/full_holdout60/large0_111_candidate.json').read_text());t=time.perf_counter();pool,stats=expand(I,inc,4,True);r=improve(I,inc,55-(time.perf_counter()-t),'joint',D/'checkpoint.json',pool,True);r.update(stats,pool_sizes={str(o):len(ss) for o,ss in pool.items()},total_seconds=time.perf_counter()-t);(D/'results.json').write_text(json.dumps(r,indent=2));print({k:v for k,v in r.items() if k not in ['solution','invalid']},flush=True)
