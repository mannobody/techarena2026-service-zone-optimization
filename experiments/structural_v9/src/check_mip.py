"""Independent assignment MILP with exact geometric witness cuts, offline only.
Reuses audited research model, not zone columns or native master's bounds.
"""
import hashlib,json,os,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
old=ROOT/'experiments/v8_exact_neighborhoods';sys.path.insert(0,str(old/'offline_deps'));sys.path.insert(0,str(old/'src'))
from mip import improve
from legacy_mip import score
os.sched_setaffinity(0,{14,15})
d=R/'logs/mip_crosscheck';d.mkdir(exist_ok=False);rows=[]
for name in ['small_grid','small_load','small_road']:
    data=json.loads((R/'inputs/dev'/f'{name}.json').read_text())
    inc=json.loads((R/'logs/screen8'/f'{name}_9001_zones.solution.json').read_text())
    for backend in ['highs','scip']:
        result=improve(data,inc,list(range(len(data['sites']))),kind='structure',backend=backend,seconds=30,export=str(d/f'{name}_{backend}'))
        (d/f'{name}_{backend}.json').write_text(json.dumps(result,indent=2))
        rows.append({k:v for k,v in result.items()if k not in ['solution','events','selected','offices']})
        print(json.dumps(dict(case=name,backend=backend,value=result['value'],bound=result['bound'],optimal=result['conditional_optimal'],official=score(data,result['solution']))),flush=True)
(d/'PROVENANCE.json').write_text(json.dumps({str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()for p in [old/'src/mip.py',old/'src/legacy_mip.py',Path(__file__)]},indent=2))
(d/'results.json').write_text(json.dumps(rows,indent=2))
