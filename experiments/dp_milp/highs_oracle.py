from pathlib import Path
import json
from highs_selection import Instance,improve
H=Path(__file__).resolve().parent;rows=[]
for old in json.loads((H/'logs/milp_oracle.json').read_text()):
 I=Instance(old['data']);inc=[dict(officeId=o,sites=list(range(4*o,4*o+4)),workers=[o]) for o in range(3)];r=improve(I,inc,60)
 assert r['status']=='HighsModelStatus.kOptimal' and abs(r['value']-old['expected'])<1e-6,(old['seed'],r)
 rows.append(dict(seed=old['seed'],expected=old['expected'],value=r['value'],seconds=r['seconds']))
(H/'logs/highs_oracle.json').write_text(json.dumps(rows,indent=2));print(len(rows),'HiGHS / exhaustive matches')
