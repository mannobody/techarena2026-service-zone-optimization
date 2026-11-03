from pathlib import Path
import shutil,json,hashlib,zipfile,subprocess,os,time,importlib.util
from concurrent.futures import ThreadPoolExecutor
H=Path(__file__).resolve().parent;R=H.parents[1];D=H/'artifacts/package_robust';D.mkdir();shutil.copyfile(H/'artifacts/robust_v1.cpp',D/'main.cpp');(D/'Makefile').write_text('build:\n\tg++ -O3 -std=c++17 -o solution main.cpp\n\nrun:\n\t./solution\n')
subprocess.run(['make','build'],cwd=D,check=True)
p=H/'artifacts/geometry_exact_experimental_O3.zip'
with zipfile.ZipFile(p,'x',compression=zipfile.ZIP_DEFLATED) as z:
 for name in ['main.cpp','Makefile']:z.write(D/name,name)
with zipfile.ZipFile(p) as z:
 assert z.read('main.cpp')==(H/'artifacts/robust_v1.cpp').read_bytes()
manifest=dict(status='Experimental; pending independent full-time comparisons; not submitted',zip=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),source_sha256=hashlib.sha256((D/'main.cpp').read_bytes()).hexdigest(),flags='-O3 -std=c++17',default_seconds=280,confirmation_seconds=60,runtime='instance.json -> solution.json; standard C++ plus compiler unsigned __int128; no external libraries')
(H/'PACKAGE_MANIFEST.json').write_text(json.dumps(manifest,indent=2))
spec=importlib.util.spec_from_file_location('validator',R/'task/validate_solution.py');V=importlib.util.module_from_spec(spec);spec.loader.exec_module(V)
log=H/'logs/package60';log.mkdir()
def run(item):
 split,case=item;d=log/f'{split}_{case}';d.mkdir();inp=H/'data'/split/f'{case}.json';shutil.copyfile(inp,d/'instance.json');env=dict(os.environ,TL='60',NT='2',SEED='81')
 for k in ['GEO_INDEX','GEO_EXACT','BOUNDARY','B_RESERVE','WORKER_DFS','WARM_START']:env.pop(k,None)
 start=time.monotonic();pr=subprocess.run([str(D/'solution')],cwd=d,env=env,capture_output=True,text=True,timeout=90);wall=time.monotonic()-start;(d/'stderr.txt').write_text(pr.stderr);score=V.validate(d/'instance.json',d/'solution.json')
 return dict(case=case,split=split,input=str(inp),output=str(d/'solution.json'),score=score,rc=pr.returncode,wall=wall,seconds=60,threads=2,seed=81,error=score if isinstance(score,str) else None)
with ThreadPoolExecutor(2) as ex:rows=list(ex.map(run,[('precision','thin'),('precision','translated'),('validation2','alphabig0'),('validation2','multiskill0')]))
(log/'results.json').write_text(json.dumps(rows,indent=2));assert all(r['error'] is None and r['rc']==0 for r in rows);print(rows)
