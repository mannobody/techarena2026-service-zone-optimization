from pathlib import Path
import json,os,time,subprocess,sys,argparse
from concurrent.futures import ThreadPoolExecutor,as_completed
from grouped import Instance,value
H=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--tag',required=True);p.add_argument('--modes',default='0,1,2');p.add_argument('--jobs',type=int,default=4);p.add_argument('--seconds',type=float,default=60);a=p.parse_args();D=H/'logs'/a.tag;D.mkdir()
items=[dict(case=r['case'],input=r['input'],incumbent=r['solution']) for r in json.loads((H.parent/'server_v4/logs/package60/results.json').read_text()) if r['split']=='validation2']
def run(job):
 r,mode=job;I=Instance.read(r['input']);inc=json.loads(Path(r['incumbent']).read_text());asg=[-1]*I.n
 for row in inc:
  for s in row['sites']:asg[s]=row['officeId']
 stem=r['case']+'_'+mode;ap=D/(stem+'.asg');ap.write_text(' '.join(map(str,asg)));out=D/(stem+'.json');env=dict(os.environ,NT='1',DBG='1',MIP_MODE=mode,LD_LIBRARY_PATH='/tmp/ta-boundary-venv/lib64/python3.14/site-packages/highspy');t=time.monotonic();q=subprocess.run([str(H/'artifacts/post_v1'),r['input'],str(out),str(ap),str(a.seconds),'1'],capture_output=True,text=True,env=env,timeout=a.seconds+3);wall=time.monotonic()-t;(D/(stem+'.stderr')).write_text(q.stderr);assert q.returncode==0,q.stderr;score=value(I,json.loads(out.read_text()));assert not isinstance(score,str),score;stats=json.loads(q.stderr.strip().splitlines()[-1]);assert stats['highs']==1
 return dict(**r,mode=mode,value=score,before=value(I,inc),stats=stats,wall=wall,valid=True,solution=str(out))
rows=[]
with ThreadPoolExecutor(a.jobs) as ex:
 for f in as_completed([ex.submit(run,(r,m)) for r in items for m in a.modes.split(',')]):
  r=f.result();rows.append(r);(D/'results.json').write_text(json.dumps(rows,indent=2));print(json.dumps(r),flush=True)
