"""Main 60-second confirmation after user steering; parameter choices stay frozen."""
import subprocess,time,json,sys
from pathlib import Path
H=Path(__file__).resolve().parent
while True:
 try:
  if len(json.loads((H/'logs/equal30_train/results.json').read_text())['results'])==81 and len(json.loads((H/'logs/equal30_tail_train/results.json').read_text())['results'])==72:break
 except (FileNotFoundError,json.JSONDecodeError):pass
 time.sleep(10)
subprocess.run([sys.executable,str(H/'bench.py'),'--tag','holdout60_broad','--split','holdout','--mode','equal','--seconds','60','--seeds','31,32,33','--threads','2','--jobs','4','--variants','base,tail','--cases','alphabig0,alphazero0,anti0,huge0,large0,latent0,latent1,latent2,latent3,medium0,multiskill0,tightA0'],check=True)
