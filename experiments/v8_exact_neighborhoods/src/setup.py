import hashlib,json,platform,subprocess,time
from pathlib import Path

# Serialize an observation copy without altering commands or subprocess env.
import sys as _report_sys
_REPORT_ROOT = next(p for p in Path(__file__).resolve().parents
                    if (p / 'tools/public_metadata.py').is_file())
_report_sys.path.insert(0, str(_REPORT_ROOT / 'tools'))
from public_metadata import public_json as _public_json
def report_json(value, **kwargs):
    return _public_json(value, _REPORT_ROOT, **kwargs)

R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
files=['CLAUDE.md','SOLVER.md','EXPERIMENTS.md','task/validate_solution.py','task/Techarena.pdf',
 'experiments/v4_local_search/baseline/frozen_v4.cpp','experiments/server_v8/artifacts/package/main.cpp',
 'experiments/server_v8/artifacts/package/Makefile','experiments/server_v8/artifacts/zip_check/solution',
 'experiments/server_v8/artifacts/case03_cpp_server_v8_O3.zip']
v=dict(timestamp=time.time(),files={f:sha(ROOT/f) for f in files},compiler=subprocess.check_output(['g++','--version'],text=True).splitlines()[0],
 topology=subprocess.check_output(['lscpu','-e=CPU,CORE,SOCKET,MAXMHZ'],text=True),
 binaries={p.name:sha(p) for p in (R/'artifacts').iterdir() if p.is_file() and p.name in ['v4','v8','solution','checkpoint']},
 python=platform.python_version(),errors=[dict(event='verify started before candidate build completed',log='logs/verify_oracles.stderr',
     consequence='first two MIP solves completed; runtime did not start; no result falsely marked successful',retained=True)])
assert v['files'][files[5]]=='5b3914fa9791cb879f3232fb2876a915de83b848ad4b353b0dbf25b574998c25'
assert v['files'][files[6]]=='1857bec7e0882d15cf3091e79aeb0df1608ced5d4ee6883c1cb02656cfbd8e03'
assert v['files'][files[8]]=='cdf65483f9452e9aed4abd6f7fd2e722d566aed891872cde3ddbb1eef181c79a'
(R/'PROVENANCE_INITIAL.json').write_text(report_json(v,indent=2))
print('Provenance verified; prior source/binary/ZIP digests match.')
