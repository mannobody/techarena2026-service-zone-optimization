from pathlib import Path
import subprocess,hashlib,json,zipfile,shutil
H=Path(__file__).resolve().parent;E=H.parent;R=E.parent;D=H/'artifacts/package';D.mkdir()
s=(E/'geometry_islands/artifacts/robust_v1.cpp').read_text();bb=(E/'boundary_beam/src/boundary.h').read_text();tail=(E/'boundary_beam/src/tail.h').read_text()
# Reuse the capacity-bound scratch array. bound() completes before recursive DFS,
# so the workspace is never live across recursion. Sorting and summation unchanged.
bb=bb.replace("// All point-footprints use the incumbent solver's conservative geometry predicates.","// Point-footprints use Sol's selected geometry kernel (exact by default in v4).")
bb=bb.replace('vector<double> suf;','vector<double> bound_prices; vector<double> suf;',1)
bb=bb.replace('        int n=xs.size();suf.assign','        bound_prices.reserve(xs.size());\n        int n=xs.size();suf.assign',1)
bb=bb.replace('for(int o:ops){vector<double> p;for(int k=j;','for(int o:ops){auto& p=bound_prices;p.clear();for(int k=j;',1)
assert 'auto& p=bound_prices;p.clear();' in bb
# Preserve tested tail scheduling; allow disabling without reserving a new budget.
tail=tail.replace('    if(I.ns>1500||g_best.load()<=0)return;','    if((getenv("BOUNDARY")&&!atoi(getenv("BOUNDARY")))||I.ns>1500||g_best.load()<=0)return;',1)
s=s.replace('// lns.h:',bb+'\n// lns.h:',1).replace('int main(int argc, char** argv)',tail+'\nint main(int argc, char** argv)',1)
s=s.replace('        finish_solution(I, limit);','        finish_solution(I, limit);\n        boundary_finish(I, limit);',1)
(D/'main.cpp').write_text(s);(D/'Makefile').write_text('build:\n\tg++ -O3 -std=c++17 -o solution main.cpp\n\nrun:\n\t./solution\n')
(H/'src/boundary_v4.h').write_text(bb);(H/'src/tail_v4.h').write_text(tail)
subprocess.run(['make','build'],cwd=D,check=True)
z=H/'artifacts/case03_cpp_server_v4_O3.zip'
with zipfile.ZipFile(z,'x',compression=zipfile.ZIP_DEFLATED) as f:
 for name in ['main.cpp','Makefile']:f.write(D/name,name)
manifest=dict(name='v4',status='Built; validation pending; not submitted',zip=str(z),sha256=hashlib.sha256(z.read_bytes()).hexdigest(),source_sha256=hashlib.sha256(s.encode()).hexdigest(),flags='-O3 -std=c++17',default_seconds=280,tests_seconds=60,components=['v3 allocation reuse','genetic office warm start','bounded worker DFS','exact binary64 orientation and coverage','immutable spatial point grid','monotone final B&B24 for N<=1500','reused B&B capacity-bound scratch vector'],not_included=['offline SCIP/HiGHS/CP-SAT libraries','negative island/ejection experiments','unresearched DP replacement'],parents={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [E/'geometry_islands/artifacts/robust_v1.cpp',E/'boundary_beam/src/boundary.h',E/'boundary_beam/src/tail.h']},primary_snapshot={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (R/'solver').glob('*') if p.is_file()})
(H/'MANIFEST.json').write_text(json.dumps(manifest,indent=2));print(z)
