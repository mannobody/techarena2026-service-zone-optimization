"""Repeat a stored specification without replacing any old run or warm starting."""
import json,subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]
spec=json.loads(Path(sys.argv[1]).read_text());spec['name']=sys.argv[2]
assert not (R/'logs'/spec['name']).exists()
p=R/(spec['name']+'.json');assert not p.exists();p.write_text(json.dumps(spec,indent=2))
subprocess.run([sys.executable,str(R/'src/run.py'),str(p)],check=True)
