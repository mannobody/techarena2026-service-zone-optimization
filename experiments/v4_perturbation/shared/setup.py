"""Create immutable development data and freeze the exact comparator; no old writes."""
import hashlib,json,os,subprocess,sys,time,zipfile
from pathlib import Path

# Serialize an observation copy without altering commands or subprocess env.
import sys as _report_sys
_REPORT_ROOT = next(p for p in Path(__file__).resolve().parents
                    if (p / 'tools/public_metadata.py').is_file())
_report_sys.path.insert(0, str(_REPORT_ROOT / 'tools'))
from public_metadata import public_json as _public_json
def report_json(value, **kwargs):
    return _public_json(value, _REPORT_ROOT, **kwargs)

R=Path(__file__).resolve().parents[1]; ROOT=R.parents[1]
if (R/'INITIAL_STATUS.json').exists():
    raise SystemExit('This round is already initialized; refusing to overwrite provenance or data.')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v): p.write_text(report_json(v,indent=2))
sys.path.insert(0,str(ROOT/'tools')); import gen
os.sched_setaffinity(0,{20,21})
# Preserve an audit of all pre-existing user files (git internals are read-only).
files={str(p.relative_to(ROOT)):sha(p) for p in ROOT.rglob('*') if p.is_file() and '.git' not in p.parts and '.venv' not in p.parts and R not in p.parents}
dump(R/'PREEXISTING_HASHES.json',files)
dump(R/'INITIAL_STATUS.json',{'time':time.time(),'status':subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True),'files':len(files)})
src=ROOT/'experiments/v4_local_search/baseline/frozen_v4.cpp'
assert sha(src)=='5b3914fa9791cb879f3232fb2876a915de83b848ad4b353b0dbf25b574998c25'
target=R/'baseline/frozen_v4.cpp'; target.write_bytes(src.read_bytes())
cmd=['g++','-O3','-std=c++17','-pthread',str(target),'-o',str(R/'baseline/v4')]
p=subprocess.run(cmd,capture_output=True); (R/'baseline/build.stderr').write_bytes(p.stderr); p.check_returncode()
z=ROOT/'experiments/server_v4/artifacts/case03_cpp_server_v4_O3.zip'
with zipfile.ZipFile(z) as f: payload=f.read('main.cpp')
assert payload==src.read_bytes()
dump(R/'baseline/PROVENANCE.json',{'time':time.time(),'original':str(src.relative_to(ROOT)),'source_sha256':sha(target),'binary_sha256':sha(R/'baseline/v4'),'zip':str(z.relative_to(ROOT)),'zip_sha256':sha(z),'zip_payload_exact':True,'command':cmd,'compiler':subprocess.check_output(['g++','--version'],text=True)})
classes=['anti','tightA','alphabig','multiskill','cluster','grid','large','huge','deficit','alphazero','elongated','negative']
records={}; d=R/'shared/inputs/dev'; d.mkdir(parents=True,exist_ok=False)
for j,name in enumerate(classes):
    seed=851000+100*j
    import random
    base=name if name in gen.SUITE else 'medium'
    params=gen.SUITE[base][1](random.Random(seed))
    if name=='tightA': params['A']=0
    if name=='large': params['ns']=3500
    if name=='huge': params['ns']=10000
    if name=='negative': params.update(A=10000,dist='road')
    path=d/f'{name}.json'; gen.gen2(seed,str(path),**params)
    data=json.loads(path.read_text()); transforms=[]
    if name=='elongated':
        for x in data['sites']+data['offices']: x['y']*=.005
        transforms.append('y *= .005; original distances retained (coordinate/road mismatch)')
    if name=='negative':
        for k,x in enumerate(data['sites']):
            if k%3==0: x['reward']*=.03
        transforms.append('every third reward *= .03; A=10000')
    path.write_text(json.dumps(data,separators=(',',':')))
    records[name]={'path':str(path.relative_to(ROOT)),'generator_seed':seed,'parameters':params,'transforms':transforms,'sha256':sha(path)}
dump(R/'shared/DEV_INPUTS.json',records)
pairs=[[0,1],[3,6],[8,10],[16,17],[18,19],[20,21]]
for name,seconds,cases,seed in [('checkpoint60',60,classes,1901),('checkpoint280',280,classes[:5]+['huge'],1902)]:
    spec={'destination':str((R/'shared/logs'/name).relative_to(ROOT)),'seconds':seconds,'cpu_pairs':pairs,'seeds':[seed],'cases':{k:records[k]['path'] for k in cases},'variants':{'v4':{'binary':str((R/'baseline/v4').relative_to(ROOT)),'source':str(target.relative_to(ROOT)),'env':{'DBG':'1'}}},'snapshots':[10,30,50] if seconds==60 else [60,120,200,260]}
    dump(R/'shared'/f'{name.upper()}.json',spec)
print('BASELINE and DEVELOPMENT READY',flush=True)
