"""Check ZIP payload, defaults, and no-argument file contract in fresh directories."""
import json,hashlib,zipfile,subprocess,os,time,shutil
from pathlib import Path
R=Path(__file__).resolve().parent;ROOT=R.parents[1]
import sys
sys.path.insert(0,str(ROOT/'task'));from validate_solution import validate
manifest=json.loads((R/'PACKAGE_SAFE.json').read_text());pkg=R/'artifacts/package_cycle_safe'
for f,h in manifest['files'].items():assert hashlib.sha256((R/f).read_bytes()).hexdigest()==h
archive=next(R/f for f in manifest['files'] if f.endswith('.zip'))
with zipfile.ZipFile(archive) as z:
 assert sorted(z.namelist())==['Makefile','main.cpp']
 for f in z.namelist():assert z.read(f)==(pkg/f).read_bytes()
s=(pkg/'main.cpp').read_text();assert ': 280.0' in s;assert 'g++ -O3 -std=c++17' in (pkg/'Makefile').read_text()
assert 'vector<State> population(mode==4?4:1,current);' in s
D=R/'logs/package_contract';D.mkdir(exist_ok=False);rows=[]
for c in ['edge_empty','edge_no_offices','edge_same_point','edge_collinear','edge_A0','edge_multi_workers']:
 src=ROOT/'results/local/synth'/f'{c}.json'
 if not src.exists():
  assert c=='edge_multi_workers';src=R/'data/development/multiskill.json'
 d=D/c;d.mkdir();shutil.copyfile(src,d/'instance.json');t=time.monotonic()
 p=subprocess.run(['taskset','-c','20',str(pkg/'solution')],cwd=d,env={'PATH':os.environ['PATH'],'NT':'2','TL':'2','SEED':'901','DBG':'1'},capture_output=True,timeout=15)
 wall=time.monotonic()-t;(D/f'{c}.stderr').write_bytes(p.stderr);files=sorted(x.name for x in d.iterdir());v=validate(d/'instance.json',d/'solution.json');rows.append({'case':c,'rc':p.returncode,'wall':wall,'files':files,'valid':not isinstance(v,str),'objective':v,'success':p.returncode==0 and wall<=5 and not isinstance(v,str) and files==['instance.json','solution.json']})
(D/'results.json').write_text(json.dumps(rows,indent=2));print('contract',sum(x['success'] for x in rows),'/',len(rows));assert all(x['success'] for x in rows)
