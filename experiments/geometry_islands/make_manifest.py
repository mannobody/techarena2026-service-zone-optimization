from pathlib import Path

# Serialize an observation copy without altering commands or subprocess env.
import sys as _report_sys
_REPORT_ROOT = next(p for p in Path(__file__).resolve().parents
                    if (p / 'tools/public_metadata.py').is_file())
_report_sys.path.insert(0, str(_REPORT_ROOT / 'tools'))
from public_metadata import public_json as _public_json
def report_json(value, **kwargs):
    return _public_json(value, _REPORT_ROOT, **kwargs)

import json,hashlib,subprocess
H=Path(__file__).resolve().parent;R=H.parents[1]
rows=[]
for p in sorted(H.rglob('*')):
 if not p.is_file() or '__pycache__' in p.parts or p.name=='PATHS.json':continue
 rows.append(dict(path=str(p),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
(H/'PATHS.json').write_text(report_json(dict(root=str(H),report=str(H/'REPORT.md'),comparison=str(H/'COMPARISON.md'),mip_results=str(H/'ANCHOR_RESULTS.md'),runtime_zip=str(H/'artifacts/geometry_exact_experimental_O3.zip'),runtime_source=str(H/'artifacts/robust_v1.cpp'),experimental_support=str(H/'anchor_support.py'),raw_logs=str(H/'logs'),data=str(H/'data'),files=rows),indent=2))
for p,sha in json.loads((H/'baseline/manifest.json').read_text()).items():assert hashlib.sha256((R/'solver'/Path(p).name).read_bytes()).hexdigest()==sha
assert not subprocess.check_output(['git','diff','--cached','--name-only'],cwd=R,text=True).strip()
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip()=='1496e64270a671e54b05d4fd9eb70917c369b658'
for patch in ['integration.patch','anchor_integration.patch']:subprocess.run(['git','apply','--check',str(H/patch)],cwd=R,check=True)
print(f'{len(rows)} artifact paths/hashes; main source preserved; patches apply; no staging or commits')
