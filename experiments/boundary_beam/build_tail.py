from pathlib import Path
import subprocess,hashlib,json
H=Path(__file__).resolve().parent;b=H/'baseline/solver'
s=(b/'solve.cpp').read_text()
for h in b.glob('*.h'):s=s.replace(f'#include "{h.name}"',h.read_text())
s=s.replace('// lns.h:',(H/'src/boundary.h').read_text()+'\n// lns.h:',1)
s=s.replace('int main(int argc, char** argv)',(H/'src/tail.h').read_text()+'\nint main(int argc, char** argv)',1)
s=s.replace('        Inst I = load_instance(inp);','''        Inst I = load_instance(inp);
        double full_limit=limit;
        if(getenv("B_RESERVE")&&atoi(getenv("B_RESERVE"))&&I.ns<=1500)limit-=min(6.,.05*limit);''',1)
s=s.replace('        finish_solution(I, limit);','        finish_solution(I, limit);\n        boundary_finish(I,full_limit);',1)
p=H/'artifacts/candidate_tail.cpp';p.write_text(s)
subprocess.run(['g++','-O3','-std=c++17',str(p),'-o',str(p.with_suffix(''))],check=True)
(H/'build_manifest_tail.json').write_text(json.dumps({str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [p,p.with_suffix(''),H/'src/boundary.h',H/'src/tail.h']},indent=2))
