// Atomic replacements preserve site counts, while changing task loads and hulls.
// In contrast to positive-profit reconstruction, EVERY unassigned site is tried.
// Transaction scoring uses the true global task range, not a relaxed guide.
static void zm_signed_finish(const Inst&I,double end) {
    if(getenv("ZM_SIGNED")&&!atoi(getenv("ZM_SIGNED")))return;
    if(I.ns>3000||I.no>32||elapsed()>=end||g_best.load()<=0)return;
    vector<int>a;vector<char>op;{lock_guard<mutex>lk(g_best_mx);a=g_best_asg;op=g_best_open;}
    if(a.empty())return;Sol s;s.init(I);s.load_state(a,op);g_wdfs_deadline=end;
    struct Move {double gain;int x,y,o,p;};
    auto more=[](const Move&a,const Move&b){return a.gain>b.gain;};
    long scanned=0,tested=0,wins=0;double before=g_best.load(),start=elapsed();
    for(int round=0;round<20&&elapsed()<end;round++) {
        vector<Move> best;
        auto add=[&](double gain,int x,int y,int o,int p){
            if(gain<=1e-8)return;Move m{gain,x,y,o,p};
            if(best.size()<256){best.push_back(m);push_heap(best.begin(),best.end(),more);}
            else if(gain>best.front().gain){pop_heap(best.begin(),best.end(),more);best.back()=m;push_heap(best.begin(),best.end(),more);}
        };
        vector<int>ops;for(int o=0;o<I.no;o++)if(s.isopen[o]&&s.size_[o])ops.push_back(o);
        long long low=LLONG_MAX,high=0;for(int o:ops){low=min(low,s.load[o]);high=max(high,s.load[o]);}
        for(int o:ops) {
            if(elapsed()>=end)break;
            long long extlow=LLONG_MAX,exthigh=LLONG_MIN;
            for(int p:ops)if(p!=o){extlow=min(extlow,s.load[p]);exthigh=max(exthigh,s.load[p]);}
            map<int,vector<pair<double,int>>> group;
            for(int x:s.members[o])group[I.ntask[x]].push_back({I.pr(o,x),x});
            for(auto&g:group){sort(g.second.begin(),g.second.end());if(g.second.size()>3)g.second.resize(3);}
            for(int y=0;y<I.ns;y++)if(s.asg[y]<0&&I.servable[y]) {
                if((y&63)==0&&elapsed()>=end)break;
                if(s.cov[y]&&!s.incov[(size_t)o*s.np+y])continue;
                for(auto&g:group) {
                    long long ld=s.load[o]+I.ntask[y]-g.first;
                    long long range=ops.size()==1?0:max(exthigh,ld)-min(extlow,ld);
                    double gain=I.pr(o,y)-g.second[0].first-I.alpha*(range-(high-low));
                    for(auto px:g.second){scanned++;add(gain+g.second[0].first-px.first,px.second,y,o,-1);}
                }
            }
        }
        // Two-office exchanges change both loads together. All removals precede
        // additions, permitting a joint hull change that sequential moves block.
        for(int x=0;x<I.ns&&elapsed()<end;x++)if(s.asg[x]>=0) {
            int o=s.asg[x];
            for(int y=x+1;y<I.ns;y++)if(s.asg[y]>=0&&s.asg[y]!=o) {
                if((++scanned&1023)==0&&elapsed()>=end)break;
                int p=s.asg[y];double gain=I.pr(o,y)+I.pr(p,x)-I.pr(o,x)-I.pr(p,y);
                long long d=I.ntask[y]-I.ntask[x],mn=LLONG_MAX,mx=LLONG_MIN;
                for(int q:ops){long long ld=s.load[q]+(q==o?d:0)-(q==p?d:0);mn=min(mn,ld);mx=max(mx,ld);}
                gain-=I.alpha*((mx-mn)-(high-low));add(gain,x,y,o,p);
            }
        }
        if(elapsed()>=end)break;
        sort(best.begin(),best.end(),more);Engine E(s);E.rec=true;bool changed=false;
        for(auto m:best) {
            if(elapsed()>=end)break;tested++;size_t mark=E.jr.size();
            E.doRemove(m.x);if(m.p>=0)E.doRemove(m.y);
            bool ok=E.doAdd(m.y,m.o)&&(m.p<0||E.doAdd(m.x,m.p));
            if(ok&&offer(I,s)){E.jr.clear();wins++;changed=true;break;}
            E.undo(mark);
        }
        if(!changed)break;
    }
    fprintf(stderr,"ZMSIGNED scanned=%ld tested=%ld wins=%ld before=%.9f after=%.9f seconds=%.6f\n",scanned,tested,wins,before,g_best.load(),elapsed()-start);
}
