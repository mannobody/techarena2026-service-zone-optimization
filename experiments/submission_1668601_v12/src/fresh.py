"""Generate after an immutable reviewed choice, then independent paired TL280."""
import sys,os,time,json,hashlib,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];ROOT=R.parents[1];sys.path.insert(0,str(ROOT/'tools'));import gen
os.sched_setaffinity(0,{14,15});sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
while not(R/'LOCAL_REVIEW_RELEASE.json').exists():time.sleep(1)
a=json.loads((R/'LOCAL_REVIEW_RELEASE.json').read_text());assert a['action']=='accept'and a['freeze_sha256']==sha(R/'FREEZE.json');f=json.loads((R/'FREEZE.json').read_text())
for p,h in f['files'].items():assert sha(ROOT/p)==h,p
plan=json.loads((R/'FRESH_PLAN.json').read_text());assert sha(Path(gen.__file__))==plan['generator_sha256'];old=set()
for p in ROOT.rglob('*.json'):
 if 'inputs'in p.parts or p.name=='instance.json'or p.name.endswith('.input.json'):old.add(sha(p))
d=R/'inputs/fresh';d.mkdir(parents=True,exist_ok=False);inputs={}
for i,(name,kw)in enumerate(plan['parameters']):
 p=d/(name+'.json');seed=plan['seed_offset']+i;gen.gen2(seed,str(p),**kw);h=sha(p);assert h not in old
 inputs[name]=dict(path=str(p.relative_to(ROOT)),sha256=h,generator_seed=seed,parameters=kw)
(R/'FRESH_INPUTS.json').write_text(json.dumps(dict(generated_unix=time.time(),freeze_unix=f['created_unix'],prior_distinct_input_hashes=len(old),no_prior_hash_overlap=True,inputs=inputs),indent=2))
(R/'CONFIRMATION_STATUS.json').write_text(json.dumps(dict(stage='independent280',started_unix=time.time()),indent=2))
with(R/'logs/independent280.output').open('x')as q:subprocess.run([sys.executable,str(R/'src/run.py'),str(R/'INDEPENDENT280.json')],cwd=ROOT,stdout=q,stderr=subprocess.STDOUT,check=True)
subprocess.run([sys.executable,str(R/'src/analyze.py'),'independent280'],cwd=ROOT,check=True)
for p,h in f['files'].items():assert sha(ROOT/p)==h,p
(R/'CONFIRMATION_STATUS.json').write_text(json.dumps(dict(stage='complete',ended_unix=time.time()),indent=2));print('independent280 complete',flush=True)
