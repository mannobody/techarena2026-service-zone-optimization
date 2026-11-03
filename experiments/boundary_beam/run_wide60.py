import subprocess,time,json,sys,hashlib,datetime
from pathlib import Path
H=Path(__file__).resolve().parent
(H/'VALIDATION2_PREREGISTRATION.json').write_text(json.dumps(dict(timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),candidate='candidate_v2',parameters=dict(BOUNDARY=1,B_SUPPORT=1,q=24),source_sha256=hashlib.sha256((H/'artifacts/candidate_v2.cpp').read_bytes()).hexdigest(),reason='Completed train30: wider reconstruction outperformed q12. Fresh validation data, no adjustment using tail holdout.',seeds=[61,62,63],seconds=60,threads=2),indent=2))
# package60 follows the four-thread repeat. These slots then become available.
while not (H/'logs/package60/results.json').exists():time.sleep(10)
subprocess.run([sys.executable,str(H/'bench.py'),'--tag','validation2_wide60','--split','validation2','--mode','equal','--seconds','60','--seeds','61,62,63','--threads','2','--jobs','4','--variants','base,wide'],check=True)
