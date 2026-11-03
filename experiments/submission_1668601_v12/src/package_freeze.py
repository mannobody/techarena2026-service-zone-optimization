"""Package selected implementation, verify actual ZIP build, then immutable freeze."""
import json,os,time,hashlib,sys,subprocess,zipfile,shutil,math
from pathlib import Path
R=Path(__file__).resolve().parents[1];ROOT=R.parents[1];sys.path.insert(0,str(ROOT/'task'));from validate_solution import validate
os.sched_setaffinity(0,{14,15});sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads((R/p).read_text())
def save(p,x):(R/p).write_text(json.dumps(x,indent=2))
save('PACKAGE_STATUS.json',dict(stage='waiting_selected'))
while not(R/'SELECTED_FINAL.json').exists():time.sleep(1)
sel=read('SELECTED_FINAL.json');cfg=sel['selected']['configuration'];measured=ROOT/cfg['binary'];source=measured.parent/'main.cpp';p=R/'package';p.mkdir(exist_ok=False);shutil.copyfile(source,p/'main.cpp')
envflags=' '.join(k+'='+v for k,v in sorted(cfg.get('env',{}).items()))
(p/'Makefile').write_text('build:\n\tg++ -O3 -std=c++17 -o solution main.cpp -ldl\n\nrun:\n\tNT=2 '+envflags+' ./solution\n\n.PHONY: build run\n')
z=R/'candidate_final.zip'
with zipfile.ZipFile(z,'x',compression=zipfile.ZIP_DEFLATED)as a:
 for n in ['Makefile','main.cpp']:a.write(p/n,n)
rebuild=R/'artifacts/package_rebuild';rebuild.mkdir(exist_ok=False)
with zipfile.ZipFile(z)as a:a.extractall(rebuild)
save('PACKAGE_STATUS.json',dict(stage='rebuilding_actual_zip',selected=sel['selected']['variant']))
with(rebuild/'compile.log').open('w')as f:subprocess.run(['taskset','-c','14,15','make','build'],cwd=rebuild,stdout=f,stderr=subprocess.STDOUT,check=True)
exe=rebuild/'solution';assert sha(exe)==sha(measured),dict(measured=sha(measured),rebuilt=sha(exe))
# The actual ZIP build is byte-identical to the already tested finalist binary.
# Reuse its411 complete oracle checks, avoiding redundant executions of the same bytes.
old=ROOT/'experiments/adaptive_v11';scale=old/'logs/scale_qa_v4'
receipt_path=R/'logs'/('scale_'+sel['selected']['variant'])/'RECEIPT.json'
while not receipt_path.exists():time.sleep(1)
receipt=json.loads(receipt_path.read_text());assert receipt['binary_sha256']==sha(exe)
assert receipt['configuration']==cfg.get('env',{}) and receipt['cases']==411 and receipt['valid']==411 and receipt['matches']==411
save('SCALE_RECEIPT_REUSE.json',dict(receipt=str(receipt_path.relative_to(ROOT)),receipt_sha256=sha(receipt_path),binary_sha256=sha(exe),byte_identical_to_packaged=True,reason='Same executable bytes; actual ZIP build/file contract separately tested'))
contract=R/'logs/package_contract';contract.mkdir(exist_ok=False);tests=[]
inputs=[('jury4',ROOT/'task/instance4/instance.json'),('grid',ROOT/'experiments/adaptive_v11/inputs/dev/grid180.json'),('huge',ROOT/'experiments/adaptive_v11/inputs/dev/huge10000.json'),('line',old/'inputs/line_mechanism/line9.json'),('micro',scale/'micro.json')]
for name,inp in inputs:
 wd=contract/name;wd.mkdir();shutil.copyfile(exe,wd/'solution');(wd/'solution').chmod(0o755);shutil.copyfile(p/'Makefile',wd/'Makefile');shutil.copyfile(inp,wd/'instance.json');begin=time.monotonic()
 with(contract/(name+'.stderr')).open('w')as f:q=subprocess.run(['taskset','-c','14,15','make','run'],cwd=wd,env=dict(PATH=os.environ['PATH'],TL='2'),stdout=f,stderr=subprocess.STDOUT,timeout=8)
 wall=time.monotonic()-begin;v=validate(wd/'instance.json',wd/'solution.json');data=sorted(x.name for x in wd.glob('*.json'));row=dict(case=name,rc=q.returncode,wall=wall,official=v,valid=isinstance(v,(int,float)),data_files=data);tests.append(row);assert q.returncode==0 and row['valid']and data==['instance.json','solution.json'],row
check=dict(selected=sel['selected']['variant'],configuration=cfg.get('env',{}),source_sha256=sha(p/'main.cpp'),measured_binary_sha256=sha(measured),rebuilt_binary_sha256=sha(exe),zip_sha256=sha(z),byte_identical=True,scale_tests=411,scale_valid=411,tests=tests,default_seconds=280,default_compute_cpus=2,contract='make build/make run; instance.json→solution.json, build files aside, no extra runtime data or answer starts')
save('PACKAGE_CHECK.json',check);assert not(R/'inputs/fresh').exists()
s=read('DEVELOPMENT280.json');s['name']='independent280';s['seconds']=280;s['seeds']=read('FRESH_PLAN.json')['seeds'];s['cases']={n:str((R/'inputs/fresh'/(n+'.json')).relative_to(ROOT))for n,_ in read('FRESH_PLAN.json')['parameters']};s['variants']={'submission':s['variants']['submission'],'candidate':dict(binary=str(exe.relative_to(ROOT)),env=cfg.get('env',{}))};save('INDEPENDENT280.json',s)
files=[R/'baseline/original.zip',R/'baseline/main.cpp',R/'baseline/Makefile',R/'baseline/solution',source,measured,exe,p/'main.cpp',p/'Makefile',z,R/'PACKAGE_CHECK.json',R/'SCALE_RECEIPT_REUSE.json',receipt_path,R/'SELECTED_FINAL.json',R/'PROTOCOL.json',R/'GEOMETRY_LONG_ADDENDUM.json',R/'FRESH_PLAN.json',R/'INDEPENDENT280.json',ROOT/'tools/gen.py',ROOT/'task/validate_solution.py',ROOT/'experiments/v4_local_search/baseline/frozen_v4.cpp']
files +=[R/'src'/n for n in ['compose.py','certified.h','run.py','analyze.py','fresh.py','package_freeze.py']]
save('FREEZE.json',dict(created_unix=time.time(),files={str(x.relative_to(ROOT)):sha(x)for x in files},note='No code/config/input-design tuning after unseen generation. Reporting helpers may be added.'))
save('PACKAGE_STATUS.json',dict(stage='frozen_await_local_review',freeze_sha256=sha(R/'FREEZE.json')));print('package frozen',sel['selected']['variant'],flush=True)
subprocess.run([sys.executable,str(R/'src/fresh.py')],cwd=ROOT,check=True)
