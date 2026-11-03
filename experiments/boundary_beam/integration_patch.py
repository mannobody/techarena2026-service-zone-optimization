from pathlib import Path
import difflib,json,hashlib
H=Path(__file__).resolve().parent;B=H/'baseline/solver';dst=H/'integration/solver';dst.mkdir(parents=True,exist_ok=True)
changes={'boundary_research.h':(H/'src/boundary.h').read_text(),'boundary_tail.h':(H/'src/tail.h').read_text()}
s=(B/'solve.cpp').read_text();s=s.replace('#include "lns.h"','#include "boundary_research.h"\n#include "lns.h"');s=s.replace('int main(int argc, char** argv)','#include "boundary_tail.h"\nint main(int argc, char** argv)',1)
s=s.replace('        Inst I = load_instance(inp);','''        Inst I = load_instance(inp);
        double full_limit=limit;
        if(getenv("B_RESERVE")&&atoi(getenv("B_RESERVE"))&&I.ns<=1500)limit-=min(6.,.05*limit);''',1)
s=s.replace('        finish_solution(I, limit);','        finish_solution(I, limit);\n        boundary_finish(I,full_limit);',1);changes['solve.cpp']=s
patch=''
for name,content in changes.items():
 old=(B/name).read_text() if (B/name).exists() else ''
 (dst/name).write_text(content)
 patch+=''.join(difflib.unified_diff(old.splitlines(True),content.splitlines(True),fromfile=f'a/solver/{name}' if old else '/dev/null',tofile=f'b/solver/{name}'))
(H/'integration/integration.patch').write_text(patch)
flat=s
for p in B.glob('*.h'):flat=flat.replace(f'#include "{p.name}"',p.read_text())
for name,c in changes.items():flat=flat.replace(f'#include "{name}"',c)
assert flat==(H/'artifacts/candidate_tail.cpp').read_text()
(H/'integration/manifest.json').write_text(json.dumps(dict(flattened_matches_tested_source=True,flattened_sha256=hashlib.sha256(flat.encode()).hexdigest(),files={str(dst/p):hashlib.sha256((dst/p).read_bytes()).hexdigest() for p in changes}),indent=2));print('Patch flattens exactly to tested source; not applied to solver/')
