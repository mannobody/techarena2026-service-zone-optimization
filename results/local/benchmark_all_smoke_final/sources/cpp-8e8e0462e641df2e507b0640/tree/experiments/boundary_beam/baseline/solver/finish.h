// finish.h: monotone improvement in the unused final time budget.
// Exact alpha=0 selection within fixed convex territories and fixed staff teams.
// Sites inside those hulls can be added without expanding any footprint.
static bool territory_select(Sol& s,double deadline) {
    const Inst&I=*s.I;if(I.alpha!=0.||elapsed()>=deadline)return false;
    vector<int> staff;if(!s.greedy_workers(&staff))return false;
    vector<vector<char>> have(I.no,vector<char>(I.nsk,0));
    for(int w=0;w<I.nw;w++)if(staff[w]>=0)for(int k=0;k<I.nsk;k++)have[staff[w]][k]|=I.wmask[w][k];
    vector<vector<int>> pool(I.no);vector<vector<double>> prefix(I.no);vector<int> positive(I.no,0),cap(I.no,0);
    for(int x=0;x<I.ns;x++) {
        if((x&127)==0&&elapsed()>=deadline)return false;
        if(!I.servable[x])continue;int o=s.asg[x];
        if(o<0&&s.cov[x])for(int p=0;p<I.no;p++)if(s.isopen[p]&&s.size_[p]>0&&s.incov[(size_t)p*s.np+x]){o=p;break;}
        if(o<0)continue;bool ok=true;for(int k:I.skillset[x])if(!have[o][k]){ok=false;break;}
        if(ok)pool[o].push_back(x);
    }
    int largest=0;
    for(int o=0;o<I.no;o++) {
        auto&v=pool[o];sort(v.begin(),v.end(),[&](int a,int b){return I.pr(o,a)>I.pr(o,b);});
        cap[o]=min((int)v.size(),I.maxsize[o]);prefix[o].assign(cap[o]+1,0.);
        for(int j=0;j<cap[o];j++){prefix[o][j+1]=prefix[o][j]+I.pr(o,v[j]);positive[o]+=I.pr(o,v[j])>0.;}
        largest=max(largest,cap[o]);
    }
    double before=s.objective(),best=max(0.,before);vector<int> chosen(I.no,0),trial(I.no,0);
    for(int lo=1;lo<=largest;lo++) {
        if((lo&31)==0&&elapsed()>=deadline)return false;
        double score=0.;fill(trial.begin(),trial.end(),0);
        for(int o=0;o<I.no;o++)if(cap[o]>=lo) {
            int hi=(int)min((long long)cap[o],lo+I.A),n=max(lo,min(hi,positive[o]));
            double value=prefix[o][n]-I.cost[o];if(value>0.){trial[o]=n;score+=value;}
        }
        if(score>best+1e-9){best=score;chosen=trial;}
    }
    if(best<=before+1e-9||elapsed()>=deadline)return false;
    vector<int>a(I.ns,-1);vector<char>open(I.no,0);
    for(int o=0;o<I.no;o++)if(chosen[o]) {
        open[o]=1;for(int j=0;j<chosen[o];j++)a[pool[o][j]]=o;
    }
    s.load_state(a,open);s.recompute_psum();return true;
}

// Find the best FEASIBLE road offer, not just the best road offer.
static bool finish_fill(Sol& s, Engine& E, double deadline) {
    const Inst& I=*s.I;Guide G0(s,0.);bool any=false;
    vector<pair<double,int>> un,choices;
    un.reserve(I.ns);choices.reserve(I.no);
    for(int pass=0;pass<3;pass++) {
        un.clear();
        for(int x=0;x<I.ns;x++)if(s.asg[x]<0&&I.servable[x]) {
            double best=NEG;for(int o=0;o<I.no;o++)if(s.isopen[o])best=max(best,I.pr(o,x));
            if(best>0)un.push_back({best,x});
        }
        if(un.empty())break;sort(un.rbegin(),un.rend());bool changed=false;
        for(auto e:un) {
            if(elapsed()>=deadline)return any;
            int x=e.second;double base=G0.tail2(-1,0,0,-1,0,0);
            choices.clear();
            for(int o:I.cand[x]) {
                if(!s.isopen[o])continue;

                if(s.size_[o]>=I.maxsize[o]||E.size_viol(o,-1)>0||!E.can_add_skills(x,o))continue;
                // Already covered points can only join their covering office.
                if(s.cov[x]>0&&!s.incov[(size_t)o*s.np+x])continue;
                double delta=I.pr(o,x)+G0.tail2(o,1,I.ntask[x],-1,0,0)-base;
                if(delta>1e-9)choices.push_back({delta,o});
            }
            stable_sort(choices.begin(),choices.end(),[](const auto&a,const auto&b){return a.first>b.first;});
            for(auto choice:choices) {
                if(elapsed()>=deadline)return any;
                size_t mark=E.jr.size();
                if(!E.doAdd(x,choice.second))continue;
                if(!I.simple_workers&&!s.greedy_workers(nullptr)) {
                    if(E.rec)E.undo(mark);else s.remove_site(x);
                    continue;
                }
                changed=any=true;break;
            }
        }
        if(!changed)break;
    }
    if(elapsed()<deadline&&level_fill(s,E,deadline))any=true;
    return any;
}

// Run only after search threads have joined, in their unused wall-clock tail.
static void finish_solution(const Inst& I, double limit) {
    const bool enabled=!getenv("FINAL_POLISH")||atoi(getenv("FINAL_POLISH"))>0;
    double end=limit-max(.5,.002*limit);
    if(!enabled||elapsed()>=end||g_best.load()<=0.)return;
    vector<int>a;vector<char>open;
    {lock_guard<mutex> lk(g_best_mx);a=g_best_asg;open=g_best_open;}
    if(a.empty())return;
    double before=g_best.load();
    // No worker threads remain; the feasibility deadline can use the tail too.
    g_wdfs_deadline=end;
    Sol s;s.init(I);s.load_state(a,open);
    if(I.alpha==0.&&elapsed()<end)territory_select(s,end);
    Engine E(s);E.rec=true;
    if(elapsed()<end)finish_fill(s,E,end);
    s.recompute_psum();
    if(s.objective()>before+1e-9)offer(I,s);
    if(DBG)fprintf(stderr,"finish before=%.9f after=%.9f t=%.3f\n",before,g_best.load(),elapsed());
}
