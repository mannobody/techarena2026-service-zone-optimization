import hashlib,json,os,subprocess,sys,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];ROOT=R.parents[1];sys.path.insert(0,str(ROOT/'task'))
from validate_solution import validate
pkg=R/'package';subprocess.run(['taskset','-c','14,15','make','build'],cwd=pkg,check=True,stdout=subprocess.DEVNULL)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
same_binary=sha(pkg/'solution')==sha(R/'artifacts/final_research/candidate')
dest=R/'logs/package_contract';dest.mkdir(exist_ok=False);rows=[]
for case,source,expected in [('tiny','inputs/dev/small_grid.json',254.08981479007377),('native',str(ROOT/'task/instance2/instance.json'),None),('big','logs/contract_final_research/inputs/edge_big10k.json',None)]:
    wd=dest/case;wd.mkdir();inp=Path(source)if Path(source).is_absolute()else R/source;(wd/'instance.json').write_bytes(inp.read_bytes())
    # Execute the exact package run recipe in a directory containing one input.
    recipe=(pkg/'Makefile').read_text().split('run:\n\t',1)[1].strip();recipe=recipe.replace('./solution',str(pkg/'solution'))
    env={'PATH':os.environ['PATH'],'TL':'1'};begin=time.monotonic()
    with (dest/f'{case}.stderr').open('w')as f:p=subprocess.run(['taskset','-c','14,15','sh','-c',recipe],cwd=wd,env=env,stderr=f,stdout=subprocess.DEVNULL,timeout=3)
    v=validate(wd/'instance.json',wd/'solution.json');files=sorted(x.name for x in wd.iterdir());ok=p.returncode==0 and isinstance(v,(int,float))and files==['instance.json','solution.json']and (expected is None or abs(v-expected)<1e-7)
    rows.append(dict(case=case,rc=p.returncode,wall=time.monotonic()-begin,official=v,files=files,ok=ok,env=env,recipe=recipe))
(R/'PACKAGE_CHECK.json').write_text(json.dumps(dict(same_binary_as_measured=same_binary,binary_sha256=sha(pkg/'solution'),rows=rows),indent=2));assert same_binary and all(r['ok']for r in rows)
print(json.dumps(dict(same_binary=same_binary,cases=len(rows),ok=sum(r['ok']for r in rows))))
