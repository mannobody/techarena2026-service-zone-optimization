from pathlib import Path
import sys,json,subprocess,os,hashlib
from concurrent.futures import ThreadPoolExecutor,as_completed
H=Path(__file__).resolve().parent;E=H.parent/'evolution'
if len(sys.argv)>1:
 sys.path.insert(0,str(E));import local_mip as M
 from anchor_support import support
 case,variant=sys.argv[1:];I=M.Instance.read(H/'data/holdout'/f'{case}.json');inc=json.loads((H/'logs/index_holdout60'/f'{case}_61_base.json').read_text());opened=[r['officeId'] for r in inc]
 from itertools import combinations
 pairs=list(combinations(opened,2)) if len(opened)>1 else [(opened[0],o) for o in range(I.m) if o!=opened[0]]
 pair=min(pairs,key=lambda p:sum((I.xy[I.n+p[0]]-I.xy[I.n+p[1]])**2))
 old_support=M.support
 fn=support if variant=='anchor' else (lambda I,o,sites,p:support(I,o,old_support(I,o,sites,p),p)) if variant=='shrink' else old_support;counts={}
 def counted(*args):
  w=fn(*args);counts[len(w)]=counts.get(len(w),0)+1;return w
 M.support=counted
 r=M.improve(I,inc,pair,seconds=60.,radius=16);r.update(case=case,variant=variant,before=M.objective(I,inc),support_sizes=counts,limit=60,threads=1,radius=16)
 dest=H/'logs/anchor_holdout60'/f'{case}_{variant}.json';dest.write_text(json.dumps(r,indent=2));print(json.dumps({k:v for k,v in r.items() if k!='solution'}));sys.exit()
D=H/'logs/anchor_holdout60';D.mkdir();rows=[]
for p in [E/'local_mip.py',H.parent/'colgen/pricing.py',H/'anchor_support.py']:(D/(p.name+'.snapshot')).write_bytes(p.read_bytes())
def run(job):
 case,var=job;pr=subprocess.run([sys.executable,__file__,case,var],text=True,capture_output=True,timeout=75,env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1'));(D/f'{case}_{var}.stdout').write_text(pr.stdout);(D/f'{case}_{var}.stderr').write_text(pr.stderr)
 if pr.returncode:return dict(case=case,variant=var,error=pr.stderr,rc=pr.returncode)
 r=json.loads((D/f'{case}_{var}.json').read_text());return {k:v for k,v in r.items() if k!='solution'}
with ThreadPoolExecutor(3) as ex:
 for f in as_completed([ex.submit(run,(case,var)) for case in ['anti0','latent1','multiskill0'] for var in ['old','anchor']]):
  r=f.result();rows.append(r);print(json.dumps(r),flush=True);(D/'results.json').write_text(json.dumps(rows,indent=2))
