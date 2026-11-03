// Whole-zone structural templates. Enumeration is over a finite pattern family,
// NOT exact optimization over arbitrary assignments. Unlike q-site B&B this can
// open a large zone at A=0 in one atomic move; all workers are reassigned jointly.
static bool xn_packets(Sol&s,mt19937_64&rng,double end){
    const Inst&I=*s.I;if(elapsed()>=end||I.no<2)return false;
    vector<int>active;for(int o=0;o<I.no;o++)if(s.isopen[o]&&s.size_[o])active.push_back(o);
    if(active.empty())return false;
    int a=active[rng()%active.size()];vector<int>ops{a};vector<pair<double,int>>near;
    for(int o=0;o<I.no;o++)if(o!=a){double dx=I.P[I.ns+o].x-I.P[I.ns+a].x,dy=I.P[I.ns+o].y-I.P[I.ns+a].y;near.push_back({dx*dx+dy*dy,o});}
    sort(near.begin(),near.end());
    for(auto p:near)if(!s.isopen[p.second]){ops.push_back(p.second);break;}
    for(auto p:near)if(s.isopen[p.second]&&ops.size()<3){ops.push_back(p.second);break;}
    if(ops.size()<2)ops.push_back(near.front().second);
    vector<char>target(I.no,0);for(int o:ops)target[o]=1;
    vector<int>base=s.asg,pool;vector<char>baseop=s.isopen;
    for(int o:ops)baseop[o]=0;
    for(int x=0;x<I.ns;x++){
        if((x&127)==0&&elapsed()>=end)return false;
        if(s.asg[x]>=0&&target[s.asg[x]]){base[x]=-1;pool.push_back(x);}
        else if(s.asg[x]<0&&I.servable[x]){
            bool external=false;for(int o=0;o<I.no;o++)if(!target[o]&&s.isopen[o]&&s.incov[(size_t)o*s.np+x]){external=true;break;}
            if(!external)pool.push_back(x);}
    }
    int extmin=INT_MAX,extmax=0;for(int o=0;o<I.no;o++)if(baseop[o]){extmin=min(extmin,s.size_[o]);extmax=max(extmax,s.size_[o]);}
    auto saved=s.asg;auto savedop=s.isopen;double before=s.objective(),best=before;
    vector<int>bestasg;vector<char>bestop;vector<int>bestw;long trials=0,geofail=0,wfail=0,valid=0;
    auto eval=[&](const vector<int>&assign,const vector<char>&op){
        if(elapsed()>=end)return;trials++;
        vector<int>cnt(I.no,0);vector<long long>ld(I.no,0);double profit=0,cost=0;
        for(int x=0;x<I.ns;x++){if((x&255)==0&&elapsed()>=end)return;int o=assign[x];if(o>=0){cnt[o]++;ld[o]+=I.ntask[x];profit+=I.pr(o,x);}}
        int cmin=INT_MAX,cmax=0;long long lmin=LLONG_MAX,lmax=0;
        for(int o=0;o<I.no;o++)if(op[o]){if(!cnt[o]||cnt[o]>I.maxsize[o])return;cmin=min(cmin,cnt[o]);cmax=max(cmax,cnt[o]);lmin=min(lmin,ld[o]);lmax=max(lmax,ld[o]);cost+=I.cost[o];}
        if((long long)cmax-cmin>I.A)return;
        double value=profit-cost-I.alpha*(lmin==LLONG_MAX?0:lmax-lmin);if(value<=best+1e-9)return;
        Sol trial;trial.init(I);trial.load_state(assign,op);if(elapsed()>=end)return;
        for(int c:trial.cov)if(c>1){geofail++;return;}
        vector<int>w;bool timed=false;if(!xn_workers(trial,w,end,timed)){wfail++;return;}
        if(!verify(I,trial.asg,trial.isopen,w,&value)){geofail++;return;}
        valid++;if(value>best+1e-9){best=value;bestasg=assign;bestop=op;bestw=move(w);}
    };
    for(unsigned mask=1;mask<(1U<<ops.size())&&elapsed()<end;mask++){
        vector<int>dest;auto op=baseop;for(size_t j=0;j<ops.size();j++)if(mask>>j&1){dest.push_back(ops[j]);op[ops[j]]=1;}
        bool blocked=false;for(int o:dest)for(int p=0;p<I.no;p++)if(baseop[p]&&s.incov[(size_t)p*s.np+I.ns+o])blocked=true;
        if(blocked)continue;
        int lower=extmin==INT_MAX?1:max(1,(int)max(0LL,(long long)extmax-I.A));
        int upper=pool.size()/dest.size();for(int o:dest)upper=min(upper,I.maxsize[o]);
        if(extmin!=INT_MAX)upper=min((long long)upper,(long long)extmin+I.A);
        if(upper<lower)continue;
        // Road-preference quotas; different office orders permit coupled changes.
        vector<int>order=dest;sort(order.begin(),order.end());
        do{
            if(elapsed()>=end)break;
            vector<int>ks{upper,lower};for(int o:dest)if(s.size_[o]>=lower&&s.size_[o]<=upper)ks.push_back(s.size_[o]);
            sort(ks.begin(),ks.end());ks.erase(unique(ks.begin(),ks.end()),ks.end());
            for(int k:ks){
                auto assign=base;vector<char>used(I.ns,0);bool enough=true;
                for(int o:order){if(elapsed()>=end){enough=false;break;}vector<pair<double,int>>rank;
                    for(int x:pool)if(!used[x])rank.push_back({I.pr(o,x),x});
                    int take=min(k,(int)rank.size());partial_sort(rank.begin(),rank.begin()+take,rank.end(),greater<pair<double,int>>());
                    if(take<k){enough=false;break;}for(int j=0;j<k;j++){assign[rank[j].second]=o;used[rank[j].second]=1;}}
                if(enough)eval(assign,op);
            }
        }while(next_permutation(order.begin(),order.end())&&elapsed()<end);
        // Coordinate cells are one template, not a validity rule. Road template
        // above is allowed to cross whenever no input point is doubly covered.
        if(elapsed()>=end)break;vector<vector<int>>cell(I.no);
        for(int x:pool){int bo=-1;double bd=1e300;
            for(int o:dest){double dx=I.P[x].x-I.P[I.ns+o].x,dy=I.P[x].y-I.P[I.ns+o].y,d=dx*dx+dy*dy;if(d<bd){bd=d;bo=o;}}
            if(bo>=0)cell[bo].push_back(x);}
        int k=upper;for(int o:dest)k=min(k,(int)cell[o].size());
        if(k>=lower){auto assign=base;for(int o:dest){auto&v=cell[o];sort(v.begin(),v.end(),[&](int x,int y){return I.pr(o,x)>I.pr(o,y);});for(int j=0;j<k;j++)assign[v[j]]=o;}eval(assign,op);}
    }
    bool win=best>before+1e-9;
    if(win){s.load_state(bestasg,bestop);s.recompute_psum();xn_offer(I,s,bestw);}
    if(DBG)fprintf(stderr,"XNPACKET trials=%ld valid=%ld geofail=%ld wfail=%ld offices_before=%zu offices_after=%ld changed=%ld gain=%.9f\n",
        trials,valid,geofail,wfail,active.size(),count(s.isopen.begin(),s.isopen.end(),1),
        (long)inner_product(saved.begin(),saved.end(),s.asg.begin(),0L,plus<long>(),not_equal_to<int>()),best-before);
    return win;
}
