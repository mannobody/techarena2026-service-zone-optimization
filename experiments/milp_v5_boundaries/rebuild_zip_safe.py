from pathlib import Path
import zipfile,json,hashlib,subprocess,os,time,shutil
from regions import Instance,value
H=Path(__file__).resolve().parent;z=H/'artifacts/case03_cpp_server_v5_2_regions_safe_experimental_O3.zip';source=H/'artifacts/package_safe';preg=json.loads((H/'SAFE_PREREGISTRATION.json').read_text());assert hashlib.sha256((source/'main.cpp').read_bytes()).hexdigest()==preg['sha256']
with zipfile.ZipFile(z,'x',compression=zipfile.ZIP_DEFLATED) as f:
 for n in ['main.cpp','Makefile']:f.write(source/n,n)
d=H/'artifacts/zip_safe_rebuild';d.mkdir()
with zipfile.ZipFile(z) as f:f.extractall(d)
q=subprocess.run(['make','build'],cwd=d,capture_output=True,text=True);(H/'logs/zip_safe_build.stdout').write_text(q.stdout);(H/'logs/zip_safe_build.stderr').write_text(q.stderr);assert q.returncode==0,q.stderr
inp=H.parent/'geometry_islands/data/validation2/alphabig0.json';shutil.copyfile(inp,d/'instance.json');t=time.monotonic();q=subprocess.run([str(d/'solution')],cwd=d,env=dict(os.environ,TL='60',NT='2',SEED='155',DBG='1',MIP='1',MIP_MODE='2',MIP_RESERVE='0',LD_LIBRARY_PATH='/tmp/ta-boundary-venv/lib64/python3.14/site-packages/highspy'),capture_output=True,text=True,timeout=63);wall=time.monotonic()-t;(H/'logs/zip_safe_smoke.stderr').write_text(q.stderr);assert q.returncode==0,q.stderr;score=value(Instance.read(inp),json.loads((d/'solution.json').read_text()));assert not isinstance(score,str),score
(H/'logs/zip_safe_check.json').write_text(json.dumps(dict(zip=str(z),sha256=hashlib.sha256(z.read_bytes()).hexdigest(),source_sha256=preg['sha256'],compiled_from_zip=True,valid=True,value=score,seconds=60,threads=2,seed=155,wall=wall,mip_called='v5_mip' in q.stderr,region_called='v52_mip' in q.stderr),indent=2));print(score,wall,flush=True)
