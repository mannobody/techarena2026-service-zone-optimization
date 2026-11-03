from pathlib import Path
import sys,json,subprocess,time,os,argparse
from concurrent.futures import ThreadPoolExecutor,as_completed
H=Path(__file__).resolve().parent
if len(sys.argv)>1 and sys.argv[1]=='child':
 from envelopes import expand
 from grouped_flow import Instance,improve
 _,_,tag,case,variant,inp,inc=sys.argv;I=Instance.read(inp);sol=json.loads(Path(inc).read_text());pool,stats=expand(I,sol,seconds=3,open_new=variant=='new');r=improve(I,sol,seconds=55-stats['expand_seconds'],mode='joint',checkpoint=H/'logs'/tag/f'{case}_{variant}.checkpoint.json',pools=pool,fixed_open=True);r.update(stats);(H/'logs'/tag/f'{case}_{variant}.json').write_text(json.dumps(r,indent=2));sys.exit()
p=argparse.ArgumentParser();p.add_argument('--tag',required=True);p.add_argument('--jobs',type=int,default=4);p.add_argument('--source',default='ordinary');a=p.parse_args();D=H/'logs'/a.tag;D.mkdir()
if a.source=='ordinary':items=[dict(case=r['case'],input=r['input'],incumbent=r['solution']) for r in json.loads((H.parent/'server_v4/logs/package60/results.json').read_text()) if r['split']=='validation2']
else:items=[dict(case=r['case'],input=r['input'],incumbent=r['solution']) for r in json.loads((H.parent/'dp_milp/logs/full_holdout60/results.json').read_text())['results'] if r['variant']=='base' and r['seed']==111]
def run(job):
 r,variant=job;stem=f'{r["case"]}_{variant}';dest=D/(stem+'.checkpoint.json');dest.write_text(json.dumps(dict(solution=json.loads(Path(r['incumbent']).read_text()),status='initial')));t=time.monotonic()
 try:
  q=subprocess.run([sys.executable,__file__,'child',a.tag,r['case'],variant,r['input'],r['incumbent']],capture_output=True,text=True,timeout=60,env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1'));(D/(stem+'.stderr')).write_text(q.stderr);assert q.returncode==0,q.stderr;out=json.loads((D/(stem+'.json')).read_text());hard=False
 except subprocess.TimeoutExpired:out=json.loads(dest.read_text());hard=True
 wall=time.monotonic()-t
 from grouped import Instance,value
 I=Instance.read(r['input']);score=value(I,out['solution']);assert not isinstance(score,str),score
 return dict(**{k:v for k,v in out.items() if k not in ['solution','value']},**r,variant=variant,value=score,hard_timeout=hard,process_wall=wall,valid=True)
rows=[]
with ThreadPoolExecutor(a.jobs) as ex:
 for f in as_completed([ex.submit(run,(r,v)) for r in items for v in ['grow','new']]):
  z=f.result();rows.append(z);(D/'results.json').write_text(json.dumps(rows,indent=2));print(json.dumps(z),flush=True)
