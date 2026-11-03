import hashlib,json,subprocess,zipfile,shutil,os,sys,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];ROOT=R.parents[1];sys.path.insert(0,str(ROOT/'task'));from validate_solution import validate
os.sched_setaffinity(0,{14,15})
while not (R/'SCREEN_SELECTION.json').exists():time.sleep(1)
s=json.loads((R/'SCREEN_SELECTION.json').read_text())['selected'];env=s['env'];source=R/'artifacts/v4/main.cpp';binary=R/'artifacts/v4/candidate';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
d=R/'package_final';d.mkdir(exist_ok=False);shutil.copy2(source,d/'main.cpp');(d/'Makefile').write_text('build:\n\tg++ -O3 -std=c++17 -o solution main.cpp\n\nrun:\n\tNT=2 AP_POLICY='+env['AP_POLICY']+' AP_SHARE='+env['AP_SHARE']+' ./solution\n')
archive=R/'adaptive_v11_final.zip'
with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED,compresslevel=9)as z:
 for name in ['main.cpp','Makefile']:
  info=zipfile.ZipInfo(name,(2026,10,22,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16;z.writestr(info,(d/name).read_bytes(),compresslevel=9)
b=R/'artifacts/package_rebuild_final';b.mkdir(exist_ok=False)
with zipfile.ZipFile(archive)as z:z.extractall(b)
with (b/'compile.log').open('w')as f:subprocess.run(['make','-C',str(b),'build'],stdout=f,stderr=subprocess.STDOUT,check=True)
assert sha(b/'solution')==sha(binary)
rows=[]
for name,path in [('negative_balance',ROOT/'experiments/warm_v10/artifacts/package_rebuild/negative_balance_1/instance.json'),('grid',R/'inputs/dev/grid180.json'),('huge',R/'inputs/dev/huge10000.json'),('single',R/'logs/specialists_v3/single_0.json'),('line',R/'inputs/line_mechanism/line0.json')]:
 w=b/name;w.mkdir();shutil.copy2(path,w/'instance.json')
 # Executable and Makefile are outside the contest cwd; only instance/solution data exist there.
 (w/'solution').symlink_to(b/'solution');shutil.copy2(d/'Makefile',w/'Makefile')
 begin=time.monotonic();settings=dict(os.environ,TL='2');settings.pop('DBG',None);settings.pop('DBG2',None)
 with (b/(name+'.stdout')).open('w')as out,(b/(name+'.stderr')).open('w')as err:p=subprocess.run(['taskset','-c','14,15','make','run'],cwd=w,env=settings,stdout=out,stderr=err,timeout=6)
 wall=time.monotonic()-begin;value=validate(w/'instance.json',w/'solution.json');rows.append(dict(case=name,rc=p.returncode,wall=wall,official=value,valid=isinstance(value,(int,float)),data_files=[x.name for x in w.iterdir()if x.name not in ['solution','Makefile']]))
 assert p.returncode==0 and isinstance(value,(int,float)),rows[-1]
record=dict(source_sha256=sha(source),measured_binary_sha256=sha(binary),rebuilt_binary_sha256=sha(b/'solution'),zip_sha256=sha(archive),byte_identical=True,configuration=env,tests=rows,contract='make build/make run, no solver arguments, instance.json and solution.json; executable/Makefile are build files, no other runtime data')
(R/'PACKAGE_CHECK_FINAL.json').write_text(json.dumps(record,indent=2));print(json.dumps(record),flush=True)
