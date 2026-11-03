from pathlib import Path

# Serialize an observation copy without altering commands or subprocess env.
import sys as _report_sys
_REPORT_ROOT = next(p for p in Path(__file__).resolve().parents
                    if (p / 'tools/public_metadata.py').is_file())
_report_sys.path.insert(0, str(_REPORT_ROOT / 'tools'))
from public_metadata import public_json as _public_json
def report_json(value, **kwargs):
    return _public_json(value, _REPORT_ROOT, **kwargs)

import json,hashlib,subprocess,os
os.sched_setaffinity(0,{12,13});R=Path(__file__).resolve().parent;ROOT=R.parents[2]
b=ROOT/'experiments/v4_local_search/baseline/frozen_v4.cpp';h=R.parent/'shared/checkpoint.h';p=R/'src/exact_repeat.cpp'
p.write_text('#define main frozen_main\n'+b.read_text()+'\n#undef main\n'+h.read_text()+'''\nstatic void repeated(Sol&s,mt19937_64&r,double end,int,int){while(elapsed()+.005<end)lns(s,r,end,end,true);offer(*s.I,s);}\nint main(int argc,char**argv){return checkpoint_main(argc,argv,repeated);}\n''')
cmd=['g++','-O3','-std=c++17','-pthread',str(p),'-o',str(R/'exact_repeat')];r=subprocess.run(cmd,capture_output=True);(R/'logs/build_repeat.stderr').write_bytes(r.stderr);r.check_returncode()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
(R/'BUILD_REPEAT.json').write_text(report_json({'source_sha256':sha(p),'frozen_sha256':sha(b),'reader_sha256':sha(h),'binary_sha256':sha(R/'exact_repeat'),'command':cmd,'affinity':[12,13]},indent=2))
