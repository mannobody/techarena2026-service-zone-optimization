from pathlib import Path
import subprocess,json,hashlib
H=Path(__file__).resolve().parent;old=(H/'src/window_v2.h').read_text()
new=old.replace('int bad=0;long double val=(long double)alpha*grid[r];','if(r)tree.add(1,0,G-1,0,r-1,0,-(long double)alpha*(grid[r]-grid[r-1]));\n  int bad=0;long double val=0;').replace('long double value=tree.t[1].value-(long double)alpha*grid[r];','long double value=tree.t[1].value;')
assert new!=old;(H/'src/window_v3.h').write_text(new)
s=(H/'artifacts/window_oracle_v2.cpp').read_text().replace(old,new,1).replace('test<2000','test<3000')
p=H/'artifacts/window_oracle_v3.cpp';p.write_text(s);subprocess.run(['g++','-O3','-std=c++17',str(p),'-o',str(p.with_suffix(''))],check=True);pr=subprocess.run([str(p.with_suffix(''))],capture_output=True,text=True);(H/'logs/window_oracle_v3.stderr').write_text(pr.stderr);assert pr.returncode==0,pr.stderr;(H/'logs/window_oracle_v3.json').write_text(pr.stdout)
for name,dest in [('adaptive_v1','relative_v1'),('post_adaptive','post_relative')]:
 s=(H/'artifacts'/f'{name}.cpp').read_text();assert old in s;s=s.replace(old,new,1);p=H/'artifacts'/f'{dest}.cpp';p.write_text(s);subprocess.run(['g++','-O3','-std=c++17',str(p),'-o',str(p.with_suffix(''))],check=True)
(H/'PREREGISTRATION.json').write_text(json.dumps(dict(candidate=str(H/'artifacts/relative_v1.cpp'),sha256=hashlib.sha256((H/'artifacts/relative_v1.cpp').read_bytes()).hexdigest(),split='full_holdout',seconds=60,threads=2,jobs=6,seeds=[111,112,113],baseline='frozen server v4',changes=['same-grid O(KGlogG) window optimization','relative values avoid alpha*absolute-load cancellation','quadratic fallback for G<=128','common task-count gcd compression'],note='Frozen before any full_holdout results'),indent=2))
