import sys,os,json,subprocess,time,re,hashlib,queue,signal
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
R=Path(__file__).resolve().parent;ROOT=R.parents[2];sys.path.insert(0,str(ROOT/'task'))
from validate_solution import validate
source=R/'logs'/'baseline280';tag=sys.argv[1];seconds=float(sys.argv[2]);modes=list(map(int,sys.argv[3].split(',')));cases=sys.argv[4].split(',')
dest=R/'logs'/tag;dest.mkdir(exist_ok=False);spec=json.loads((source/'MANIFEST.json').read_text())['spec'];exe=R/'bin'/(sys.argv[5] if len(sys.argv)>5 else 'post_v3')
checkpoints={c:source/f'{c}_711_v4.solution.json' for c in cases}
for c in cases:assert json.loads((source/f'{c}_711_v4.json').read_text())['success']
manifest=dict(operator_seconds=seconds,input_source=str(source),seeds=[711,712],modes=modes,checkpoints={k:hashlib.sha256(v.read_bytes()).hexdigest() for k,v in checkpoints.items()},inputs={k:hashlib.sha256((ROOT/spec['cases'][k]).read_bytes()).hexdigest() for k in cases},exe_sha256=hashlib.sha256(exe.read_bytes()).hexdigest())
(dest/'MANIFEST.json').write_text(report_json(manifest,indent=2));slots=queue.Queue()
for c in [6,7]:slots.put(c)
def run(c,m,seed):
 cpu=slots.get();os.sched_setaffinity(0,{cpu});prefix=dest/f'{c}_{seed}_{m}';out=prefix.with_suffix('.solution.json');err=prefix.with_suffix('.stderr');res=prefix.with_suffix('.resource');inp=ROOT/spec['cases'][c];start=time.monotonic();rc=None;timeout=False
 try:
  with err.open('w') as f:
   p=subprocess.Popen(['/usr/bin/time','-f','rss_kb=%M user=%U sys=%S','-o',str(res),'taskset','-c',str(cpu),str(exe),str(inp),str(checkpoints[c]),str(out),str(seconds),str(m),str(seed)],stderr=f,stdout=subprocess.DEVNULL,start_new_session=True,env={'PATH':os.environ['PATH'],'NT':'1'})
   try:rc=p.wait(timeout=seconds+10)
   except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait();timeout=True
  wall=time.monotonic()-start;v=validate(inp,out);initial=validate(inp,checkpoints[c]);valid=not isinstance(v,str)
  row=dict(case=c,mode=m,seed=seed,initial=initial,objective=v if valid else None,gain=v-initial if valid else None,wall=wall,rc=rc,timeout=timeout,valid=valid,validation_error=None if valid else v,success=rc==0 and valid and not timeout and wall<=seconds+3,affinity=[cpu],actual_nt=1,resource=res.read_text())
  prefix.with_suffix('.json').write_text(report_json(row,indent=2));return row
 finally:slots.put(cpu)
rows=[]
with ThreadPoolExecutor(max_workers=2) as pool:
 for f in as_completed([pool.submit(run,c,m,s) for c in cases for m in modes for s in [711,712]]):
  row=f.result();rows.append(row);(dest/'results.json').write_text(report_json(rows,indent=2));print(len(rows),row['case'],row['mode'],row['gain'],row['success'],flush=True)
