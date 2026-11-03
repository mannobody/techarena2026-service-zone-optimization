// Include after frozen v4 search/finish helpers and geometry_perturb.h, before main.
// Call between finish_solution(I,limit) and boundary_finish(I,limit).
// Flag OFF by default. No restart cache, external file access, or extra dependency.
#pragma once
static void geometry_finish(const Inst&I,double limit){
    int mode=getenv("GEOMETRY_PERTURB")?atoi(getenv("GEOMETRY_PERTURB")):0;
    if(mode<1||mode>3||g_best.load()<=0)return;
    double available_end=limit-max(.25,.002*limit);
    double requested=getenv("GEOMETRY_SECONDS")?atof(getenv("GEOMETRY_SECONDS")):.8;
    if(requested<=0||elapsed()+.02>=available_end)return;
    double start=elapsed(),end=min(available_end,start+requested);
    vector<int>a;vector<char>op;
    {lock_guard<mutex>lk(g_best_mx);a=g_best_asg;op=g_best_open;}
    if(a.empty())return;
    double before=g_best.load();g_wdfs_deadline=end;int nt=detect_cpus();
    uint64_t seed=getenv("SEED")?strtoull(getenv("SEED"),nullptr,10):0;
    auto run=[&](int tid){
        Sol s;s.init(I);s.load_state(a,op);mt19937_64 rng(0xABC8837ULL+seed*1000003ULL+tid*7919ULL);
        GeometryStats st;if(elapsed()<end)geometry_search(s,rng,end,mode,st);
        if(s.objective()>g_best.load()+1e-9)offer(I,s);
        if(DBG)fprintf(stderr,"geometry_tail tid=%d mode=%d accepted=%ld endpoint_improvements=%ld endpoint_returns=%ld endpoint_unrecovered=%ld perturb_seconds=%.6f recovery_seconds=%.6f\n",tid,mode,st.accepted,st.improved,st.returned_same,st.unrecovered,st.perturb_seconds,st.recovery_seconds);
    };
    vector<thread>th;for(int i=1;i<nt;i++)th.emplace_back(run,i);run(0);for(auto&t:th)t.join();
    if(DBG)fprintf(stderr,"geometry_finish before=%.12f after=%.12f seconds=%.6f requested=%.6f\n",before,g_best.load(),elapsed()-start,requested);
}
