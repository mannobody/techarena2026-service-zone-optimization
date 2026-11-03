import json,subprocess,os,sys,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];ROOT=R.parents[1];os.sched_setaffinity(0,{14,15})
while not (R/'PACKAGE_CHECK_FINAL.json').exists():time.sleep(1)
# Parent and tested children stay on controller cores, disjoint from every quality slot.
p=R/'src/qa_revision.py';s=p.read_text().replace("'3,6',str(R/'artifacts'","os.getenv('QA_CPU','3,6'),str(R/'artifacts'")
new=R/'src/qa_final.py';assert not new.exists();new.write_text(s)
with (R/'logs/qa_v4.output').open('x')as f:subprocess.run([sys.executable,str(new),'v4'],cwd=ROOT,env=dict(os.environ,QA_CPU='14,15'),stdout=f,stderr=subprocess.STDOUT,check=True)
(R/'QA_FINAL_STATUS.json').write_text(json.dumps(dict(stage='complete'),indent=2))
