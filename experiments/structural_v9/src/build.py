"""Compose only from the immutable exact v4, with an auditable minimal hook."""
import hashlib,json,subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
base=ROOT/'experiments/v4_local_search/baseline/frozen_v4.cpp'
assert hashlib.sha256(base.read_bytes()).hexdigest()=='5b3914fa9791cb879f3232fb2876a915de83b848ad4b353b0dbf25b574998c25'
s=base.read_text();h=(R/'src/zone_master.h').read_text();signed=(R/'src/signed_exchange.h').read_text()
revision=sys.argv[1]if len(sys.argv)>1 else 'v2'
out=R/'artifacts'/revision;out.mkdir(exist_ok=False)
assert s.count('int main(int argc, char** argv) {')==1
s=s.replace('int main(int argc, char** argv) {',h+'\n'+signed+'\nint main(int argc, char** argv) {')
s=s.replace('        Fast F(I);','        if(zm::tiny(I,limit))return 0;\n        Fast F(I);',1)
s=s.replace('        boundary_finish(I, limit);',
'''        if(!getenv("ZM_DISABLE")) {
            double signed_end=min(limit-max(.25,.002*limit),elapsed()+.45*max(0.,limit-max(.25,.002*limit)-elapsed()));
            zm_signed_finish(I,signed_end);
        }
        zm::finish(I, limit);
        boundary_finish(I, limit);''',1)
s=s.replace('    if (n > 16) n = 16;','    if (n > 2) n = 2;',1)
s=s.replace('    alarm((unsigned)max(5.0, limit + 14));',
'''    alarm((unsigned)max(5.0, limit + 14));
    struct sigaction deadline_action = sa;
    deadline_action.sa_handler = zm::deadline_signal;
    sigaction(SIGALRM, &deadline_action, nullptr);
    double wall_budget=max(.01,limit-.04);
    struct itimerval timer{};
    timer.it_value.tv_sec=(time_t)wall_budget;
    timer.it_value.tv_usec=(suseconds_t)((wall_budget-timer.it_value.tv_sec)*1e6);
    setitimer(ITIMER_REAL,&timer,nullptr);''',1)
# Reserve only the last stage: keep early warm/start/chunk phase schedules on
# the original wall clock. v3 shortened tend and changed every earlier phase.
needle='    static const double LAMS[4] = {0.25, 0.10, 0.50, 0.0};'
assert s.count(needle)==1
s=s.replace(needle,'''    const bool zm_reserved=(!getenv("ZM_RESERVE")||atoi(getenv("ZM_RESERVE")))&&!getenv("ZM_DISABLE")&&g_geo_exact&&I.nsk<=63&&I.alpha>=0&&I.ns>16&&I.ns<=1500&&I.no<=16&&I.nw<=128&&all_of(I.cost.begin(),I.cost.end(),[](double x){return x>=0;});
    const double zm_worker_end=tend-max(.5,(zm_reserved?.08:.02)*tend);
'''+needle,1)
s=s.replace('while (elapsed() < tend - max(0.5, 0.02 * tend)) {','while (elapsed() < zm_worker_end) {',1)
s=s.replace('        double ce = now0 + chunk;','        chunk=min(chunk,max(0.,zm_worker_end-now0));\n        double ce = now0 + chunk;',1)
(out/'main.cpp').write_text(s)
(out/'Makefile').write_text('build:\n\tg++ -O3 -std=c++17 -o solution main.cpp\n\nrun:\n\t./solution\n')
cmd=['taskset','-c','14,15','g++','-O3','-std=c++17',str(out/'main.cpp'),'-o',str(out/'candidate')]
subprocess.run(cmd,check=True)
files=[base,R/'src/zone_master.h',R/'src/signed_exchange.h',R/'src/build.py',out/'main.cpp',out/'Makefile',out/'candidate',R/'artifacts/v4']
(out/'BUILD.json').write_text(json.dumps({'command':cmd,'files':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}},indent=2))
