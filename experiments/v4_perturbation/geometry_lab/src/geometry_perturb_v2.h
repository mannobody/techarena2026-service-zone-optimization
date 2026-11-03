// Small, count/load preserving perturbations for the exact frozen server v4.
// Include after lns. No dependencies or IO; default integration is OFF.
#pragma once
struct GeometryStats {
    long attempts=0, accepted=0, geometry_reject=0, worker_reject=0, loss_reject=0;
    long moved=0, hull_changed=0, workers_changed=0, offices_changed=0, freed_points=0;
    long recoveries=0, improved=0, returned_same=0, unrecovered=0;
    double perturb_seconds=0, recovery_seconds=0, loss_sum=0, gain_sum=0, first_improvement=-1;
};
static bool gp_hull_equal(const vector<Pt>&a,const vector<Pt>&b){
    if(a.size()!=b.size())return false;
    for(size_t j=0;j<a.size();++j)if(!pteq(a[j],b[j]))return false;
    return true;
}
static bool gp_on_hull(const Sol&s,int x,int o){
    for(auto&p:s.hull[o])if(pteq(p,s.I->P[x]))return true;
    return false;
}
static double gp_dist2(Pt p,Pt q){double x=p.x-q.x,y=p.y-q.y;return x*x+y*y;}
static double gp_hull_distance(Pt p,const vector<Pt>&h){
 double best=1e300;if(h.empty())return best;
 for(size_t i=0;i<h.size();++i){Pt a=h[i],b=h[(i+1)%h.size()];double dx=b.x-a.x,dy=b.y-a.y;
  double t=(dx*dx+dy*dy)>0?((p.x-a.x)*dx+(p.y-a.y)*dy)/(dx*dx+dy*dy):0;
  t=max(0.,min(1.,t));best=min(best,gp_dist2(p,{a.x+t*dx,a.y+t*dy}));}
 return best;
}
static int gp_neighbor(const Sol&s,int a,const vector<int>&ops,mt19937_64&rng,int exclude=-1){
 vector<pair<double,int>> rank;
 for(int b:ops)if(b!=a&&b!=exclude){double d=1e300;for(Pt p:s.hull[a])d=min(d,gp_hull_distance(p,s.hull[b]));rank.push_back({d,b});}
 if(rank.empty())return -1;sort(rank.begin(),rank.end());return rank[rng()%min(3,(int)rank.size())].second;
}
static vector<int> gp_pool(const Sol&s,int a,int b,int cap=24){
 const Inst&I=*s.I;vector<pair<double,int>>geo,profit;
 for(int x:s.members[a]){geo.push_back({gp_hull_distance(I.P[x],s.hull[b]),x});profit.push_back({I.pr(b,x)-I.pr(a,x),x});}
 sort(geo.begin(),geo.end());sort(profit.rbegin(),profit.rend());vector<int>out;
 for(int j=0;j<(int)geo.size()&&j<cap/2;++j)out.push_back(geo[j].second);
 for(auto v:profit){if((int)out.size()>=cap)break;if(find(out.begin(),out.end(),v.second)==out.end())out.push_back(v.second);}
 return out;
}
// Atomic final-state transaction. Counts, loads and active offices are unchanged;
// temporary cardinality violation during removal is local and never published.
static bool gp_transaction(Sol&s,const vector<int>&xs,const vector<int>&to,
                           double loss_cap,GeometryStats&st,int require_hull=0){
    ++st.attempts;const Inst&I=*s.I;double old=s.objective();
    vector<int> count(I.no);vector<long long> load(I.no);
    vector<int> affected;double delta=0;
    for(size_t j=0;j<xs.size();++j){
        int x=xs[j],a=s.asg[x],b=to[j];
        for(size_t k=0;k<j;++k)if(xs[k]==x)return false;
        if(a>=0){--count[a];load[a]-=I.ntask[x];delta-=I.pr(a,x);affected.push_back(a);}
        if(b>=0){++count[b];load[b]+=I.ntask[x];delta+=I.pr(b,x);affected.push_back(b);}
    }
    for(int o=0;o<I.no;++o)if(count[o]||load[o])return false;
    if(delta < -loss_cap){++st.loss_reject;return false;}
    sort(affected.begin(),affected.end());affected.erase(unique(affected.begin(),affected.end()),affected.end());
    vector<vector<Pt>> hulls;vector<vector<int>> oldcov;for(int o:affected){hulls.push_back(s.hull[o]);oldcov.push_back(s.covlist[o]);}
    vector<int> oldw;s.greedy_workers(&oldw);
    Engine E(s);E.rec=true;
    for(int x:xs)E.doRemove(x);
    bool ok=true;
    for(size_t j=0;j<xs.size();++j)if(to[j]>=0&&!E.doAdd(xs[j],to[j])){ok=false;break;}
    if(!ok){++st.geometry_reject;E.undo(0);return false;}
    vector<int>w;if(!s.greedy_workers(&w)){++st.worker_reject;E.undo(0);return false;}
    int hc=0;for(size_t j=0;j<affected.size();++j)hc+=!gp_hull_equal(hulls[j],s.hull[affected[j]]);
    int freed=0;for(size_t j=0;j<affected.size();++j)for(int p:oldcov[j])freed+=!s.incov[(size_t)affected[j]*s.np+p]&&find(xs.begin(),xs.end(),p)==xs.end();
    if((require_hull&&!hc)||(require_hull==2&&!freed)){E.undo(0);return false;}
    s.recompute_psum();
    if(E.size_viol(-1,-1)||s.objective()<old-loss_cap-1e-7){E.undo(0);return false;}
    ++st.accepted;st.moved+=xs.size();st.hull_changed+=hc;st.freed_points+=freed;
    for(size_t j=0;j<min(w.size(),oldw.size());++j)st.workers_changed+=(w[j]!=oldw[j]);
    st.loss_sum+=max(0.,old-s.objective());return true;
}
// mode1: equal-load two-site packets across a promising boundary (1<->1 or2<->2).
// mode2: hull support replaces a free equal-load site; both cardinality/load exact.
// mode3: directed three-office equal-load cycle, not whole-zone reconstruction.
static bool geometry_perturb(Sol&s,mt19937_64&rng,double deadline,int mode,GeometryStats&st){
    double start=elapsed();const Inst&I=*s.I;vector<int>ops;
    int total=0;for(int o=0;o<I.no;++o)if(s.isopen[o]&&s.size_[o]){ops.push_back(o);total+=s.size_[o];}
    double cap=min(max(1.,fabs(s.objective()))*.002,
                   max(1.,fabs(s.psum)/max(1,total))*.5);
    bool success=false;
    for(int trial=0;trial<256&&elapsed()<deadline&&!success;++trial){
        if(ops.empty())break;int a=ops[rng()%ops.size()];
        if(mode==2){
            vector<int>support;for(int x:s.members[a])if(gp_on_hull(s,x,a))support.push_back(x);
            if(support.empty())continue;int x=support[rng()%support.size()];
            vector<pair<double,int>>free;
            for(int y=0;y<I.ns&&elapsed()<deadline;++y)
                if(s.asg[y]<0&&I.servable[y]&&I.ntask[y]==I.ntask[x])
                    free.push_back({I.pr(a,y)-I.pr(a,x),y});
            sort(free.rbegin(),free.rend());int n=min(32,(int)free.size());
            if(!n)continue;int y=free[rng()%n].second;
            success=gp_transaction(s,{x,y},{-1,a},cap,st,2);
        }else{
            if(ops.size()<2)break;int b=gp_neighbor(s,a,ops,rng);if(b<0)continue;
            auto pa=gp_pool(s,a,b),pb=gp_pool(s,b,a);if(pa.empty()||pb.empty())continue;
            int x=pa[rng()%pa.size()],y=pb[rng()%pb.size()];
            struct P{double delta;vector<int>x,to;};vector<P>proposals;
            auto add=[&](vector<int>x,vector<int>to){double delta=0;for(size_t j=0;j<x.size();++j)delta+=I.pr(to[j],x[j])-I.pr(s.asg[x[j]],x[j]);if(delta>=-cap)proposals.push_back({delta,move(x),move(to)});else ++st.loss_reject;};
            if(mode==3){
                if(ops.size()<3)break;int c=gp_neighbor(s,b,ops,rng,a);if(c<0)continue;
                auto pc=gp_pool(s,c,a,12),by=gp_pool(s,b,c,12);pa=gp_pool(s,a,b,12);
                for(int xx:pa)for(int yy:by)for(int zz:pc)
                    if(I.ntask[xx]==I.ntask[yy]&&I.ntask[yy]==I.ntask[zz])add({xx,yy,zz},{b,c,a});
            }else{
                for(int xx:pa)for(int yy:pb)if(I.ntask[xx]==I.ntask[yy])add({xx,yy},{b,a});
                for(int k=0;k<512;++k){int xx=pa[rng()%pa.size()],xxx=pa[rng()%pa.size()],yy=pb[rng()%pb.size()],yyy=pb[rng()%pb.size()];
                    if(xx!=xxx&&yy!=yyy&&I.ntask[xx]+I.ntask[xxx]==I.ntask[yy]+I.ntask[yyy])add({xx,xxx,yy,yyy},{b,b,a,a});}
            }
            sort(proposals.begin(),proposals.end(),[](const P&a,const P&b){return a.delta>b.delta;});
            // Only a bounded good-loss frontier is considered; random tie order avoids
            // deterministically repeating the exact same zero-loss proposal.
            int n=min(64,(int)proposals.size());shuffle(proposals.begin(),proposals.begin()+n,rng);
            for(int j=0;j<n&&elapsed()<deadline&&!success;++j)
                success=gp_transaction(s,proposals[j].x,proposals[j].to,cap,st,true);
        }
    }
    st.perturb_seconds+=elapsed()-start;return success;
}
static void geometry_search(Sol&s,mt19937_64&rng,double deadline,int mode,GeometryStats&st){
    Sol best=s;double start=elapsed(),bv=s.objective();
    while(elapsed()+.015<deadline){
        s=best;auto before=s.asg;double old=bv;
        bool changed=geometry_perturb(s,rng,min(deadline,elapsed()+.08),mode,st);
        if(!changed){lns(s,rng,deadline,deadline,false);if(s.objective()>bv){best=s;bv=s.objective();}break;}
        double rstart=elapsed(),rend=min(deadline,rstart+.35);
        lns(s,rng,rend,rend,false,.25,1.,true);
        ++st.recoveries;st.recovery_seconds+=elapsed()-rstart;

        if(s.asg==before)++st.returned_same;
        if(s.objective()<old-1e-7)++st.unrecovered;
        if(s.objective()>bv+1e-7){++st.improved;st.gain_sum+=s.objective()-bv;
            if(st.first_improvement<0)st.first_improvement=elapsed()-start;
            bv=s.objective();best=s;offer(*s.I,s);}
        // Native LNS can publish an intermediate better state but return a worse
        // endpoint. Adopt the process incumbent independently of endpoint diagnostics.
        if(g_best.load()>bv+1e-7){vector<int>a;vector<char>op;
            {lock_guard<mutex>lk(g_best_mx);a=g_best_asg;op=g_best_open;}
            if(!a.empty()){Sol published;published.init(*s.I);published.load_state(a,op);
                if(published.objective()>bv+1e-7){best=published;bv=published.objective();}}}

    }
    s=best;
}
