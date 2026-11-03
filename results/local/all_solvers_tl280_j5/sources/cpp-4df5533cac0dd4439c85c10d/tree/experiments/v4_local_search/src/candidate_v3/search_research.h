// Optional basin-level experiments. Included after LNS/polish definitions.
// SEARCH_MODE=1 ILS, 2 VNS, 3 sampled tabu search, 4 population resampling (GWW).
// No external state; bounded memory and the caller's existing time budget.
static uint64_t search_fingerprint(const Sol& s) {
    uint64_t h=1469598103934665603ULL;
    for(int x:s.asg){h^=uint64_t(x+2);h*=1099511628211ULL;}
    return h;
}
static bool search_valid(Sol& s) {
    Engine E(s);
    return E.size_viol(-1,-1)==0 && s.greedy_workers(nullptr);
}
static void search_shake(Sol& s,mt19937_64& rng,int strength,double deadline) {
    const Inst& I=*s.I;Engine E(s);Guide G(s,0.);
    vector<int> assigned,op,closed;
    for(int x=0;x<I.ns;x++)if(s.asg[x]>=0)assigned.push_back(x);
    for(int o=0;o<I.no;o++)if(s.isopen[o] && s.size_[o]>0)op.push_back(o);else if(!s.isopen[o] && I.maxsize[o]>0)closed.push_back(o);
    s.begin_defer();
    if(strength<3 && !assigned.empty()) {
        int center=assigned[rng()%assigned.size()];
        if(strength==1)shuffle(assigned.begin(),assigned.end(),rng);
        else sort(assigned.begin(),assigned.end(),[&](int a,int b){
            auto d=[&](int x){double dx=I.P[x].x-I.P[center].x,dy=I.P[x].y-I.P[center].y;return dx*dx+dy*dy;};return d(a)<d(b);});
        int n=min<int>(assigned.size(),max(2,int(sqrt(double(assigned.size())))*(strength==2?2:1)));
        for(int i=0;i<n;i++)E.doRemove(assigned[i]);
    } else if(!op.empty()) {
        int a=op[rng()%op.size()];
        if(strength==3){auto v=s.members[a];shuffle(v.begin(),v.end(),rng);for(size_t i=0;i<(v.size()+1)/2;i++)E.doRemove(v[i]);}
        else {
            E.doClose(a);
            if(!closed.empty()) {
                int b=closed[rng()%closed.size()];s.end_defer();
                // Clear only the region covering the new anchor, with a bounded budget.
                vector<pair<double,int>> near;
                for(int x:assigned)if(s.asg[x]>=0){double dx=I.P[x].x-I.P[I.ns+b].x,dy=I.P[x].y-I.P[I.ns+b].y;near.push_back({dx*dx+dy*dy,x});}
                sort(near.begin(),near.end());
                for(auto [d,x]:near){if(!s.cov[I.ns+b] || elapsed()>=deadline)break;E.doRemove(x);}
                E.doOpen(b);
            }
        }
    }
    s.end_defer();
    recreate(E,G,rng,true,5,deadline);repair_sizes(s);s.recompute_psum();
    if(elapsed()<deadline)greedy_fill(s,E,deadline);
    repair_sizes(s);s.recompute_psum();
}
static void research_search(Sol& s,mt19937_64& rng,double deadline,int mode) {
    const Inst& I=*s.I;
    struct State{vector<int>a;vector<char>o;double f;uint64_t h;};
    auto save=[&](){return State{s.asg,s.isopen,s.objective(),search_fingerprint(s)};};
    auto restore=[&](const State& x){s.load_state(x.a,x.o);};
    State current=save(),best=current;
    const double initial_f=current.f;
    vector<State> population{current};
    vector<pair<uint64_t,int>> tabu;
    int iteration=0,stagnation=0,level=1,accepts=0,clones=0,cycles=0;
    double t0=elapsed();
    while(elapsed()<deadline) {
        int idx=mode==4?iteration%4:0;
        if(mode==4)restore(population[min<int>(idx,population.size()-1)]);else restore(current);
        double slice=min(deadline,elapsed()+max(0.03,(deadline-t0)/12));
        int strength=mode==2?level:1+stagnation%4;
        search_shake(s,rng,strength,min(slice,elapsed()+0.25*(slice-elapsed())));
        if(!search_valid(s)){restore(current);stagnation++;iteration++;continue;}
        if(elapsed()<slice)exchange_descent(s,rng,min(slice,elapsed()+0.2*(slice-elapsed())),2);
        if(elapsed()<slice)polish(s,rng,slice,slice,false);
        if(!search_valid(s)){restore(current);stagnation++;iteration++;continue;}
        State next=save();bool improved=next.f>best.f+1e-9;
        if(improved){best=next;stagnation=0;offer(I,s);}else stagnation++;
        bool cycle=false;for(auto [h,expiry]:tabu)if(h==next.h && expiry>iteration)cycle=true;
        cycles+=cycle;
        bool accept=next.f>current.f+1e-9;
        if(mode==1 && stagnation>=4){accept=true;stagnation=0;} // restart the chain
        if(mode==2){if(accept)level=1;else level=level%4+1;}
        if(mode==3)accept=!cycle || improved; // record aspiration, sampled basin move
        if(mode==4) {
            if(idx>=(int)population.size())population.push_back(next);else population[idx]=next;
            if(idx==3) {
                sort(population.begin(),population.end(),[](const State&a,const State&b){return a.f>b.f;});
                // Retain a different office set, or a trajectory differing at >=5% of sites.
                int diverse=-1;
                for(int i=1;i<4;i++){int d=0;for(int x=0;x<I.ns;x++)d+=population[0].a[x]!=population[i].a[x];if(population[0].o!=population[i].o || d>=max(1,I.ns/20)){diverse=i;break;}}
                if(diverse>1)swap(population[1],population[diverse]);
                population[2]=population[0];population[3]=population[1];clones+=2;
            }
            accept=false;
        }
        if(accept){current=next;accepts++;tabu.push_back({next.h,iteration+7});}
        tabu.erase(remove_if(tabu.begin(),tabu.end(),[&](auto e){return e.second<=iteration;}),tabu.end());
        if(tabu.size()>64)tabu.erase(tabu.begin());
        iteration++;
    }
    restore(best);offer(I,s);try_elite(I,s);
    if(getenv("SEARCH_TRACE"))fprintf(stderr,"trace_search mode=%d iterations=%d accepted=%d clones=%d cycles=%d gain=%.9f seconds=%.6f\n",mode,iteration,accepts,clones,cycles,best.f-initial_f,elapsed()-t0);
}
