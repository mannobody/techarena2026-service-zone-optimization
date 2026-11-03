// Explore cheap office subsets on otherwise idle cores during serial Fast.search.
// These threads keep running to the original deadline; later workers use only
// the remaining slots. Total solver concurrency never exceeds detect_cpus().
static void evo_scout(const Inst&I,const Fast&F,uint64_t seed,double limit,
                      double dp_deadline,int tid) {
    mt19937_64 rng(seed);vector<Cand> cands;
    vector<int> eligible;
    for(int o=0;o<I.no;o++)if(I.maxsize[o]>0) {
        bool duplicate=false;
        for(int p:eligible)if(pteq(I.P[I.ns+o],I.P[I.ns+p])){duplicate=true;break;}
        if(!duplicate)eligible.push_back(o);
    }
    if(eligible.empty())return;
    auto add=[&](vector<int>op) {
        sort(op.begin(),op.end());
        for(const auto&c:cands)if(c.op==op)return;
        Cand c;c.op=move(op);c.h.assign(I.no,0.);
        c.G.assign(I.P.begin()+I.ns,I.P.end());c.f=0.;
        cands.push_back(move(c));
    };
    add(eligible);
    int n=max(3,(int)sqrt((double)eligible.size()));
    for(int j=0;j<n&&elapsed()<.08*limit;j++) {
        auto op=eligible;shuffle(op.begin(),op.end(),rng);
        int k=1+(tid+j*max(1,(int)eligible.size()/n))%eligible.size();
        op.resize(k);add(move(op));
    }
    fprintf(stderr,"scout tid=%d candidates=%zu t=%.3f\n",tid,cands.size(),elapsed());
    worker(I,F,cands,seed,limit,dp_deadline,tid);
}
