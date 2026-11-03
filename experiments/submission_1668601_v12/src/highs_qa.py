"""Optional original library branch, isolated from portable quality labels."""
from pathlib import Path
import os,time,subprocess,json,ctypes,sys,concurrent.futures,re,hashlib
R=Path(__file__).resolve().parents[1];ROOT=R.parents[1];sys.path.insert(0,str(ROOT/'task'));from validate_solution import validate
os.sched_setaffinity(0,{8,10,12,13});d=R/'logs/highs_qa';d.mkdir(exist_ok=False)
lib=ROOT/'experiments/v8_exact_neighborhoods/offline_deps/highspy/libhighs.so.1';api=ctypes.CDLL(str(lib));api.Highs_create.restype=ctypes.c_void_p;api.Highs_getSizeofHighsInt.argtypes=[ctypes.c_void_p];api.Highs_destroy.argtypes=[ctypes.c_void_p];h=api.Highs_create();size=api.Highs_getSizeofHighsInt(h);api.Highs_destroy(h);assert size==4,size
s=json.loads((R/'SCREEN20.json').read_text());pairs=[[8,10],[12,13]];jobs=list(s['variants'].items());rows=[]
def one(item):
 j,(label,cfg)=item;binary=ROOT/cfg['binary'];build=binary.parent/'BUILD.json'
 if label!='submission':
  while not build.exists():time.sleep(1)
  assert json.loads(build.read_text())['rc']==0
 local=[]
 for case in ['grid180','equal180']:
  inp=ROOT/'experiments/adaptive_v11/inputs/dev'/(case+'.json');out=d/(label+'_'+case+'.solution.json');err=out.with_suffix('.stderr');env=dict(PATH=os.environ['PATH'],NT='2',SEED='12601',DBG='1',LD_LIBRARY_PATH=str(lib.parent),**cfg.get('env',{}));cpu=pairs[j%2]
  with err.open('w')as f:p=subprocess.run(['taskset','-c',','.join(map(str,cpu)),str(binary),str(inp),str(out),'5'],cwd=ROOT,stderr=f,env=env,timeout=12)
  v=validate(inp,out);txt=err.read_text();x=dict(variant=label,case=case,rc=p.returncode,official=v,valid=isinstance(v,(int,float)),mip_events=re.findall(r'^v5(?:2)?_(?:regions|mip).*$',txt,re.M),errors=bool(re.search(r'error:|VERIFY|INVALID',txt)));assert x['valid']and x['rc']==0 and not x['errors'],x;local.append(x)
 return local
# Fixed two lanes, so concurrent checks never share their CPU pair.
with concurrent.futures.ThreadPoolExecutor(max_workers=2)as pool:
 for j in range(0,len(jobs),2):
  for local in pool.map(one,list(enumerate(jobs))[j:j+2]):rows+=local;(d/'results.json').write_text(json.dumps(rows,indent=2))
(R/'HIGHS_QA.json').write_text(json.dumps(dict(stage='complete',default_lookup_present=False,explicit_library=str(lib.relative_to(ROOT)),library_sha256=hashlib.sha256(lib.read_bytes()).hexdigest(),sizeof_HighsInt=size,runs=len(rows),valid=sum(x['valid']for x in rows),mip_exercised_variants=sorted({x['variant']for x in rows if x['mip_events']}),no_quality_claim=True),indent=2));print('HiGHS optional branch QA:',len(rows),flush=True)
