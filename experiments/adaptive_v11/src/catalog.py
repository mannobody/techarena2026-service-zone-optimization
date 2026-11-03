import json,hashlib,collections
from pathlib import Path
R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
rows=[]
for p in sorted((ROOT/'experiments').rglob('MANIFEST.json')):
 if R in p.parents:continue
 try:a=json.loads(p.read_text())
 except ValueError:continue
 s=a.get('spec',{});d=p.parent;res=d/'results.json';result=json.loads(res.read_text())if res.exists()else None
 rows.append(dict(path=str(p.relative_to(ROOT)),keys=list(a),seconds=s.get('seconds',a.get('seconds',a.get('tl'))),variants=s.get('variants',{}),cases=s.get('cases',{}),seeds=s.get('seeds'),result_count=len(result)if isinstance(result,list)else None,result_keys=list(result[0])if isinstance(result,list)and result and isinstance(result[0],dict)else None,manifest_sha256=sha(p)))
(R/'CATALOG.json').write_text(json.dumps(rows,indent=2))
for a in rows:
 print(a['path'].replace('experiments/',''),a['seconds'],a['result_count'],list(a['variants']),a['result_keys'][:7]if a['result_keys']else None)
user={str(p.relative_to(ROOT)):sha(p)for p in (ROOT/'solver').glob('*')if p.is_file()}
user|={p:sha(ROOT/p)for p in ['README.md','SOLVER.md','tools/test_geometry_state.cpp']}
(R/'USER_FILES_BEFORE.json').write_text(json.dumps(user,indent=2))
