from pathlib import Path
import subprocess,hashlib,json
H=Path(__file__).resolve().parent
base=H/'baseline/solver'
def flatten(p):
 s=p.read_text()
 for h in base.glob('*.h'): s=s.replace(f'#include "{h.name}"',h.read_text())
 assert '#include "' not in s
 return s
s=flatten(base/'solve.cpp');header=(H/'src/boundary_v1.h').read_text()
# Insert before lns, after all primitives it uses, preserving base include order.
s=s.replace('// lns.h:',header+'\n// lns.h:',1)
# Use a reserved tail in each search chunk. Keep flags off by default in research build.
s=s.replace('    polish(s, rng, min(tend, dp_deadline), dp_deadline, lock_offices);', '''    int bm=getenv("BOUNDARY")?atoi(getenv("BOUNDARY")):0;
    double bend=min(tend,dp_deadline);
    double reserve=bm?min(.4,max(0.,bend-elapsed())*.35):0.;
    polish(s,rng,bend-reserve,dp_deadline,lock_offices);
    if(bm&&elapsed()<bend){
        boundary_polish(s,rng,bend,bm,getenv("B_SUPPORT")?atoi(getenv("B_SUPPORT")):0);
        offer(I,s);
    }''')
s=s.replace('    }\n}\n\n#include "evolution_warm.h"','    }\n}\n\n#include "evolution_warm.h"') # no-op, flattened
# standalone postprocessor reads saved assignment for research only; never packaged
prefix=s[:s.index('int main(int argc, char** argv)')]
post=prefix+(H/'src/post.cpp').read_text()
for name,code in [('candidate',s),('post',post)]:
 p=H/'artifacts'/f'{name}.cpp';p.write_text(code)
 subprocess.run(['g++','-O3','-std=c++17',str(p),'-o',str(H/'artifacts'/name)],check=True)
manifest={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in list(base.glob('*'))+list((H/'artifacts').glob('*')) if p.is_file()}
(H/'build_manifest.json').write_text(json.dumps(manifest,indent=2))
