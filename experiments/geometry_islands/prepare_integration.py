from pathlib import Path
import difflib,hashlib,json
H=Path(__file__).resolve().parent;B=H/'baseline/solver';D=H/'integration/solver';D.mkdir(parents=True,exist_ok=True)
s=(H/'artifacts/robust_v1.cpp').read_text()
# Extract tested contiguous modules; extra newline belongs to include expansion.
mods={p.name:p.read_text() for p in B.iterdir() if p.is_file()}
for name,nxt in [('geom.h','inst.h'),('sol.h','check.h'),('check.h','output.h')]:
 start=s.index(mods[name].splitlines()[0]);end=s.index(mods[nxt].splitlines()[0],start)
 mods[name]=s[start:end].removesuffix('\n')
mods['spatial_geometry.h']=(H/'src/spatial.h').read_text()
mods['solve.cpp']=mods['solve.cpp'].replace('#include "sol.h"','#include "spatial_geometry.h"\n#include "sol.h"').replace('Inst I = load_instance(inp);','Inst I = load_instance(inp);\n        g_geo_grid.init(I);',1)
flat=mods['solve.cpp']
for p in B.glob('*.h'):flat=flat.replace(f'#include "{p.name}"',mods[p.name])
flat=flat.replace('#include "spatial_geometry.h"',mods['spatial_geometry.h'])
assert flat==s, 'Modular copy must reproduce tested source byte for byte'
patch=[]
for name,body in mods.items():
 (D/name).write_text(body);old=(B/name).read_text() if (B/name).exists() else ''
 if old!=body:patch.extend(difflib.unified_diff(old.splitlines(True),body.splitlines(True),fromfile='a/solver/'+name if old else '/dev/null',tofile='b/solver/'+name))
(H/'integration.patch').write_text(''.join(patch))
(H/'INTEGRATION_MANIFEST.json').write_text(json.dumps(dict(status='Optional experimental patch; NOT applied',flatten_equals_tested=True,flat_sha256=hashlib.sha256(flat.encode()).hexdigest(),files={str(D/n):hashlib.sha256(v.encode()).hexdigest() for n,v in mods.items()}),indent=2))
print('Exact flat-source match; patch prepared, primary unchanged')
