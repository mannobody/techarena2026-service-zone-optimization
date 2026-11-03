"""No-argument, two-file runtime contract and official synthetic validation."""
import fcntl,hashlib,json,os,signal,subprocess,sys,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
sys.path.insert(0,str(ROOT/'task'));from validate_solution import validate
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
spec=json.loads(Path(sys.argv[1]).read_text());dest=ROOT/spec['destination'];dest.mkdir(parents=True,exist_ok=False)
os.sched_setaffinity(0,set(spec['cpu']));locks=[]
for cpu in sorted(spec['cpu']):
 f=open(f'/tmp/szo-perturbation-cpu{cpu}.lock','w');fcntl.flock(f,fcntl.LOCK_EX);locks.append(f)
source=ROOT/spec['source'];binary=ROOT/spec['binary'];cases=sorted((ROOT/'experiments/server_v6/logs/package_check').glob('*/instance.json'))
manifest={'spec':spec,'source_sha256':sha(source),'binary_sha256':sha(binary),'inputs':{p.parent.name:sha(p) for p in cases},'runner_sha256':sha(Path(__file__)),'note':'Known compatibility data, not independent quality holdout'}
(dest/'MANIFEST.json').write_text(json.dumps(manifest,indent=2));rows=[]
env={k:v for k,v in os.environ.items() if k in ['HOME','PATH','LANG','LD_LIBRARY_PATH']};env|=spec['env'];env|={'NT':'2','TL':str(spec['seconds']),'SEED':'2401','DBG':'1'}
for p in cases:
 name=p.parent.name;cwd=dest/name;cwd.mkdir();inp=cwd/'instance.json';inp.write_bytes(p.read_bytes());err=dest/f'{name}.stderr';res=dest/f'{name}.resource'
 start=time.monotonic();started=time.time();timeout=False
 with err.open('w') as f:
  child=subprocess.Popen(['/usr/bin/time','-f','rss_kb=%M user=%U sys=%S','-o',str(res),str(binary)],cwd=cwd,env=env,stderr=f,stdout=subprocess.DEVNULL,start_new_session=True)
  try:rc=child.wait(timeout=spec['seconds']+10)
  except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);rc=child.wait();timeout=True
 wall=time.monotonic()-start;ended=time.time();out=cwd/'solution.json'
 try:value=validate(inp,out)
 except Exception as ex:value=str(ex)
 valid=not isinstance(value,str);files=sorted(x.name for x in cwd.iterdir())
 ok=valid and rc==0 and not timeout and wall<=spec['seconds']+3 and files==['instance.json','solution.json']
 row={'case':name,'rc':rc,'timeout':timeout,'wall':wall,'started_unix':started,'ended_unix':ended,'affinity':spec['cpu'],'valid':valid,'objective_or_error':value,'resource':res.read_text(),'files':files,'success':ok,'input_sha256':sha(inp),'solution_sha256':sha(out) if out.exists() else None}
 rows.append(row);(dest/'results.json').write_text(json.dumps(rows,indent=2));print(name,ok,flush=True)
(dest/'COMPLETE.json').write_text(json.dumps({'expected':len(cases),'completed':len(rows),'success':sum(r['success'] for r in rows)},indent=2))
