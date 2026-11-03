import hashlib,json,os,subprocess,sys,time,zipfile
from pathlib import Path
R=Path(__file__).resolve().parents[1];ROOT=R.parents[1];sys.path.insert(0,str(ROOT/'task'))
from validate_solution import validate
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
source=R/'artifacts/v5/main.cpp';measured=R/'artifacts/v5/candidate';rows=[]
for mode,name in [(1,'geometry'),(2,'memetic')]:
 d=R/('package_'+name);d.mkdir(exist_ok=False)
 (d/'main.cpp').write_bytes(source.read_bytes())
 (d/'Makefile').write_text('build:\n\tg++ -O3 -std=c++17 -o solution main.cpp\n\nrun:\n\tNT=2 ZM_POOL=0 ZM_RESERVE=0 GW_MODE='+str(mode)+' ./solution\n')
 with zipfile.ZipFile(R/(name+'_experimental.zip'),'w',zipfile.ZIP_DEFLATED)as z:
  for f in ['main.cpp','Makefile']:z.write(d/f,f)
d=R/'artifacts/package_rebuild';d.mkdir(exist_ok=False);(d/'main.cpp').write_bytes(source.read_bytes())
cmd=['taskset','-c','14,15','g++','-O3','-std=c++17',str(d/'main.cpp'),'-o',str(d/'solution')]
subprocess.run(cmd,check=True);assert sha(d/'solution')==sha(measured),(sha(d/'solution'),sha(measured))
tests={'negative_balance':ROOT/'experiments/structural_v9/inputs/negative_improves_global_balance.json','grid':ROOT/'experiments/structural_v9/inputs/dev/grid_boundary.json','huge':ROOT/'experiments/structural_v9/inputs/dev/huge.json'}
for mode in [1,2]:
 for name,inp in tests.items():
  wd=d/f'{name}_{mode}';wd.mkdir();(wd/'instance.json').write_bytes(inp.read_bytes())
  env={'PATH':os.environ['PATH'],'TL':'2','GW_MODE':str(mode),'ZM_POOL':'0','ZM_RESERVE':'0'}
  start=time.monotonic()
  with (d/f'{name}_{mode}.stderr').open('x')as f:p=subprocess.run(['taskset','-c','14,15',str(d/'solution')],cwd=wd,env=env,stderr=f,timeout=5)
  v=validate(wd/'instance.json',wd/'solution.json');files=sorted(p.name for p in wd.iterdir())
  rows.append(dict(mode=mode,case=name,rc=p.returncode,wall=time.monotonic()-start,official=v,valid=isinstance(v,(int,float)),files=files))
  assert p.returncode==0 and isinstance(v,(int,float))and files==['instance.json','solution.json'],rows[-1]
(R/'PACKAGE_CHECK.json').write_text(json.dumps(dict(source_sha256=sha(source),measured_binary_sha256=sha(measured),rebuild_binary_sha256=sha(d/'solution'),command=cmd,byte_identical=True,cases=rows,zip_sha256={name:sha(R/(name+'_experimental.zip'))for name in ['geometry','memetic']}),indent=2))
print(json.dumps(dict(byte_identical=True,valid=len(rows),cases=len(rows))))
