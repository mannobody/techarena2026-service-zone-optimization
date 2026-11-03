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
header=R/'src/geometry_perturb_tail.h';reader=ROOT/'experiments/v4_perturbation/shared/checkpoint.h'
callback=r'''
static atomic<int> stage_arrived{0},stage_ready{0};
static string stage_path;
static void search_geometry(Sol&s,mt19937_64&r,double end,int mode,int tid){
 double initial=s.objective(),start=elapsed();GeometryStats st;
 if(mode==0){while(elapsed()+.005<end)lns(s,r,end,end,true);}
 else if(mode==4)polish(s,r,end,end);
 else if(mode==5||mode>=11){
  if(mode>=11)geometry_search(s,r,min(end,elapsed()+.8),mode-10,st);
  stage_arrived.fetch_add(1);
  if(tid==0){while(stage_arrived.load()<detect_cpus())this_thread::yield();
   ofstream f(stage_path);f<<g_buf[g_idx.load()];f.close();
   fprintf(stderr,"geometry_stage initial=%.12f after=%.12f at=%.6f\\n",initial,g_best.load(),elapsed());stage_ready.store(1);
  }else while(!stage_ready.load())this_thread::yield();
  uint64_t seed=getenv("SEED")?strtoull(getenv("SEED"),nullptr,10):0;
  r.seed(0xBB017ULL+tid*7919ULL+seed*1000003ULL);
  vector<int>a;vector<char>op;{lock_guard<mutex>lk(g_best_mx);a=g_best_asg;op=g_best_open;}
  if(!a.empty())s.load_state(a,op);
  while(elapsed()<end){long n=boundary_stats.calls;boundary_move(s,r,min(end,elapsed()+.04),1,1,24);if(n==boundary_stats.calls)break;if(s.objective_fast()>g_best.load()+1e-9)offer(*s.I,s);}
 }
 else geometry_search(s,r,end,mode,st);
 offer(*s.I,s);
 fprintf(stderr,"geometry tid=%d mode=%d initial=%.12f final=%.12f elapsed=%.6f attempts=%ld accepted=%ld reject=%ld worker_reject=%ld loss_reject=%ld moved=%ld hull_changed=%ld freed_points=%ld workers_changed=%ld offices_changed=%ld recoveries=%ld improved=%ld returned_same=%ld unrecovered=%ld perturb_seconds=%.6f recovery_seconds=%.6f loss_sum=%.12f gain_sum=%.12f first_improvement=%.6f\\n",tid,mode,initial,s.objective(),elapsed()-start,st.attempts,st.accepted,st.geometry_reject,st.worker_reject,st.loss_reject,st.moved,st.hull_changed,st.freed_points,st.workers_changed,st.offices_changed,st.recoveries,st.improved,st.returned_same,st.unrecovered,st.perturb_seconds,st.recovery_seconds,st.loss_sum,st.gain_sum,st.first_improvement);
}
int main(int argc,char**argv){stage_path=string(argv[3])+".stage.json";return checkpoint_main(argc,argv,search_geometry);}
'''.replace('\\\\n','\\n')
src=R/'src/post_synced.cpp'
src.write_text('#define main frozen_v4_main\n'+base.read_text()+'\n#undef main\n'+header.read_text()+'\n'+reader.read_text()+'\n'+callback)
cmd=['g++','-O3','-std=c++17','-pthread',str(src),'-o',str(R/'post_synced')]
r=subprocess.run(cmd,capture_output=True);(R/'logs/build_synced.stderr').write_bytes(r.stderr);r.check_returncode()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
(R/'BUILD_SYNCED.json').write_text(report_json({'command':cmd,'affinity':sorted(os.sched_getaffinity(0)),'sources':{str(p.relative_to(ROOT)):sha(p) for p in [base,header,reader,src]},'binary_sha256':sha(R/'post_synced')},indent=2))
