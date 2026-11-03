import subprocess,time,json,sys
from pathlib import Path
H=Path(__file__).resolve().parent
# Keep benchmark CPU contention bounded: start after both training series finish.
while True:
 try:
  a=json.loads((H/'logs/equal30_train/results.json').read_text())['results']
  b=json.loads((H/'logs/equal30_tail_train/results.json').read_text())['results']
  if len(a)==81 and len(b)==72:break
 except (FileNotFoundError,json.JSONDecodeError):pass
 time.sleep(10)
subprocess.run([sys.executable,str(H/'bench.py'),'--tag','holdout280','--split','holdout','--mode','equal','--seconds','280','--seeds','31,32','--threads','4','--jobs','2','--variants','base,tail','--cases','alphabig0,latent0'],check=True)
