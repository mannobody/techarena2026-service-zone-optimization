"""Prepare and freeze a selected development policy before generating holdout.

Explicit selection is a CLI argument; this script never reads holdout results.
Original development source and binary remain untouched.
"""
import hashlib,json,subprocess,sys,time
from pathlib import Path

# Serialize an observation copy without altering commands or subprocess env.
import sys as _report_sys
_REPORT_ROOT = next(p for p in Path(__file__).resolve().parents
                    if (p / 'tools/public_metadata.py').is_file())
_report_sys.path.insert(0, str(_REPORT_ROOT / 'tools'))
from public_metadata import public_json as _public_json
def report_json(value, **kwargs):
    return _public_json(value, _REPORT_ROOT, **kwargs)

I=Path(__file__).resolve().parent
R=I.parent
ROOT=R.parents[1]
mode=int(sys.argv[1])
assert mode in (5,6)
assert not (I/'FINAL_FREEZE.json').exists()
assert not (I/'HOLDOUT_INPUTS.json').exists()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
old=I/'src/boundary_dev.cpp'
source=old.read_text()
needle='mode(getenv("ESCAPE_MODE")?atoi(getenv("ESCAPE_MODE")):0)'
assert source.count(needle)==1
source=source.replace(needle,f'mode(getenv("ESCAPE_MODE")?atoi(getenv("ESCAPE_MODE")):{mode})')
guard='if (escape.tick(E,Gd,rng,cur,now)) { wsig=~0ULL; now=elapsed(); if(now>=tloop) break; }'
assert source.count(guard)==1
source=source.replace(guard,'if (escape.tick(E,Gd,rng,cur,now)) wsig=~0ULL;\n            now=elapsed(); if(now>=tloop) break; // charge observer cost even without state change')
d=I/'final_candidate';d.mkdir(exist_ok=False)
p=d/'main.cpp';p.write_text(source)
(d/'Makefile').write_text('CXX ?= g++\nCXXFLAGS := -O3 -std=c++17 -pthread\n\nall: solve\n\nsolve: main.cpp\n\t$(CXX) $(CXXFLAGS) main.cpp -o solve\n\n.PHONY: all\n')
cmd=['taskset','-c','14,15','make','-C',str(d)]
with (I/'FINAL_BUILD.log').open('x') as log:
    subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,check=True)
binary=d/'solve'
freeze={'frozen_unix':time.time(),'source':str(p.relative_to(ROOT)),'source_sha256':sha(p),
        'binary':str(binary.relative_to(ROOT)),'binary_sha256':sha(binary),
        'makefile_sha256':sha(d/'Makefile'),'compiler':subprocess.check_output(['g++','--version'],text=True),
        'build_command':cmd,'default_mode':mode,'default_seconds':280,
        'off_env':{'DBG':'1','ESCAPE_MODE':'0'},'candidate_env':{'DBG':'1'},
        'development_source_sha256':sha(old),
        'changes_after_development':['Set selected ESCAPE_MODE default; all-off explicitly overrides to0.',
            'Always refresh elapsed and check tloop after controller tick, including tick=false observer cost.'],
        'runtime_policy':'No new input-specific rules, no external dependencies, no checkpoint reader in runtime.',
        'holdout_policy':'Sources/binary/parameters immutable after this freeze; no new holdout data generated before freeze.'}
(I/'FINAL_FREEZE.json').write_text(report_json(freeze,indent=2))
print(report_json(freeze,indent=2))
