// Native bounded reconstruction: fixed nonempty office cores, free boundary sites.
// All point-footprints use the incumbent solver's conservative geometry predicates.
struct BoundaryStats { long calls=0,nodes=0,pruned=0,geo=0,leaves=0,wfail=0,complete=0,wins=0; double gain=0; };
static thread_local BoundaryStats boundary_stats;

struct BoundarySearch {
    Sol& s; const Inst& I; Engine E;
    vector<int> xs,ops,old,best; vector<vector<int>> dom;
    vector<double> suf; vector<vector<int>> reach;
    vector<vector<long long>> tasks;
    double deadline,bestval,cost=0; bool stopped=false; int strong;
    BoundarySearch(Sol& v,vector<int> sites,vector<int> offices,double end,int st=1):
        s(v),I(*v.I),E(v),xs(move(sites)),ops(move(offices)),deadline(end),strong(st) {
        E.rec=true; bestval=s.objective();
        // Expensive decisions first: geometry and count constraints then propagate early.
        stable_sort(xs.begin(),xs.end(),[&](int a,int b){
            double va=0,vb=0;for(int o:ops){va=max(va,I.pr(o,a));vb=max(vb,I.pr(o,b));}
            return va>vb;
        });
        for(int x:xs){old.push_back(s.asg[x]);E.doRemove(x);} best=old;
        // At least one site per incumbent office remains: opening costs are constant.
        for(int o=0;o<I.no;o++)if(s.isopen[o]&&s.size_[o])cost+=I.cost[o];
        dom.resize(xs.size()); vector<Pt> h;
        for(size_t j=0;j<xs.size();j++) {
            int x=xs[j];
            for(int o:ops)if(E.can_add_skills(x,o)&&s.size_[o]<I.maxsize[o]&&s.geo_ok(x,o,h))dom[j].push_back(o);
            sort(dom[j].begin(),dom[j].end(),[&](int a,int b){return I.pr(a,x)>I.pr(b,x);});
            dom[j].push_back(-1);
        }
        int n=xs.size();suf.assign(n+1,0);reach.assign(n+1,vector<int>(I.no,0));tasks.assign(n+1,vector<long long>(I.no,0));
        for(int j=n-1;j>=0;j--){double p=0;reach[j]=reach[j+1];tasks[j]=tasks[j+1];
            for(int o:dom[j])if(o>=0){p=max(p,I.pr(o,xs[j]));reach[j][o]++;tasks[j][o]+=I.ntask[xs[j]];}
            suf[j]=suf[j+1]+p;
        }
        E.jr.clear();
    }
    double bound(int j) {
        long long maxlo=0,minhi=LLONG_MAX;int maxcnt=0,mincnt=INT_MAX;
        for(int o=0;o<I.no;o++)if(s.isopen[o]&&s.size_[o]){
            maxlo=max(maxlo,s.load[o]);minhi=min(minhi,s.load[o]+tasks[j][o]);
            maxcnt=max(maxcnt,s.size_[o]);mincnt=min(mincnt,min(I.maxsize[o],s.size_[o]+reach[j][o]));
        }
        if((long long)maxcnt>mincnt+I.A)return NEG;
        double extra=suf[j];
        if(strong){ // capacity relaxation: allow same site to earn in several offices, safely optimistic
            double capextra=0;
            for(int o:ops){vector<double> p;for(int k=j;k<(int)xs.size();k++)
                if(find(dom[k].begin(),dom[k].end(),o)!=dom[k].end()&&I.pr(o,xs[k])>0)p.push_back(I.pr(o,xs[k]));
                sort(p.rbegin(),p.rend());int cap=I.maxsize[o]-s.size_[o];
                for(int k=0;k<min(cap,(int)p.size());k++)capextra+=p[k];}
            extra=min(extra,capextra);
        }
        return s.psum+extra-cost-I.alpha*(double)max(0LL,maxlo-minhi);
    }
    bool expired(){if(elapsed()>=deadline){stopped=true;return true;}return false;}
    void leaf(){
        boundary_stats.leaves++; if(E.size_viol(-1,-1))return;
        double val=s.objective_fast();if(val<=bestval+1e-7*max(1.,fabs(bestval)))return;
        if(!s.greedy_workers(nullptr)){boundary_stats.wfail++;return;}
        bestval=val;for(size_t k=0;k<xs.size();k++)best[k]=s.asg[xs[k]];
    }
    void dfs(int j){
        boundary_stats.nodes++;if(expired())return;
        if(bound(j)<=bestval+1e-9){boundary_stats.pruned++;return;}
        if(j==(int)xs.size()){leaf();return;}
        for(int o:dom[j]){size_t mark=E.jr.size();
            if(o<0||E.doAdd(xs[j],o)){dfs(j+1);E.undo(mark);}else boundary_stats.geo++;
            if(stopped)return;
        }
    }
    void beam(int width,bool diverse,bool adaptive=false){
        struct State{vector<int> path;double ub;uint64_t profile;};
        vector<State> beam{{{},bound(0),0}};
        for(int j=0;j<(int)xs.size()&&!beam.empty();j++){
            vector<State> next;
            for(const auto& st:beam){if(expired())break;size_t root=E.jr.size();bool ok=true;
                for(int k=0;k<j;k++)if(st.path[k]>=0&&!E.doAdd(xs[k],st.path[k])){ok=false;break;}
                if(ok)for(int o:dom[j]){
                    if(expired())break;boundary_stats.nodes++;size_t mark=E.jr.size();
                    if(o<0||E.doAdd(xs[j],o)){
                        double ub=bound(j+1);
                        if(ub>bestval+1e-9){
                            if(j+1==(int)xs.size())leaf();
                            else{auto path=st.path;path.push_back(o);uint64_t hash=0;
                                for(int p:ops)hash=(hash*1000003ULL)^((uint64_t)s.size_[p]*7919ULL+(uint64_t)s.load[p]);
                                next.push_back({move(path),ub,hash});}
                        }else boundary_stats.pruned++;
                        E.undo(mark);
                    }else boundary_stats.geo++;
                }
                E.undo(root);
            }
            if(stopped)break;
            sort(next.begin(),next.end(),[](const State&a,const State&b){return a.ub>b.ub;});
            if(adaptive){
                set<uint64_t> unique;for(const auto&v:next)unique.insert(v.profile);
                width=max(16,min(128,(int)unique.size()*2));
            }
            beam.clear();vector<char> used(next.size(),0);set<uint64_t> profiles;
            if(diverse)for(size_t k=0;k<next.size()&&(int)beam.size()<width/2;k++)
                if(profiles.insert(next[k].profile).second){beam.push_back(next[k]);used[k]=1;}
            for(size_t k=0;k<next.size()&&(int)beam.size()<width;k++)if(!used[k])beam.push_back(move(next[k]));
        }
    }
    bool finish(){
        double oldval=0; // restore with force_add; no floating accumulation survives a call
        for(size_t k=0;k<xs.size();k++)if(old[k]>=0)s.force_add(xs[k],old[k]);
        s.recompute_psum();oldval=s.objective();
        if(bestval>oldval+1e-7*max(1.,fabs(oldval))){
            auto saved=s.asg;auto opened=s.isopen;
            for(int x:xs)s.remove_site(x);
            for(size_t k=0;k<xs.size();k++)if(best[k]>=0)s.force_add(xs[k],best[k]);
            s.recompute_psum();vector<int>w;double val=0;
            if(!s.greedy_workers(&w)||!verify(I,s.asg,s.isopen,w,&val)||val<=oldval+1e-9){s.load_state(saved,opened);return false;}
            boundary_stats.wins++;boundary_stats.gain+=val-oldval;return true;
        }
        return false;
    }
};

static bool boundary_move(Sol&s,mt19937_64&rng,double end,int method=1,int style=0,int q=12){
    const Inst&I=*s.I;if(elapsed()>=end)return false;
    vector<int>active;for(int o=0;o<I.no;o++)if(s.isopen[o]&&s.size_[o]>1)active.push_back(o);
    if(active.size()<2)return false;
    int a=active[rng()%active.size()];int anchor=s.members[a][rng()%s.members[a].size()];
    // Alternate geometric proximity and road opportunity; geometry remains in original coordinates.
    if(style&&rng()%2){vector<pair<double,int>>v;for(int x=0;x<I.ns;x++)if(I.servable[x]&&(s.asg[x]<0||s.asg[x]!=a)){
        double gain=I.pr(a,x)-(s.asg[x]<0?0:I.pr(s.asg[x],x));if(gain>0)v.push_back({gain,x});}
        sort(v.rbegin(),v.rend());if(!v.empty())anchor=v[rng()%min<size_t>(16,v.size())].second;
    }
    vector<pair<double,int>>near;
    for(int o:active)if(o!=a){double d=1e300;
        for(int x:s.members[o]){double dx=I.P[x].x-I.P[anchor].x,dy=I.P[x].y-I.P[anchor].y;d=min(d,dx*dx+dy*dy);}
        near.push_back({d,o});}
    sort(near.begin(),near.end());vector<int>ops{a,near[rng()%min<size_t>(2,near.size())].second};
    if(rng()%3==0&&near.size()>1)for(auto e:near)if(e.second!=ops[1]){ops.push_back(e.second);break;}
    vector<char>target(I.no,0);for(int o:ops)target[o]=1;
    vector<pair<double,int>>rank;
    for(int x=0;x<I.ns;x++)if(I.servable[x]&&(s.asg[x]<0||target[s.asg[x]])){
        double dx=I.P[x].x-I.P[anchor].x,dy=I.P[x].y-I.P[anchor].y;double d=dx*dx+dy*dy;
        // Support-focused variant prioritizes removable hull vertices near the opportunity.
        if(style&&s.asg[x]>=0)for(Pt p:s.hull[s.asg[x]])if(pteq(p,I.P[x])){d*=.12;break;}
        rank.push_back({d,x});
    }
    sort(rank.begin(),rank.end());vector<int>xs,removed(I.no,0);int free=0;
    for(auto e:rank){int x=e.second,o=s.asg[x];if(o<0&&free>=q/3)continue;
        if(o>=0&&removed[o]+1>=s.size_[o])continue;
        xs.push_back(x);if(o<0)free++;else removed[o]++;
        if((int)xs.size()>=q)break;
    }
    if(xs.empty())return false;
    boundary_stats.calls++;BoundarySearch b(s,xs,ops,end,method!=4);
    if(method==1||method==4)b.dfs(0);else b.beam(32,method==3||method==5,method==5);
    if(!b.stopped&&(method==1||method==4))boundary_stats.complete++;
    return b.finish();
}
static void boundary_polish(Sol&s,mt19937_64&rng,double end,int method,int style=0){
    while(elapsed()<end){double d=min(end,elapsed()+.04);long old=boundary_stats.calls;
        int q=getenv("B_Q")?max(4,min(40,atoi(getenv("B_Q")))):24;
        boundary_move(s,rng,d,method,style,q);
        if(old==boundary_stats.calls)break;}
}
