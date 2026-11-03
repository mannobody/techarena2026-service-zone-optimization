from regions import *
import subprocess,os,argparse,json
from concurrent.futures import ThreadPoolExecutor,as_completed
p=argparse.ArgumentParser();p.add_argument('--tag',required=True);p.add_argument('--seconds',type=float,default=60);p.add_argument('--modes',default='fixed,joint');p.add_argument('--jobs',type=int,default=4);p.add_argument('--cases',default='');a=p.parse_args();D=H/'logs'/a.tag;D.mkdir()
rs=json.loads((H.parent/'milp_v5/logs/lazy_holdout60/results.json').read_text())['results'];items=[r for r in rs if r['variant']=='candidate' and r['seed']==161 and (not a.cases or r['case'] in a.cases.split(','))]
def run(job):
 r,mode=job;stem=f'{r["case"]}_{mode}';I=Instance.read(r['input']);inc=json.loads(Path(r['solution']).read_text());asg=[-1]*I.n;staff=[-1]*I.w
 for off in inc:
  for s in off['sites']:asg[s]=off['officeId']
  for w in off['workers']:staff[w]=off['officeId']
 ap=D/(stem+'.asg');wp=D/(stem+'.staff');out=D/(stem+'.json');ap.write_text(' '.join(map(str,asg)));wp.write_text(' '.join(map(str,staff)));env=dict(os.environ,REGION_JOINT=str(int(mode=='joint')),REGION_MODE='0',LD_LIBRARY_PATH='/tmp/ta-boundary-venv/lib64/python3.14/site-packages/highspy');start=time.perf_counter()
 q=subprocess.run([str(H/'artifacts/post'),r['input'],str(out),str(ap),str(a.seconds),str(wp)],capture_output=True,text=True,timeout=60 if a.seconds<60 else 65,env=env);wall=time.perf_counter()-start;(D/(stem+'.stderr')).write_text(q.stderr);assert q.returncode==0,q.stderr;score=value(I,json.loads(out.read_text()));assert not isinstance(score,str),score
 stats=json.loads(q.stderr.strip().splitlines()[-1]);assert abs(stats['before']-r['score'])<1e-6*max(1,abs(r['score']))
 return dict(case=r['case'],input=r['input'],incumbent=r['solution'],mode=mode,seconds=a.seconds,wall=wall,stats=stats,value=score,before=r['score'],valid=True,solution=str(out))
rows=[]
with ThreadPoolExecutor(a.jobs) as ex:
 for f in as_completed([ex.submit(run,(r,m)) for r in items for m in a.modes.split(',')]):
  r=f.result();rows.append(r);(D/'results.json').write_text(json.dumps(rows,indent=2));print(r['case'],r['mode'],r['value']-r['before'],r['wall'],flush=True)
