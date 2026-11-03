struct GeoStats{long calls=0,wins=0,geo_fail=0,balance_fail=0,worker_fail=0,trimmed=0,triangles=0;double gain=0;};
static thread_local GeoStats geo_stats;
static bool gi_accept(Sol&s,const vector<int>&a,const vector<char>&op,double old){
    s.recompute_psum();vector<int>w;double f=0;
    bool win=s.objective_fast()>old+1e-7*max(1.,fabs(old))&&s.greedy_workers(&w)&&verify(*s.I,s.asg,s.isopen,w,&f)&&f>old+1e-7*max(1.,fabs(old));
    if(win){geo_stats.wins++;geo_stats.gain+=f-old;}else s.load_state(a,op);return win;
}
static bool gi_eject(Sol&s,mt19937_64&rng,double end){
    const Inst&I=*s.I;geo_stats.calls++;auto olda=s.asg;auto oldop=s.isopen;double old=s.objective();
    vector<pair<double,pair<int,int>>>cand;Guide g(s,I.alpha*.25);g.dual_step(1.0);
    for(int o=0;o<I.no;o++)if(s.isopen[o])for(int x=0;x<I.ns;x++)if(I.servable[x]&&s.asg[x]!=o){
        double p=g.eff(o,x)-(s.asg[x]>=0?g.eff(s.asg[x],x):0);
        if(p>0)cand.push_back({p,{o,x}});
    }
    if(cand.empty())return false;int kk=min(128,(int)cand.size());partial_sort(cand.begin(),cand.begin()+kk,cand.end(),[](const auto&a,const auto&b){return a>b;});
    auto [o,x]=cand[rng()%kk].second;Engine E(s);E.rec=false;E.doRemove(x);s.force_add(x,o);
    vector<double>cost(I.ns,0);for(int y=0;y<I.ns;y++)if(s.asg[y]>=0)cost[y]=max(0.,g.eff(s.asg[y],y))+1e-8;
    for(int step=0;step<12&&elapsed()<end;step++){
        int q=-1;for(int i=0;i<s.np;i++)if(s.cov[i]>1){q=i;break;}if(q<0)break;
        TrimResult best;int bo=-1;
        for(int z=0;z<I.no;z++)if(s.isopen[z]&&s.incov[(size_t)z*s.np+q]){
            vector<Pt>protect={I.P[I.ns+z]};if(z==o)protect.push_back(I.P[x]);
            auto t=gi_trim(I.P,s.members[z],cost,I.P[q],protect,end,I.eps_len*2);
            if(t.loss<best.loss){best=move(t);bo=z;}
        }
        if(bo<0||best.remove.empty())break;geo_stats.trimmed+=best.remove.size();for(int y:best.remove)E.doRemove(y);
    }
    for(int i=0;i<s.np;i++)if(s.cov[i]>1){geo_stats.geo_fail++;s.load_state(olda,oldop);return false;}
    for(int z=0;z<I.no;z++)while(s.size_[z]>I.maxsize[z]&&elapsed()<end){int y=-1;double c=1e100;for(int v:s.members[z])if(v!=x&&cost[v]<c){y=v;c=cost[v];}if(y<0)break;E.doRemove(y);}
    if(elapsed()<end){greedy_fill(s,E,end);repair_sizes(s);resize_dp(s,end,false);}
    if(E.size_viol(-1,-1))geo_stats.balance_fail++;
    if(!s.greedy_workers(nullptr))geo_stats.worker_fail++;
    return gi_accept(s,olda,oldop,old);
}
static bool gi_rebuild(Sol&s,mt19937_64&rng,double end,bool pairmode){
    const Inst&I=*s.I;geo_stats.calls++;auto olda=s.asg;auto oldop=s.isopen;double old=s.objective();auto oldhulls=s.hull;
    vector<int>ops;for(int o=0;o<I.no;o++)if(s.size_[o])ops.push_back(o);if(ops.empty())return false;
    int o=ops[rng()%ops.size()],other=-1;
    if(pairmode&&ops.size()>1){vector<pair<double,int>>near;for(int z:ops)if(z!=o)near.push_back({hypot(I.P[I.ns+o].x-I.P[I.ns+z].x,I.P[I.ns+o].y-I.P[I.ns+z].y),z});sort(near.begin(),near.end());other=near[rng()%min(3,(int)near.size())].second;}
    Guide G(s,I.alpha*.25);G.dual_step(1.0);vector<double>pi=G.pi;Engine E(s);E.rec=false;
    vector<int>chosen={o};if(other>=0)chosen.push_back(other);
    for(int z:chosen){auto mem=s.members[z];for(int x:mem)E.doRemove(x);}
    for(int z:chosen){if(elapsed()>=end)break;
        vector<double>weights(s.np,0);vector<char>red(s.np,0);vector<pair<double,int>>rank;
        for(int i=0;i<s.np;i++)red[i]=s.cov[i]-(int)s.incov[(size_t)z*s.np+i]>0;
        double competition=other>=0?(rng()%4)*.25:0.;
        for(int x=0;x<I.ns;x++)if(s.asg[x]<0&&I.servable[x]&&!red[x]){
            double v=I.pr(z,x)-pi[z]*I.ntask[x];int competitor=z==o?other:o;
            weights[x]=max(0.,v)-(competitor>=0?competition*max(0.,I.pr(competitor,x)-pi[competitor]*I.ntask[x]):0);
            if(v>0||olda[x]==z)rank.push_back({v*(.75+double(rng()%1000)/2000),x});
        }
        int K=I.ns>1500?20:32;sort(rank.rbegin(),rank.rend());vector<int>vertices={I.ns+z};
        for(auto [w,x]:rank){if((int)vertices.size()>=K)break;vertices.push_back(x);}
        // Preserve old extreme points in the proposal alphabet; cap keeps N=10000 bounded.
        for(int x=0;x<I.ns&&(int)vertices.size()<K+8;x++)if(olda[x]==z&&!red[x]){
            bool extreme=false;for(Pt p:oldhulls[z])if(pteq(p,I.P[x]))extreme=true;
            if(extreme&&find(vertices.begin(),vertices.end(),x)==vertices.end())vertices.push_back(x);
        }
        auto isl=gi_island(I.P,weights,red,vertices,I.ns+z,end,I.eps_cr);geo_stats.triangles+=isl.triangles;
        if(isl.hull.empty())continue;vector<pair<double,int>>add;
        for(int x=0;x<I.ns;x++)if(s.asg[x]<0&&I.servable[x]&&gi_inside(isl.hull,I.P[x],I.eps_cr))add.push_back({I.pr(z,x)-pi[z]*I.ntask[x],x});
        sort(add.rbegin(),add.rend());for(auto [w,x]:add){if(elapsed()>end)break;E.doAdd(x,z);}
    }
    if(elapsed()<end){resize_dp(s,end,false);repair_sizes(s);greedy_fill(s,E,end);}
    if(E.size_viol(-1,-1))geo_stats.balance_fail++;
    return gi_accept(s,olda,oldop,old);
}
static void gi_polish(Sol&s,mt19937_64&rng,double end,int method){
    while(elapsed()<end){double slice=min(end,elapsed()+(s.I->ns>1500?.5:.20));
        int mode=method==5?1+rng()%3:method;
        if(mode==1)gi_eject(s,rng,slice);else if(mode==2||mode==3)gi_rebuild(s,rng,slice,mode==3);else boundary_polish(s,rng,slice,1,1);
    }
}
