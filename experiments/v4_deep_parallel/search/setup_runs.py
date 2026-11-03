from pathlib import Path
import json
R=Path(__file__).resolve().parent;ROOT=R.parents[2]
s=(ROOT/'experiments/v4_local_search/run.py').read_text().replace('parents[2]; R=', 'parents[3]; R=')
# The script is nested one directory deeper than old run.py.
(R/'run.py').write_text(s)
cases={c:v['path'] for c,v in json.loads((R/'INPUTS.json').read_text()).items()}
variants={'v4':{'binary':'experiments/v4_deep_parallel/shared/v4','env':{'DBG':'1'}}}
for name,flag in [('batch','LAB_BATCH'),('alns','LAB_ALNS'),('archive','LAB_ARCHIVE'),('wide','LAB_WIDE'),('memo','LAB_MEMO')]:
 variants[name]={'binary':'experiments/v4_deep_parallel/search/bin/lab','env':{'DBG':'1',flag:'1'}}
spec={'name':'screen60','seconds':60,'jobs':4,'cpu_offset':8,'cases':cases,'seeds':[1101,1102],'variants':variants}
(R/'SCREEN60.json').write_text(json.dumps(spec,indent=2))
