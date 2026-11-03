from pathlib import Path
import sys,json,subprocess,time,os,argparse
from concurrent.futures import ThreadPoolExecutor,as_completed
H=Path(__file__).resolve().parent
if len(sys.argv)>1 and sys.argv[1]=='child':
 from grouped_flow import *
 _,_,tag,case,mode,inp,inc=sys.argv;r=improve(Instance.read(inp),json.loads(Path(inc).read_text()),58,mode,H/'logs'/tag/f'{case}_{mode}.checkpoint.json',fixed_open=True);(H/'logs'/tag/f'{case}_{mode}.json').write_text(json.dumps(r,indent=2));sys.exit()
p=argparse.ArgumentParser();p.add_argument('--tag',required=True);p.add_argument('--modes',default='assigned,territory,joint');p.add_argument('--jobs',type=int,default=4);a=p.parse_args();D=H/'logs'/a.tag;D.mkdir()
items=[dict(case='controlled_'+r['case'],input=r['input'],incumbent=r['incumbent']) for r in json.loads((H.parent/'dp_milp/data/controlled_manifest.json').read_text())]
items += [dict(case='ordinary_'+r['case'],input=r['input'],incumbent=r['solution']) for r in json.loads((H.parent/'server_v4/logs/package60/results.json').read_text()) if r['split']=='validation2']
def run(job):
 r,mode=job;stem=f'{r["case"]}_{mode}';dest=D/(stem+'.checkpoint.json');dest.write_text(json.dumps(dict(solution=json.loads(Path(r['incumbent']).read_text()),status='initial')));t=time.monotonic()
 try:
  q=subprocess.run([sys.executable,__file__,'child',a.tag,r['case'],mode,r['input'],r['incumbent']],capture_output=True,text=True,timeout=60,env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1'));(D/(stem+'.stderr')).write_text(q.stderr);assert q.returncode==0,q.stderr;out=json.loads((D/(stem+'.json')).read_text());hard=False
 except subprocess.TimeoutExpired:out=json.loads(dest.read_text());hard=True
 wall=time.monotonic()-t
 from grouped_flow import Instance,value
 I=Instance.read(r['input']);score=value(I,out['solution']);assert not isinstance(score,str),score
 return dict(**{k:v for k,v in out.items() if k not in ['solution','mode','value']},**r,mode=mode,value=score,hard_timeout=hard,process_wall=wall,valid=True)
rows=[]
with ThreadPoolExecutor(a.jobs) as ex:
 for f in as_completed([ex.submit(run,(r,m)) for r in items for m in a.modes.split(',')]):
  z=f.result();rows.append(z);(D/'results.json').write_text(json.dumps(rows,indent=2));print(json.dumps(z),flush=True)
