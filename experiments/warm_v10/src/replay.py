"""Replay a saved manifest with its exact runner, same inputs/binaries/flags; fresh solves."""
import hashlib,json,subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
name,newname=sys.argv[1:];m_path=R/'logs'/name/'MANIFEST.json';m=json.loads(m_path.read_text());spec=m['spec']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert not (R/'logs'/newname).exists()
for k,p in spec['cases'].items():assert sha(ROOT/p)==m['inputs'][k],p
for k,v in spec['variants'].items():assert sha(ROOT/v['binary'])==m['binaries'][k],k
assert sha(ROOT/'task/validate_solution.py')==m['validator']
candidates=[R/'src/run.py',R/'src/run_instrumented.py',*(R/'artifacts/runners').glob('*.py')]
matching=[p for p in candidates if sha(p)==m['runner_sha256']];assert matching,('archived runner missing',m['runner_sha256'])
# Archived scripts derive R from __file__; restore a copy beneath src/ before execution.
runner=R/'src'/('replay_runner_'+m['runner_sha256'][:16]+'.py')
if runner.exists():assert sha(runner)==m['runner_sha256']
else:runner.write_bytes(matching[0].read_bytes())
spec['name']=newname;p=R/(newname+'.json');assert not p.exists();p.write_text(json.dumps(spec,indent=2))
subprocess.run([sys.executable,str(runner),str(p)],cwd=ROOT,check=True)
subprocess.run([sys.executable,str(R/'src/analysis.py'),newname],cwd=ROOT,check=True)
