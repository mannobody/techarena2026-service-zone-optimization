// Separate final operator: keep the baseline search trajectory and use its remaining budget.
static void boundary_finish(const Inst&I,double limit){
    if(I.ns>1500||g_best.load()<=0)return;
    const double end=limit-max(.25,.002*limit);
    if(elapsed()>=end)return;
    g_wdfs_deadline=end;
    vector<int>a;vector<char>op;
    {lock_guard<mutex> lk(g_best_mx);a=g_best_asg;op=g_best_open;}
    if(a.empty())return;
    double before=g_best.load(),start=elapsed();int nt=detect_cpus();
    auto run=[&](int tid){
        Sol s;s.init(I);s.load_state(a,op);
        uint64_t seed=getenv("SEED")?strtoull(getenv("SEED"),nullptr,10):0;
        mt19937_64 rng(0xBB017ULL+tid*7919ULL+seed*1000003ULL);
        while(elapsed()<end){
            long n=boundary_stats.calls;
            boundary_move(s,rng,min(end,elapsed()+.04),1,1,24);
            if(n==boundary_stats.calls)break;
            if(s.objective_fast()>g_best.load()+1e-9)offer(I,s);
        }
        if(DBG)fprintf(stderr,"boundary tid=%d calls=%ld nodes=%ld complete=%ld wins=%ld gain=%.9f\n",tid,boundary_stats.calls,boundary_stats.nodes,boundary_stats.complete,boundary_stats.wins,boundary_stats.gain);
    };
    vector<thread>th;for(int i=1;i<nt;i++)th.emplace_back(run,i);run(0);for(auto&t:th)t.join();
    if(DBG)fprintf(stderr,"boundary_finish before=%.9f after=%.9f seconds=%.6f\n",before,g_best.load(),elapsed()-start);
}
