// All-office fallback after geometric/worker failure. Negative raw profit is
// permitted when the actual global load penalty makes its insertion profitable.
static bool level_fill(Sol&,Engine&,double);
static atomic<long> xn_fill_geofail{0},xn_fill_alternative{0},xn_fill_negative{0};
static int xn_fill_mode(){static const int m=getenv("XN_FILL")?atoi(getenv("XN_FILL")):0;return m;}
static void xn_recreate(Engine&E,Guide&Gd,mt19937_64&rng,bool aggressive,int topk,double deadline){
    Sol&s=E.s;const Inst&I=E.I;vector<int>un;
    for(int x=0;x<I.ns;x++)if(s.asg[x]<0&&I.servable[x])un.push_back(x);
    shuffle(un.begin(),un.end(),rng);long long v0=E.size_viol(-1,-1);vector<pair<double,int>>choices;
    for(int x:un){
        if(elapsed()>=deadline)return;choices.clear();
        for(int o:I.cand[x]){
            if(!s.isopen[o]||s.size_[o]>=I.maxsize[o]||E.size_viol(o,-1)>max(v0,0LL)||!E.can_add_skills(x,o))continue;
            double sc=Gd.eff(o,x);if(aggressive||sc>0)choices.push_back({sc,o});}
        stable_sort(choices.begin(),choices.end(),[](auto&a,auto&b){return a.first>b.first;});
        int tried=0;for(auto choice:choices){if(elapsed()>=deadline)return;
            if(E.doAdd(x,choice.second)){if(tried&&DBG)xn_fill_alternative++;break;}
            if(DBG)xn_fill_geofail++;tried++;}
    }
}
static bool xn_greedy_fill(Sol&s,Engine&E,double deadline){
    const Inst&I=*s.I;Guide G0(s,0.);bool any=false;vector<pair<double,int>>un,choices;
    for(int pass=0;pass<3;pass++){
        un.clear();for(int x=0;x<I.ns;x++)if(s.asg[x]<0&&I.servable[x]){
            if((x&127)==0&&elapsed()>=deadline)return any;
            double b=NEG;for(int o=0;o<I.no;o++)if(s.isopen[o])b=max(b,I.pr(o,x));
            // One insertion can decrease max(load)-min(load) by at most its
            // task load. This safe bound avoids sorting hopeless negative sites.
            if(b+I.alpha*I.ntask[x]>1e-9)un.push_back({b,x});}
        sort(un.rbegin(),un.rend());bool changed=false;
        for(auto e:un){
            if(elapsed()>=deadline)return any;int x=e.second;double base=G0.tail2(-1,0,0,-1,0,0);choices.clear();
            for(int o:I.cand[x]){
                if(!s.isopen[o]||s.size_[o]>=I.maxsize[o]||E.size_viol(o,-1)>0||!E.can_add_skills(x,o))continue;
                double delta=I.pr(o,x)+G0.tail2(o,1,I.ntask[x],-1,0,0)-base;
                if(delta>1e-9)choices.push_back({delta,o});}
            stable_sort(choices.begin(),choices.end(),[](auto&a,auto&b){return a.first>b.first;});
            int tried=0;for(auto choice:choices){
                if(elapsed()>=deadline)return any;
                size_t mark=E.jr.size();
                if(!E.doAdd(x,choice.second)){if(DBG)xn_fill_geofail++;tried++;continue;}
                if(!I.simple_workers&&!s.greedy_workers(nullptr)){if(E.rec)E.undo(mark);else s.remove_site(x);tried++;continue;}
                if(DBG){if(tried)xn_fill_alternative++;if(I.pr(choice.second,x)<0)xn_fill_negative++;}
                changed=any=true;break;}
        }
        if(!changed)break;
    }
    if(elapsed()<deadline&&level_fill(s,E,deadline))any=true;return any;
}
