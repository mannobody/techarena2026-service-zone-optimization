"""Research-only scheduling diagnosis on held-out controller cores, not quality evidence."""
import collections,hashlib,json,os,resource,subprocess,sys,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];ROOT=R.parents[1];sys.path.insert(0,str(ROOT/'task'))
from validate_solution import validate
sys.path.insert(0,str(ROOT/'tools'))
from public_metadata import public_json
def report_json(value, **kwargs):
    return public_json(value, ROOT, **kwargs)
os.sched_setaffinity(0,{14,15});d=R/'logs/cpu_profile20';d.mkdir(exist_ok=False)
inp=ROOT/'experiments/structural_v9/inputs/dev/huge.json';rows=[]
for label,binary in [('v9','experiments/structural_v9/artifacts/final_research/candidate'),('geometry','experiments/warm_v10/artifacts/v5/candidate')]:
 out=d/(label+'.solution.json');env={'PATH':os.environ['PATH'],'NT':'2','SEED':'10302','ZM_POOL':'0','ZM_RESERVE':'0','GW_MODE':'1','DBG':'1'}
 cmd=['taskset','-c','14,15',str(ROOT/binary),str(inp),str(out),'20'];before=resource.getrusage(resource.RUSAGE_CHILDREN);start=time.monotonic();samples=[]
 with (d/(label+'.stderr')).open('x')as f:
  p=subprocess.Popen(cmd,env=env,stderr=f)
  while p.poll()is None:
   threads=[]
   try:
    for q in Path(f'/proc/{p.pid}/task').iterdir():
     stat=q.joinpath('stat').read_text().split(') ')[1].split();sched=q.joinpath('schedstat').read_text().split();wchan=q.joinpath('wchan').read_text().strip()
     threads.append(dict(tid=int(q.name),state=stat[0],cpu_ticks=int(stat[11])+int(stat[12]),runtime_ns=int(sched[0]),runqueue_ns=int(sched[1]),slices=int(sched[2]),wchan=wchan))
   except (FileNotFoundError,ProcessLookupError):pass
   samples.append(dict(wall=time.monotonic()-start,threads=threads));time.sleep(.1)
  rc=p.wait()
 wall=time.monotonic()-start;after=resource.getrusage(resource.RUSAGE_CHILDREN);cpu=after.ru_utime+after.ru_stime-before.ru_utime-before.ru_stime
 latest={}
 for s in samples:
  for t in s['threads']:latest[t['tid']]=t
 states=collections.Counter(t['state']for s in samples for t in s['threads']);waits=collections.Counter(t['wchan']for s in samples for t in s['threads'])
 v=validate(inp,out);rows.append(dict(label=label,command=cmd,env=env,wall=wall,cpu=cpu,cpu_ratio=cpu/wall,rc=rc,official=v,valid=isinstance(v,(int,float)),states=dict(states),waits=dict(waits),threads_last=latest,samples=samples,binary_sha256=hashlib.sha256((ROOT/binary).read_bytes()).hexdigest()))
 (d/(label+'.json')).write_text(report_json(rows[-1],indent=2));print(report_json({k:v for k,v in rows[-1].items()if k not in ['samples','threads_last','env','command']}),flush=True)
(d/'results.json').write_text(report_json(rows,indent=2))
