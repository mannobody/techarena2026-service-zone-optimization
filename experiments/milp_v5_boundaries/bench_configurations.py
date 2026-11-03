from pathlib import Path
import json,sys,time,subprocess,os,argparse
from concurrent.futures import ThreadPoolExecutor,as_completed
H=Path(__file__).resolve().parent
if len(sys.argv)>1 and sys.argv[1]=='child':
 from configurations import *
 _,_,tag,case,mode,inp,inc=sys.argv;I=Instance.read(inp);sol=json.loads(Path(inc).read_text());r=run(I,sol,seconds=54,checkpoint=H/'logs'/tag/f'{case}_{mode}.checkpoint.json');(H/'logs'/tag/f'{case}_{mode}.json').write_text(json.dumps(r,indent=2));sys.exit()
p=argparse.ArgumentParser();p.add_argument('--tag',required=True);p.add_argument('--modes',default='pair,power,both');p.add_argument('--cases',default='alphabig0,tightA0,large0,huge0,latent0');p.add_argument('--jobs',type=int,default=4);a=p.parse_args();D=H/'logs'/a.tag;D.mkdir()
rr=json.loads((H.parent/'milp_v5/logs/lazy_holdout60/results.json').read_text())['results'];items=[r for r in rr if r['variant']=='candidate' and r['seed']==161 and (not a.cases or r['case'] in a.cases.split(','))]
def run(job):
 r,mode=job;stem=f'{r["case"]}_{mode}';dest=D/(stem+'.checkpoint.json');dest.write_text(json.dumps(dict(solution=json.loads(Path(r['solution']).read_text()),value=r['score'],before=r['score'],status='initial')));start=time.perf_counter();hard=False
 try:
  q=subprocess.run([sys.executable,__file__,'child',a.tag,r['case'],mode,r['input'],r['solution']],capture_output=True,text=True,timeout=60,env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1'));(D/(stem+'.stderr')).write_text(q.stderr);assert q.returncode==0,q.stderr;out=json.loads((D/(stem+'.json')).read_text())
 except subprocess.TimeoutExpired:out=json.loads(dest.read_text());hard=True
 wall=time.perf_counter()-start
 from regions import Instance,value
 score=value(Instance.read(r['input']),out['solution']);assert not isinstance(score,str),score
 return dict(**{k:v for k,v in out.items() if k!='solution'},case=r['case'],input=r['input'],incumbent=r['solution'],mode=mode,wall=wall,hard_timeout=hard,valid=True)
rows=[]
with ThreadPoolExecutor(a.jobs) as ex:
 for f in as_completed([ex.submit(run,(r,m)) for r in items for m in a.modes.split(',')]):
  r=f.result();rows.append(r);(D/'results.json').write_text(json.dumps(rows,indent=2));print(r['case'],r['mode'],r['value']-r['before'],r.get('seconds'),r['status'],flush=True)
