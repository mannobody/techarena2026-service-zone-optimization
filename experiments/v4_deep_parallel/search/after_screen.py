from pathlib import Path
import json,time,subprocess,sys
R=Path(__file__).resolve().parent
while True:
 ready=True
 for name,n in [('screen60',96),('phase2_block60',40),('synthetic_all5',28)]:
  p=R/'logs'/name/'results.json'
  try:ready&=len(json.loads(p.read_text()))==n
  except (OSError,json.JSONDecodeError):ready=False
 if ready:break
 time.sleep(20)
sys.exit(subprocess.call([sys.executable,str(R/'run_blocked.py'),str(R/'CONTROL280.json')]))
