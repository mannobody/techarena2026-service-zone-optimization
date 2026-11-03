import json,subprocess,time
from pathlib import Path
H=Path(__file__).resolve().parent;D=H/'logs/index_oracle';D.mkdir();rows=[]
while not (H/'build_index.json').exists():time.sleep(2)
pairs=[(p,H/'logs/train_base60'/f'{p.stem}_1_base.json') for p in sorted((H/'data/train').glob('*.json'))]
pairs +=[(p,H.parent/'boundary_beam/logs/edges'/p.stem/'solution.json') for p in sorted((H.parent/'boundary_beam/data/edge').glob('*.json'))]
for inp,sol in pairs:
 asg=[-1]*len(json.loads(inp.read_text())['sites'])
 for o in json.loads(sol.read_text()):
  for x in o['sites']:asg[x]=o['officeId']
 p=D/f'{inp.stem}.asg';p.write_text(' '.join(map(str,asg)));pr=subprocess.run([str(H/'artifacts/index_oracle'),str(inp),str(p)],text=True,capture_output=True,timeout=65)
 row=dict(case=inp.stem,input=str(inp),source=str(sol),rc=pr.returncode,stderr=pr.stderr,**json.loads(pr.stdout));rows.append(row);(D/'results.json').write_text(json.dumps(rows,indent=2));print(row,flush=True);assert pr.returncode==0
