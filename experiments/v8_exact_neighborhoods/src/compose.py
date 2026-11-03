"""Rebuild standalone candidate from verified v8 and the local header only."""
import hashlib,json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]
s=(R/'src/frozen_v8.cpp').read_text(); assert hashlib.sha256(s.encode()).hexdigest()=='1857bec7e0882d15cf3091e79aeb0df1608ced5d4ee6883c1cb02656cfbd8e03'
h=(R/'src/exact_neighborhood.h').read_text()
h=h.replace('static void xn_finish(', (R/'src/structural_packets.h').read_text()+'\nstatic void xn_finish(',1)
revision=sys.argv[1] if len(sys.argv)>1 else 'candidate_v2'
out=R/'artifacts'/revision;out.mkdir(exist_ok=False)
fallback=(R/'src/fill_fallback.h').read_text()
s=s.replace('static void recreate(Engine& E, Guide& Gd,',fallback+'\nstatic void recreate(Engine& E, Guide& Gd,',1)
s=s.replace('double deadline = 1e18) {\n    Sol& s = E.s;',
    'double deadline = 1e18) {\n    if(xn_fill_mode()==1||xn_fill_mode()==3){xn_recreate(E,Gd,rng,aggressive,topk,deadline);return;}\n    Sol& s = E.s;',1)
s=s.replace('static bool greedy_fill(Sol& s, Engine& E, double deadline) {',
    'static bool greedy_fill(Sol& s, Engine& E, double deadline) {\n    if(xn_fill_mode()==1||xn_fill_mode()==2)return xn_greedy_fill(s,E,deadline);',1)
s=s.replace('if(best>0)un.push_back({best,x});','if(best>0||xn_fill_mode())un.push_back({best,x});',1)
s=s.replace('        finish_solution(I, limit);','        finish_solution(I, limit);',1)
s=s.replace('        if (DBG) fprintf(stderr, "worker_dfs calls=',
    '        if(DBG)fprintf(stderr,"XNFILL geofail=%ld alternative=%ld negative=%ld\\n",xn_fill_geofail.load(),xn_fill_alternative.load(),xn_fill_negative.load());\n        if (DBG) fprintf(stderr, "worker_dfs calls=',1)
# Include after BoundarySearch and before LNS: dependencies already defined.
s=s.replace('// lns.h: главный цикл LNS + отжиг, detect_cpus.',h+'\n// lns.h: главный цикл LNS + отжиг, detect_cpus.',1)
# Correct the known stale open-bit signature; isolated by XN_SIG_FIX=0 ablation.
s=s.replace('isopen[o] = 0;\n        clear_cov(o);','isopen[o] = 0;\n        if(!getenv("XN_SIG_FIX")||atoi(getenv("XN_SIG_FIX")))sig_open(o);\n        clear_cov(o);',1)
# Complete canonical open-bit bookkeeping (initial realization + direct open).
s=s.replace('s.isopen[o] = 1;\n        s.rebuild_hull(o);','s.isopen[o] = 1;\n        if(getenv("XN_SIG_FIX")&&atoi(getenv("XN_SIG_FIX")))s.sig_open(o);\n        s.rebuild_hull(o);',1)
s=s.replace('s.isopen[o] = 1;\n                s.rebuild_hull(o);','s.isopen[o] = 1;\n                if(getenv("XN_SIG_FIX")&&atoi(getenv("XN_SIG_FIX")))s.sig_open(o);\n                s.rebuild_hull(o);',1)
# An optional exact staffing attempt is bounded by the caller's global deadline
# and a 2ms local slice. Failure on timeout remains an unknown conservative result.
s=s.replace('int nodes = 0, budget = (int)max(64LL, min(4096LL, 4LL * I->nw * max(1, I->no)));',
    '''int nodes = 0, budget = (int)max(64LL, min(4096LL, 4LL * I->nw * max(1, I->no)));
        static const bool xn_exact_worker=getenv("XN_WORKER")&&atoi(getenv("XN_WORKER"));
        const double worker_end=xn_exact_worker?min(g_wdfs_deadline,elapsed()+.002):g_wdfs_deadline;
        if(xn_exact_worker)budget=INT_MAX;''',1)
s=s.replace('((nodes & 31) == 0 && elapsed() >= g_wdfs_deadline)',
    '((nodes & 31) == 0 && elapsed() >= worker_end)',1)
s=s.replace('    if (n > 16) n = 16;','    if (n > 2) n = 2;',1)
s=s.replace('        boundary_finish(I, limit);','        xn_finish(I, limit);\n        boundary_finish(I, limit);',1)
# Exact tiny full-domain path, including crossing segments, serves also as runtime oracle.
s=s.replace('        Fast F(I);','''        if((!getenv("XN_MODE")||atoi(getenv("XN_MODE"))>0)&&I.ns<=10&&I.no<=5){
            Sol tiny;tiny.init(I);mt19937_64 tr(1);XNStats st;
            xn_move(tiny,tr,min(limit-max(.25,.002*limit),elapsed()+min(.15,.1*limit)),2,10,&st);
            if(st.complete&&st.nodes){fprintf(stderr,"XN global_complete=1 objective=%.9f\\n",g_best.load());return 0;}
        }
        Fast F(I);''',1)
(out/'main.cpp').write_text(s)
(out/'Makefile').write_text((R/'artifacts/Makefile').read_text())
print(json.dumps(dict(source=hashlib.sha256(s.encode()).hexdigest(),header=hashlib.sha256(h.encode()).hexdigest())))
