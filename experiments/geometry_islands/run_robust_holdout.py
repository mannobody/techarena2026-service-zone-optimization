import json,time,subprocess
from pathlib import Path
H=Path(__file__).resolve().parent
while True:
 p=H/'logs/precision60/results.json'
 if p.exists():
  try:
   r=json.loads(p.read_text())['results']
   if len(r)==10:
    assert all(x['error'] is None and x['rc']==0 for x in r);break
  except json.JSONDecodeError:pass
 time.sleep(3)
with (H/'logs/robust_holdout60.stdout').open('x') as f:
 subprocess.run(['/tmp/ta-boundary-venv/bin/python',str(H/'bench.py'),'--tag','robust_holdout60','--split','validation2','--variants','base,exact','--seeds','71,72,73','--seconds','60','--threads','2','--jobs','4','--exe','robust_v1'],stdout=f,stderr=subprocess.STDOUT,check=True)
