"""Generate only after immutable selection and local review release; then full primary."""
import json,hashlib,sys,time,subprocess,os
from pathlib import Path
R=Path(__file__).resolve().parents[1];ROOT=R.parents[1];sys.path.insert(0,str(ROOT/'tools'));import gen
os.sched_setaffinity(0,{14,15});sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
while not (R/'SELECTION_REVIEW_RELEASE.json').exists():time.sleep(1)
release=json.loads((R/'SELECTION_REVIEW_RELEASE.json').read_text());assert release['action']=='accept'and release['freeze_sha256']==sha(R/'FREEZE.json')
freeze=json.loads((R/'FREEZE.json').read_text())
for p,h in freeze['files'].items():assert sha(ROOT/p)==h,p
plan=json.loads((R/'INDEPENDENT_PLAN.json').read_text());assert sha(Path(gen.__file__))==plan['generator_sha256']
old=set()
for p in (ROOT/'experiments').rglob('*.json'):
 if 'inputs'in p.parts or p.name=='instance.json':old.add(sha(p))
for p in (ROOT/'task').glob('instance*/instance.json'):old.add(sha(p))
d=R/'inputs/fresh';d.mkdir(exist_ok=False);inputs={}
for i,(name,kw)in enumerate(plan['parameters']):
 p=d/(name+'.json');seed=plan['seed_offset']+i;gen.gen2(seed,str(p),**kw);h=sha(p);assert h not in old
 inputs[name]=dict(path=str(p.relative_to(ROOT)),sha256=h,seed=seed,parameters=kw)
(R/'FRESH_INPUTS.json').write_text(json.dumps(dict(generated_unix=time.time(),freeze_unix=freeze['created_unix'],no_prior_hash_overlap=True,inputs=inputs),indent=2))
(R/'CONFIRMATION_STATUS.json').write_text(json.dumps(dict(stage='independent280',started_unix=time.time()),indent=2))
with (R/'logs/independent280_v4.output').open('x')as f:subprocess.run([sys.executable,str(R/'src/run_instrumented.py'),str(R/'INDEPENDENT280_V4.json')],cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,check=True)
subprocess.run([sys.executable,str(R/'src/analysis.py'),'independent280_v4'],cwd=ROOT,check=True)
for p,h in freeze['files'].items():assert sha(ROOT/p)==h,p
(R/'CONFIRMATION_STATUS.json').write_text(json.dumps(dict(stage='independent280_complete',ended_unix=time.time()),indent=2));print('independent280_v4 complete',flush=True)
