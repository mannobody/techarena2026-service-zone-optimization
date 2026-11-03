// Research: joint site-count / task-load selection inside fixed convex hulls.
// Staff certificate stays fixed; offices may close. No new territory is created.
// Exact if the whole bounded DP/window enumeration completes; monotone otherwise.
static bool joint_territory_select(Sol& s, double deadline) {
    const Inst& I=*s.I;
    if(elapsed()>=deadline)return false;
    vector<int> staff;
    if(!s.greedy_workers(&staff))return false;
    vector<vector<char>> have(I.no,vector<char>(I.nsk,0));
    for(int w=0;w<I.nw;w++)if(staff[w]>=0)
        for(int k=0;k<I.nsk;k++)have[staff[w]][k]|=I.wmask[w][k];
    struct Table {
        int o=0,C=0,W=0,stride=0;size_t states=0,words=0;
        vector<int> pool;vector<double> f;vector<uint64_t> take;
    };
    vector<Table> tabs;
    long long work=0;int maxC=0,maxW=0;
    for(int o=0;o<I.no;o++)if(s.isopen[o]&&s.size_[o]>0){
        if(elapsed()>=deadline)return false;
        Table t;t.o=o;
        int sum=0,mxt=0;
        for(int x=0;x<I.ns;x++){
            if((x&127)==0&&elapsed()>=deadline)return false;
            if(!I.servable[x]||!s.incov[(size_t)o*s.np+x])continue;
            bool ok=true;for(int k:I.skillset[x])if(!have[o][k]){ok=false;break;}
            if(ok){t.pool.push_back(x);sum+=I.ntask[x];mxt=max(mxt,I.ntask[x]);}
        }
        t.C=min(I.maxsize[o],(int)t.pool.size());
        t.W=(int)min((long long)sum,(long long)t.C*mxt);
        t.stride=t.W+1;t.states=(size_t)(t.C+1)*t.stride;
        work+=(long long)t.states*t.pool.size();
        if(work>30000000LL)return false;
        maxC=max(maxC,t.C);maxW=max(maxW,t.W);tabs.push_back(move(t));
    }
    int K=tabs.size();if(!K)return false;
    // Fixed guards are work/memory bounds, independent of any test identity.
    if((long double)maxC*(maxW+1)*(maxW+1)*K>80000000.L)return false;
    for(auto&t:tabs){
        t.f.assign(t.states,NEG);t.f[0]=0.;t.words=(t.states+63)/64;
        t.take.assign(t.words*t.pool.size(),0);
        for(size_t i=0;i<t.pool.size();i++){
            if(elapsed()>=deadline)return false;
            int x=t.pool[i],w=I.ntask[x];double p=I.pr(t.o,x);
            uint64_t* bits=t.take.data()+i*t.words;
            for(int c=min((int)i+1,t.C);c>=1;c--)
                for(int l=t.W;l>=w;l--){
                    size_t pos=(size_t)c*t.stride+l;
                    double prev=t.f[pos-t.stride-w];
                    if(prev>NEG/2&&prev+p>t.f[pos]+1e-12){
                        t.f[pos]=prev+p;bits[pos>>6]|=1ULL<<(pos&63);
                    }
                }
        }
    }
    double before=s.objective(),best=max(0.,before);
    vector<int> bestCount(K,0),bestLoad(K,0);
    bool found=before<0.;
    vector<vector<double>> g(K,vector<double>(maxW+1,NEG));
    vector<vector<int>> gc(K,vector<int>(maxW+1,0));
    vector<double> running(K);
    vector<int> rc(K),rl(K);
    bool complete=true;
    for(int lowerCount=1;lowerCount<=maxC;lowerCount++){
        if(elapsed()>=deadline){complete=false;break;}
        for(int b=0;b<K;b++){
            auto&t=tabs[b];fill(g[b].begin(),g[b].end(),NEG);
            int upper=(int)min((long long)t.C,(long long)lowerCount+I.A);
            for(int c=lowerCount;c<=upper;c++)for(int l=0;l<=t.W;l++){
                double val=t.f[(size_t)c*t.stride+l];
                if(val>g[b][l]){g[b][l]=val;gc[b][l]=c;}
            }
        }
        for(int lo=0;lo<=maxW;lo++){
            if((lo&7)==0&&elapsed()>=deadline){complete=false;break;}
            fill(running.begin(),running.end(),NEG);
            fill(rc.begin(),rc.end(),0);fill(rl.begin(),rl.end(),0);
            for(int hi=lo;hi<=maxW;hi++){
                if((hi&127)==0&&elapsed()>=deadline){complete=false;break;}
                double value=-I.alpha*(hi-lo);
                for(int b=0;b<K;b++){
                    if(g[b][hi]>running[b]){
                        running[b]=g[b][hi];rc[b]=gc[b][hi];rl[b]=hi;
                    }
                    double net=running[b]-I.cost[tabs[b].o];
                    if(net>0.)value+=net;
                }
                if(value>best+1e-9){
                    best=value;found=true;
                    for(int b=0;b<K;b++){
                        bool keep=running[b]-I.cost[tabs[b].o]>0.;
                        bestCount[b]=keep?rc[b]:0;bestLoad[b]=keep?rl[b]:0;
                    }
                }
            }
            if(!complete)break;
        }
        if(!complete)break;
    }
    if(!found||elapsed()>=deadline)return false;
    vector<int>a(I.ns,-1);vector<char>op(I.no,0);
    for(int b=0;b<K;b++){
        auto&t=tabs[b];int c=bestCount[b],l=bestLoad[b];if(!c)continue;
        op[t.o]=1;
        for(int i=(int)t.pool.size()-1;i>=0;i--){
            size_t pos=(size_t)c*t.stride+l;
            const uint64_t* bits=t.take.data()+(size_t)i*t.words;
            if(bits[pos>>6]>>(pos&63)&1ULL){
                int x=t.pool[i];if(a[x]>=0)return false;
                a[x]=t.o;c--;l-=I.ntask[x];
            }
        }
        if(c||l)return false;
    }
    if(elapsed()>=deadline)return false;
    vector<int> old=s.asg;vector<char> opened=s.isopen;
    s.load_state(a,op);s.recompute_psum();Engine E(s);
    bool valid=E.size_viol(-1,-1)==0;
    for(int q:s.cov)if(q>1){valid=false;break;}
    if(!valid||s.objective()<=before+1e-9){s.load_state(old,opened);return false;}
    if(getenv("JOINT_TRACE"))fprintf(stderr,"joint_territory before=%.9f after=%.9f complete=%d work=%lld\n",before,s.objective(),complete,work);
    return true;
}

static void joint_territory_finish(const Inst&I,double limit){
    if(!getenv("JOINT_TERRITORY")||!atoi(getenv("JOINT_TERRITORY")))return;
    double end=limit-max(.25,.002*limit);
    if(elapsed()>=end||g_best.load()<=0)return;
    double budget=getenv("JOINT_SECONDS")?max(0.,atof(getenv("JOINT_SECONDS"))):1.;
    end=min(end,elapsed()+budget);
    vector<int>a;vector<char>op;{lock_guard<mutex>lk(g_best_mx);a=g_best_asg;op=g_best_open;}
    if(a.empty())return;
    Sol s;s.init(I);s.load_state(a,op);g_wdfs_deadline=end;
    if(joint_territory_select(s,end))offer(I,s);
}
