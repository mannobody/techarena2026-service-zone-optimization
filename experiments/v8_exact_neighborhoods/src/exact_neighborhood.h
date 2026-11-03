// Conditional full-domain B&B. Atomic reconstruction permits office-count changes,
// crossings without input-point conflicts, coupled count/load/worker exchanges.
// No external solver, disk state, envelopes, warm input, or instance-ID branches.
static bool xn_workers(Sol&s,vector<int>&out,double end,bool&timeout){
    if(s.greedy_workers(&out))return true;
    const Inst&I=*s.I;vector<int>wof(I.nw,-1);vector<char>have((size_t)I.no*I.nsk,0);
    long nodes=0;
    auto dfs=[&](auto&&self)->bool{
        if((++nodes&31)==0&&elapsed()>=end){timeout=true;return false;}
        vector<int>avail(I.nsk,0),demand(I.nsk,0);int bo=-1,bk=-1,bn=INT_MAX;
        for(int w=0;w<I.nw;w++)if(wof[w]<0)for(int k:I.wskills[w])avail[k]++;
        for(int o=0;o<I.no;o++)for(int k=0;k<I.nsk;k++)if(s.need[o][k]&&!have[(size_t)o*I.nsk+k]){
            demand[k]++;if(avail[k]<bn){bo=o;bk=k;bn=avail[k];}}
        if(bo<0){out=wof;return true;}
        for(int k=0;k<I.nsk;k++)if(demand[k]>avail[k])return false;
        vector<int>choices;for(int w=0;w<I.nw;w++)if(wof[w]<0&&I.wmask[w][bk]){
            bool dup=false;for(int v:choices)if(I.wmask[v]==I.wmask[w]){dup=true;break;}
            if(!dup)choices.push_back(w);}
        stable_sort(choices.begin(),choices.end(),[&](int a,int b){int ga=0,gb=0;
            for(int k=0;k<I.nsk;k++)if(s.need[bo][k]&&!have[(size_t)bo*I.nsk+k]){ga+=I.wmask[a][k];gb+=I.wmask[b][k];}return ga>gb;});
        for(int w:choices){auto save=have;wof[w]=bo;for(int k:I.wskills[w])have[(size_t)bo*I.nsk+k]=1;
            if(self(self))return true;have=move(save);wof[w]=-1;if(timeout)return false;}
        return false;
    };return dfs(dfs);
}

static bool xn_offer(const Inst&I,Sol&s,const vector<int>&w){
    double val=0;if(!verify(I,s.asg,s.isopen,w,&val))return false;
    lock_guard<mutex>lk(g_best_mx);if(val<=g_best.load()+1e-9)return false;
    g_best.store(val);g_best_asg=s.asg;g_best_open=s.isopen;
    publish(serialize(I,s.asg,s.isopen,w));push_elite(val,s.asg,s.isopen);return true;
}

struct XNStats{long nodes=0,leaves=0,masks=0,geo=0,wfail=0;bool complete=true;double gain=0,seconds=0;};
struct XNSearch{
    const Inst&I;Sol work;Engine E;vector<int>xs,ops,base,best,certificate;
    vector<char>baseopen,bestopen;vector<vector<int>>dom,reach;
    vector<vector<long long>>tasks;vector<double>suf;
    double end,bestval,cost=0;XNStats stats;
    XNSearch(const Sol&s,vector<int>sites,vector<int>offices,double deadline):
        I(*s.I),work(s),E(work),xs(move(sites)),ops(move(offices)),base(s.asg),best(s.asg),
        baseopen(s.isopen),bestopen(s.isopen),end(deadline),bestval(s.objective()){
        stable_sort(xs.begin(),xs.end(),[&](int a,int b){double pa=0,pb=0;
            for(int o:ops){pa=max(pa,I.pr(o,a));pb=max(pb,I.pr(o,b));}return pa>pb;});
        for(int x:xs)base[x]=-1;
    }
    bool expired(){if(elapsed()>=end){stats.complete=false;return true;}return false;}
    double bound(int j){
        int maxcnt=0,minhi=INT_MAX;long long maxload=0,minloadhi=LLONG_MAX;
        for(int o=0;o<I.no;o++)if(work.isopen[o]){
            int hi=min(I.maxsize[o],work.size_[o]+reach[j][o]);if(hi<1)return NEG;
            maxcnt=max(maxcnt,max(1,work.size_[o]));minhi=min(minhi,hi);
            maxload=max(maxload,work.load[o]);minloadhi=min(minloadhi,work.load[o]+tasks[j][o]);
        }
        if(minhi!=INT_MAX&&(long long)maxcnt>minhi+I.A)return NEG;
        double penalty=minloadhi==LLONG_MAX?0:I.alpha*(double)max(0LL,maxload-minloadhi);
        return work.psum+suf[j]-cost-penalty;
    }
    void dfs(int j){
        stats.nodes++;if(expired())return;
        if(bound(j)<=bestval+1e-9)return;
        if(j==(int)xs.size()){
            stats.leaves++;for(int o=0;o<I.no;o++)if(work.isopen[o]&&!work.size_[o])return;
            if(E.size_viol(-1,-1))return;
            double val=work.objective();if(val<=bestval+1e-9)return;
            vector<int>w;bool timed=false;if(!xn_workers(work,w,end,timed)){stats.wfail++;if(timed)stats.complete=false;return;}
            if(!verify(I,work.asg,work.isopen,w,&val))return;
            bestval=val;best=work.asg;bestopen=work.isopen;certificate=move(w);return;
        }
        int x=xs[j];
        for(int o:dom[j]){
            if(o<0){dfs(j+1);}else if(E.doAdd(x,o)){dfs(j+1);work.remove_site(x);}else stats.geo++;
            if(!stats.complete)return;
        }
    }
    bool run(Sol&result,int mode){
        double start=elapsed(),before=result.objective();
        if(I.alpha<0||any_of(I.cost.begin(),I.cost.end(),[](double c){return c<0;}))return false;
        vector<int>toggle;vector<char>forced(I.no,0);
        for(int x:base)if(x>=0)forced[x]=1;
        for(int o:ops)if(!forced[o])toggle.push_back(o);
        if(toggle.size()>10)return false;
        uint64_t oldmask=0;for(size_t i=0;i<toggle.size();i++)if(baseopen[toggle[i]])oldmask|=1ULL<<i;
        // Incumbent mask first, then alternatives; mode1 fixes the active offices.
        vector<uint64_t>masks{oldmask};if(mode!=1)for(uint64_t m=0;m<(1ULL<<toggle.size());m++)if(m!=oldmask)masks.push_back(m);
        for(uint64_t mask:masks){
            if(expired())break;stats.masks++;vector<char>op=baseopen;
            for(int o:ops)op[o]=forced[o];for(size_t i=0;i<toggle.size();i++)op[toggle[i]]=(mask>>i)&1;
            work.load_state(base,op);if(expired())break;
            bool ok=true;for(int c:work.cov)if(c>1){ok=false;break;}if(!ok)continue;
            cost=0;for(int o=0;o<I.no;o++)if(op[o])cost+=I.cost[o];
            dom.assign(xs.size(),{});vector<Pt>h;
            for(size_t j=0;j<xs.size();j++){
                int x=xs[j];for(int o:ops)if(op[o]&&I.maxsize[o]>work.size_[o]&&E.can_add_skills(x,o)&&work.geo_ok(x,o,h))dom[j].push_back(o);
                stable_sort(dom[j].begin(),dom[j].end(),[&](int a,int b){return I.pr(a,x)>I.pr(b,x);});dom[j].push_back(-1);
                if((j&7)==0&&expired())break;
            }
            if(!stats.complete)break;int n=xs.size();suf.assign(n+1,0);reach.assign(n+1,vector<int>(I.no));tasks.assign(n+1,vector<long long>(I.no));
            for(int j=n-1;j>=0;j--){double p=0;reach[j]=reach[j+1];tasks[j]=tasks[j+1];
                for(int o:dom[j])if(o>=0){p=max(p,I.pr(o,xs[j]));reach[j][o]++;tasks[j][o]+=I.ntask[xs[j]];}suf[j]=suf[j+1]+p;}
            dfs(0);if(!stats.complete)break;
        }
        bool win=bestval>before+1e-9;
        if(win){result.load_state(best,bestopen);result.recompute_psum();xn_offer(I,result,certificate);}
        stats.gain=win?bestval-before:0;stats.seconds=elapsed()-start;return win;
    }
};

// Select boundary/support layers for geometry, whole small zones for structural
// closure, and a closed office for joint opening. Retain full domains within ops.
static bool xn_move(Sol&s,mt19937_64&rng,double end,int mode,int q,XNStats*report=nullptr){
    const Inst&I=*s.I;if(elapsed()>=end||I.no==0)return false;
    vector<int>ops,xs,active;for(int o=0;o<I.no;o++)if(s.isopen[o]&&s.size_[o])active.push_back(o);
    if(I.ns<=10&&I.no<=5){ops.resize(I.no);iota(ops.begin(),ops.end(),0);xs.resize(I.ns);iota(xs.begin(),xs.end(),0);}
    else{
        if(active.empty())return false;
        int a=active[rng()%active.size()];ops.push_back(a);
        vector<pair<double,int>>near;for(int o=0;o<I.no;o++)if(o!=a&&(mode!=1||s.isopen[o])){
            double dx=I.P[I.ns+o].x-I.P[I.ns+a].x,dy=I.P[I.ns+o].y-I.P[I.ns+a].y;near.push_back({dx*dx+dy*dy,o});}
        sort(near.begin(),near.end());
        if(!near.empty())ops.push_back(near[rng()%min<size_t>(3,near.size())].second);
        if(mode!=1&&ops.size()<3)for(auto p:near)if(find(ops.begin(),ops.end(),p.second)==ops.end()){ops.push_back(p.second);break;}
        vector<char>target(I.no,0),chosen(I.ns,0);for(int o:ops)target[o]=1;
        auto add=[&](int x){if(!chosen[x]&&(int)xs.size()<q){xs.push_back(x);chosen[x]=1;}};
        if(mode!=1){vector<int>small=ops;sort(small.begin(),small.end(),[&](int a,int b){return s.size_[a]<s.size_[b];});
            for(int o:small)if(s.size_[o]&&s.size_[o]<=q/2){for(int x:s.members[o])add(x);break;}}
        Pt anchor=I.P[I.ns+ops.back()];
        if(mode==1&&!s.members[a].empty())anchor=I.P[s.members[a][rng()%s.members[a].size()]];
        vector<pair<double,int>>rank;
        for(int x=0;x<I.ns;x++){
            if((x&127)==0&&elapsed()>=end)return false;
            if(!I.servable[x]||(s.asg[x]>=0&&!target[s.asg[x]]))continue;
            double dx=I.P[x].x-anchor.x,dy=I.P[x].y-anchor.y,d=dx*dx+dy*dy;
            if(s.asg[x]>=0)for(Pt p:s.hull[s.asg[x]])if(pteq(p,I.P[x])){d*=.12;break;}
            rank.push_back({d,x});
        }
        sort(rank.begin(),rank.end());int free=0;
        for(auto p:rank){if(s.asg[p.second]<0&&free>=q/3)continue;if(s.asg[p.second]<0)free++;add(p.second);if((int)xs.size()>=q)break;}
    }
    if(xs.empty()||elapsed()>=end)return false;
    XNSearch search(s,xs,ops,end);bool win=search.run(s,mode);if(report)*report=search.stats;
    if(DBG&&search.stats.nodes)fprintf(stderr,"XN mode=%d q=%zu ops=%zu masks=%ld nodes=%ld leaves=%ld complete=%d geo=%ld wfail=%ld gain=%.9f seconds=%.6f\n",
        mode,xs.size(),ops.size(),search.stats.masks,search.stats.nodes,search.stats.leaves,search.stats.complete,search.stats.geo,search.stats.wfail,search.stats.gain,search.stats.seconds);
    return win;
}

static void xn_finish(const Inst&I,double limit){
    int mode=getenv("XN_MODE")?atoi(getenv("XN_MODE")):3;if(mode<=0)return;
    double end=limit-max(.25,.002*limit);if(elapsed()>=end)return;
    vector<int>a;vector<char>op;{lock_guard<mutex>lk(g_best_mx);a=g_best_asg;op=g_best_open;}
    if(a.empty())return;Sol s;s.init(I);s.load_state(a,op);g_wdfs_deadline=end;
    uint64_t seed=getenv("SEED")?strtoull(getenv("SEED"),nullptr,10):0;mt19937_64 rng(0xE8AC7ULL+seed);
    int q=getenv("XN_Q")?max(4,min(18,atoi(getenv("XN_Q")))):12;int calls=0;
    // Budget is inside the original TL. Half the remaining tail remains for native boundary.
    double stop=min(end,elapsed()+min(.8,.5*(end-elapsed())));
    while(elapsed()<stop){int use=mode==3?(++calls%2?1:2):mode;XNStats st;
        if(mode>=4){xn_packets(s,rng,min(stop,elapsed()+.04));continue;}
        xn_move(s,rng,min(stop,elapsed()+.04),use,q,&st);if(!st.nodes)break;}
}
