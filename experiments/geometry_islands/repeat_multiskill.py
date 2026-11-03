import subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
H=Path(__file__).resolve().parent
jobs=[('v1','1,2,3,4'),('v2','6'),('v3','8'),('v4','7')]
def run(job):
 ver,variants=job;tag=f'post60_multiskill_{ver}_fixed'
 with (H/'logs'/f'{tag}.stdout').open('x') as f:
  subprocess.run(['/tmp/ta-boundary-venv/bin/python',str(H/'bench.py'),'--tag',tag,'--split','train','--variants',variants,'--seeds','11','--seconds','60','--threads','1','--jobs','1','--cases','multiskill0','--post-from','train_base60','--exe',f'post_{ver}_finalize'],stdout=f,stderr=subprocess.STDOUT,check=True)
with ThreadPoolExecutor(4) as ex:list(ex.map(run,jobs))
