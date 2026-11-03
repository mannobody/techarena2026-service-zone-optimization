#!/usr/bin/env python3
# Fixed checkpoints, equal operator wall budgets, independent validation.
import sys,os,json,subprocess,time,re,hashlib,fcntl,queue,signal
from pathlib import Path

# Serialize an observation copy without altering commands or subprocess env.
import sys as _report_sys
_REPORT_ROOT = next(p for p in Path(__file__).resolve().parents
                    if (p / 'tools/public_metadata.py').is_file())
_report_sys.path.insert(0, str(_REPORT_ROOT / 'tools'))
from public_metadata import public_json as _public_json
def report_json(value, **kwargs):
    return _public_json(value, _REPORT_ROOT, **kwargs)

from concurrent.futures import ThreadPoolExecutor,as_completed
R=Path(__file__).resolve().parent;ROOT=R.parents[1];sys.path.insert(0,str(ROOT/'task'))
from validate_solution import validate
source=R/'logs'/sys.argv[1];tag=sys.argv[2];seconds=float(sys.argv[3]);dest=R/'logs'/tag;dest.mkdir(exist_ok=False)
spec=json.loads((source/'MANIFEST.json').read_text())['spec'];exe=R/'artifacts/post_boundary'
checkpoints={c:source/f'{c}_301_base.solution.json' for c in spec['cases']}
checkpoints={c:p for c,p in checkpoints.items() if p.exists()}
manifest={'operator_seconds':seconds,'input_source':str(source),'seeds':[701,702,703],'modes':{'0':'polish','1':'exchange1','2':'exchange2','3':'ILS','4':'VNS','5':'TS','6':'GWW','7':'balanced cycle','8':'boundary baseline','9':'cycle then boundary, same total budget'},'checkpoints':{k:hashlib.sha256(v.read_bytes()).hexdigest() for k,v in checkpoints.items()},'exe_sha256':hashlib.sha256(exe.read_bytes()).hexdigest()}
(dest/'MANIFEST.json').write_text(report_json(manifest,indent=2))
slots=queue.Queue();cpus=sorted(os.sched_getaffinity(0))[0:8:2]
for c in cpus[:4]:slots.put(c)
def run(case,mode,seed):
 cpu=slots.get();lock=(R/f'post_cpu_{cpu}.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX)
 name=f'{case}_{seed}_{mode}';prefix=dest/name;out=prefix.with_suffix('.solution.json');err=prefix.with_suffix('.stderr');inp=ROOT/spec['cases'][case];start=time.monotonic();rc=None
 try:
  with err.open('w') as f:
   p=subprocess.Popen(['taskset','-c',str(cpu),str(exe),str(inp),str(checkpoints[case]),str(out),str(seconds),str(mode),str(seed)],stderr=f,stdout=subprocess.DEVNULL,start_new_session=True,env={'PATH':os.environ['PATH'],'NT':'1','SEED':str(seed)})
   try:rc=p.wait(timeout=seconds+10)
   except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
  wall=time.monotonic()-start;val=validate(inp,out);initial=validate(inp,checkpoints[case]);valid=not isinstance(val,str)
  row={'case':case,'mode':mode,'seed':seed,'initial':initial,'objective':val if valid else None,'gain':val-initial if valid else None,'wall':wall,'rc':rc,'valid':valid,'success':rc==0 and valid and wall<=seconds+3}
  prefix.with_suffix('.json').write_text(report_json(row,indent=2));return row
 finally:fcntl.flock(lock,fcntl.LOCK_UN);lock.close();slots.put(cpu)
rows=[]
with ThreadPoolExecutor(max_workers=min(4,len(cpus))) as pool:
 fs=[pool.submit(run,c,m,s) for c in checkpoints for m in [8,9] for s in [701,702,703]]
 for f in as_completed(fs):
  rows.append(f.result());(dest/'results.json').write_text(report_json(rows,indent=2))
print('completed',len(rows),'success',sum(x['success'] for x in rows),flush=True)
