import hashlib,json,subprocess,os
from pathlib import Path

# Serialize an observation copy without altering commands or subprocess env.
import sys as _report_sys
_REPORT_ROOT = next(p for p in Path(__file__).resolve().parents
                    if (p / 'tools/public_metadata.py').is_file())
_report_sys.path.insert(0, str(_REPORT_ROOT / 'tools'))
from public_metadata import public_json as _public_json
def report_json(value, **kwargs):
    return _public_json(value, _REPORT_ROOT, **kwargs)

R=Path(__file__).resolve().parent;ROOT=R.parents[2]
os.sched_setaffinity(0,{12,13})
base=ROOT/'experiments/v4_local_search/baseline/frozen_v4.cpp'
header=R/'src/geometry_perturb.h';reader=ROOT/'experiments/v4_perturbation/shared/checkpoint.h'
callback=r'''
static void search_geometry(Sol&s,mt19937_64&r,double end,int mode,int tid){
 double initial=s.objective(),start=elapsed();GeometryStats st;
 if(mode==0)lns(s,r,end,end,true);
 else if(mode==4)polish(s,r,end,end);
 else geometry_search(s,r,end,mode,st);
 offer(*s.I,s);
 fprintf(stderr,"geometry tid=%d mode=%d initial=%.12f final=%.12f elapsed=%.6f attempts=%ld accepted=%ld reject=%ld worker_reject=%ld loss_reject=%ld moved=%ld hull_changed=%ld freed_points=%ld workers_changed=%ld offices_changed=%ld recoveries=%ld improved=%ld returned_same=%ld unrecovered=%ld perturb_seconds=%.6f recovery_seconds=%.6f loss_sum=%.12f gain_sum=%.12f first_improvement=%.6f\\n",tid,mode,initial,s.objective(),elapsed()-start,st.attempts,st.accepted,st.geometry_reject,st.worker_reject,st.loss_reject,st.moved,st.hull_changed,st.freed_points,st.workers_changed,st.offices_changed,st.recoveries,st.improved,st.returned_same,st.unrecovered,st.perturb_seconds,st.recovery_seconds,st.loss_sum,st.gain_sum,st.first_improvement);
}
int main(int argc,char**argv){return checkpoint_main(argc,argv,search_geometry);}
'''.replace('\\n','\n')
src=R/'src/post_geometry.cpp'
src.write_text('#define main frozen_v4_main\n'+base.read_text()+'\n#undef main\n'+header.read_text()+'\n'+reader.read_text()+'\n'+callback)
cmd=['g++','-O3','-std=c++17','-pthread',str(src),'-o',str(R/'post_geometry')]
r=subprocess.run(cmd,capture_output=True);(R/'logs/build.stderr').write_bytes(r.stderr);r.check_returncode()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
(R/'BUILD.json').write_text(report_json({'command':cmd,'affinity':sorted(os.sched_getaffinity(0)),'sources':{str(p.relative_to(ROOT)):sha(p) for p in [base,header,reader,src]},'binary_sha256':sha(R/'post_geometry')},indent=2))
