// Plateau escape research. Include immediately before frozen-v4 lns().
// No runtime file access, no dependencies; every published state still passes offer().
struct EscapeControl {
    Sol& s; const Inst& I; int mode;
    double begin, end, best, last_gain, next_episode, episode_end=0, episode_start=0;
    double plateau, episode, loss_cap, episode_best=0, escape_seconds=0, recovery_seconds=0;
    bool active=false; int strength=1;
    vector<int> ba, ea; vector<char> bo, eo;
    vector<double> history; size_t hist_at=0;
    vector<uint64_t> tabu; uint64_t hash=0;
    long ticks=0, flat_ticks=0, episodes=0, kicks=0, failed_kicks=0, improvements=0,
         return_same=0, improved_episodes=0, accepted=0, tabu_reject=0,
         changed_assignment=0, changed_office=0, changed_hull=0, changed_worker=0;
    vector<vector<Pt>> eh; vector<int> ew;
    double entry_profit=0, entry_cost=0, entry_penalty=0;
    static uint64_t token(uint64_t x) { x+=0x9e3779b97f4a7c15ULL; x=(x^(x>>30))*0xbf58476d1ce4e5b9ULL; x=(x^(x>>27))*0x94d049bb133111ebULL; return x^(x>>31); }
    uint64_t state_hash() const { uint64_t h=0; for(int x=0;x<I.ns;x++) if(s.asg[x]>=0) h^=token((uint64_t)(x+1)*(I.no+1)+s.asg[x]); for(int o=0;o<I.no;o++) if(s.isopen[o])h^=token((uint64_t)(I.ns+1)*(I.no+1)+o); return h; }
    uint64_t trial_hash(const Engine& E) const { uint64_t h=hash; for(const auto& p:E.jr) { if(p.t<2)h^=token((uint64_t)(p.x+1)*(I.no+1)+p.o); else h^=token((uint64_t)(I.ns+1)*(I.no+1)+p.o); } return h; }
    void decompose(double& p,double& c,double& z) const { p=0;c=0;long long lo=LLONG_MAX,hi=LLONG_MIN; for(int o=0;o<I.no;o++)if(s.isopen[o]&&s.size_[o]){c+=I.cost[o];lo=min(lo,s.load[o]);hi=max(hi,s.load[o]);for(int x:s.members[o])p+=I.pr(o,x);}z=hi==LLONG_MIN?0:I.alpha*(hi-lo); }
    EscapeControl(Sol& ss,double finish,double scale):s(ss),I(*ss.I),mode(getenv("ESCAPE_MODE")?atoi(getenv("ESCAPE_MODE")):0),begin(elapsed()),end(finish),best(0),last_gain(begin),next_episode(begin),plateau(0),episode(0),loss_cap(0) {
        if(mode<1||mode>5){mode=0;return;}
        best=s.objective();ba=s.asg;bo=s.isopen;
        double duration=max(0.,end-begin);
        plateau=min(2.,max(.08,.16*duration)); episode=min(.8,max(.06,.10*duration));
        next_episode=begin+plateau;loss_cap=max(1e-8,min(.0075*max(1.,fabs(best)),2.*scale));
        history.assign(64,best);hash=state_hash();tabu.push_back(hash);
        decompose(entry_profit,entry_cost,entry_penalty);
    }
    void observe() {
        if(!mode)return;
        double f=s.objective_fast();
        if(f>best+1e-9*max(1.,fabs(best))) {
            vector<int>w;double checked;
            if(s.greedy_workers(&w)&&verify(I,s.asg,s.isopen,w,&checked)&&checked>best+1e-9*max(1.,fabs(best))){best=checked;ba=s.asg;bo=s.isopen;last_gain=elapsed();improvements++;}
        }
    }
    void record_episode() {
        if(!active)return;
        double now=elapsed();escape_seconds+=now-episode_start;
        if(best>episode_best+1e-9*max(1.,fabs(best))) improved_episodes++;
        else {if(s.asg==ba&&s.isopen==bo)return_same++;strength=min(4,strength+1);}
        if(best>episode_best+1e-9*max(1.,fabs(best)))strength=1;
        for(int x=0;x<I.ns;x++)changed_assignment+=s.asg[x]!=ea[x];
        for(int o=0;o<I.no;o++){changed_office+=s.isopen[o]!=eo[o];bool diff=s.hull[o].size()!=eh[o].size();if(!diff)for(size_t j=0;j<eh[o].size();j++)diff|=s.hull[o][j].x!=eh[o][j].x||s.hull[o][j].y!=eh[o][j].y;changed_hull+=diff;}
        vector<int>w;if(s.greedy_workers(&w)&&w.size()==ew.size())for(size_t j=0;j<w.size();j++)changed_worker+=w[j]!=ew[j];
        active=false;next_episode=now+plateau;
    }
    void restore(Engine& E,Guide& G,double& cur) {s.load_state(ba,bo);E.jr.clear();E.clear_ban();cur=G.val();hash=state_hash();}
    bool tick(Engine& E,Guide& G,mt19937_64& rng,double& cur,double now) {
        if(!mode)return false;
        ticks++;observe();if(now-last_gain>=plateau)flat_ticks++;
        bool changed=false;
        if(active&&now>=episode_end){record_episode();restore(E,G,cur);changed=true;}
        if(mode==4||active||now<next_episode||now-last_gain<plateau||end-now<episode+min(.05,plateau))return changed;
        // At most 30% of the LNS loop can be allocated to escape episodes.
        if(escape_seconds>=.30*(end-begin))return changed;
        active=true;episodes++;episode_start=now;episode_end=min(end-.02,now+episode);episode_best=best;
        ea=s.asg;eo=s.isopen;eh=s.hull;ew.clear();s.greedy_workers(&ew);
        history.assign(64,s.objective_fast());hist_at=0;tabu.clear();tabu.push_back(hash);
        if(mode!=1&&mode!=3&&mode!=5)return changed;
        restore(E,G,cur);kicks++;
        double t=elapsed();size_t mark=E.jr.size();
        if(mode==5){
            GeometryStats gs;
            mt19937_64 kick_rng=rng;
            bool ok=geometry_perturb(s,kick_rng,min(episode_end,t+.35*episode),2,gs);
            bool retained=ok&&s.objective_fast()>=best-loss_cap;
            if(!retained){restore(E,G,cur);failed_kicks++;}
            E.jr.clear();E.clear_ban();cur=G.val();hash=state_hash();
            recovery_seconds+=elapsed()-t;observe();
            if(s.objective_fast()>g_best.load(memory_order_relaxed)+1e-9)offer(I,s);
            double polish_start=elapsed();
            if(retained&&elapsed()<episode_end)polish(s,rng,episode_end,episode_end,true);
            s.recompute_psum();E.jr.clear();E.clear_ban();cur=G.val();hash=state_hash();
            observe();if(s.objective_fast()>g_best.load(memory_order_relaxed)+1e-9)offer(I,s);
            fprintf(stderr,"GEOKICK_POLISH retained=%d seconds=%.9f episode_remaining=%.9f\n",(int)retained,elapsed()-polish_start,episode_end-elapsed());
            fprintf(stderr,"GEOKICK success=%d attempts=%ld accepted=%ld geometry_reject=%ld worker_reject=%ld loss_reject=%ld moved=%ld freed_points=%ld seconds=%.9f\n",(int)ok,gs.attempts,gs.accepted,gs.geometry_reject,gs.worker_reject,gs.loss_reject,gs.moved,gs.freed_points,elapsed()-t);
            return true;
        }
        // Count-compatible small removal: remove the same bounded amount per
        // active office at tight A. No office-set destruction or broad restart.
        vector<int> op;for(int o=0;o<I.no;o++)if(s.isopen[o]&&s.size_[o])op.push_back(o);
        int q=(mode==3?strength:1);if(!op.empty())for(int o:op)q=min(q,max(0,s.size_[o]-1));
        vector<char> removed(I.ns,0); vector<int> target=s.size_;
        for(int o:op){vector<int> mem=s.members[o];shuffle(mem.begin(),mem.end(),rng);for(int j=0;j<q;j++){removed[mem[j]]=1;E.doRemove(mem[j]);}}
        // Do not immediately add the destroyed sites back. Try a bounded set of
        // alternative free sites jointly across offices, including negative
        // support sites when A=0. A partial refill is rolled back as a unit.
        double repair_end=min(episode_end,t+.35*episode);
        for(int o:op)while(s.size_[o]<target[o]&&elapsed()<repair_end){
            vector<pair<double,int>> pool;
            for(int x=0;x<I.ns;x++){if((x&255)==0&&elapsed()>=repair_end)break;if(s.asg[x]<0&&!removed[x]&&I.servable[x])pool.push_back({I.pr(o,x),x});}
            int k=min(24,(int)pool.size());partial_sort(pool.begin(),pool.begin()+k,pool.end(),greater<pair<double,int>>());
            int random_k=min(4,k);shuffle(pool.begin(),pool.begin()+random_k,rng);
            bool added=false;for(int j=0;j<k&&!added&&elapsed()<repair_end;j++)added=E.doAdd(pool[j].second,o);
            if(!added)break;
        }
        if(I.A<=2&&elapsed()<repair_end)level_fill(s,E,repair_end);
        if(elapsed()<repair_end)recreate(E,G,rng,true,5,repair_end);
        bool ok=E.size_viol(-1,-1)==0&&s.greedy_workers(nullptr);
        if(!ok||s.objective_fast()<best-loss_cap){E.undo(mark);failed_kicks++;}
        E.jr.clear();cur=G.val();hash=state_hash();tabu.clear();tabu.push_back(hash);
        recovery_seconds+=elapsed()-t;observe();return true;
    }
    template<class U> bool accept(double d,double T,mt19937_64& rng,U& random,Engine& E) {
        if(!mode)return d>-1e-12||random(rng)<exp(d/max(1e-12,T));
        double f=s.objective_fast();bool yes;
        uint64_t h=0;
        if(mode==3)h=trial_hash(E);
        if(active&&mode==2){double threshold=max(best-loss_cap,history[hist_at]);yes=f>=best-loss_cap&&(f+1e-10>=threshold||d>-1e-12);history[hist_at]=yes?f:history[hist_at];hist_at=(hist_at+1)%history.size();}
        else if(active&&mode==3){bool forbidden=find(tabu.begin(),tabu.end(),h)!=tabu.end();if(forbidden&&f<=best+1e-9){tabu_reject++;yes=false;}else yes=f>=best-loss_cap&&(d>-1e-12||random(rng)<exp(d/max(1e-12,4*T)));}
        else yes=d>-1e-12||random(rng)<exp(d/max(1e-12,T));
        if(yes){accepted++;observe();if(mode==3){hash=h;tabu.push_back(h);if(tabu.size()>12)tabu.erase(tabu.begin());}}
        return yes;
    }
    void resync(){if(mode==3)hash=state_hash();}
    void finish(Engine& E,Guide& G,double& cur) {
        if(!mode)return;observe();record_episode();restore(E,G,cur);
        double p,c,z;decompose(p,c,z);
        fprintf(stderr,"ESCAPE mode=%d seconds=%.6f ticks=%ld plateau_ticks=%ld episodes=%ld kicks=%ld failed_kicks=%ld improvements=%ld improved_episodes=%ld same_max=%ld accepted=%ld tabu_reject=%ld escape_seconds=%.6f recovery_seconds=%.6f changed_assignment=%ld changed_office=%ld changed_hull=%ld changed_worker=%ld gain_profit=%.9f gain_cost=%.9f gain_penalty=%.9f best=%.9f\n",mode,elapsed()-begin,ticks,flat_ticks,episodes,kicks,failed_kicks,improvements,improved_episodes,return_same,accepted,tabu_reject,escape_seconds,recovery_seconds,changed_assignment,changed_office,changed_hull,changed_worker,p-entry_profit,entry_cost-c,entry_penalty-z,best);
    }
};
