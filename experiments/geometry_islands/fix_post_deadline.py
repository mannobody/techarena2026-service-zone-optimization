from pathlib import Path
import subprocess,json,hashlib
from concurrent.futures import ThreadPoolExecutor
H=Path(__file__).resolve().parent
old='end=start+atof(argv[3]);g_wdfs_deadline=end;'
new='end=start+atof(argv[3])-.25;g_wdfs_deadline=end+.23;'
def run(ver):
 p=H/'artifacts'/f'post_{ver}.cpp';s=p.read_text();assert old in s;s=s.replace(old,new);q=p.with_name(f'post_{ver}_finalize.cpp');assert not q.exists();q.write_text(s);subprocess.run(['g++','-O3','-std=c++17',str(q),'-o',str(q.with_suffix(''))],check=True)
 return dict(version=ver,source=str(q),sha256=hashlib.sha256(q.read_bytes()).hexdigest())
with ThreadPoolExecutor(2) as ex:rows=list(ex.map(run,['v1','v2','v3','v4']))
(H/'FINALIZATION_FIX.json').write_text(json.dumps(dict(reason='Research output worker reconstruction happened after worker DFS deadline; reserve 0.25s for output verification.',files=rows),indent=2))
