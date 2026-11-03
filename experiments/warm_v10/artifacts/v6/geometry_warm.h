// Feasible spatial memetic starts. No external state; all genomes belong to this input.
static double gw_distance(const vector<int>& a,const vector<int>& b) {
    size_t different=0,used=0;
    for(size_t x=0;x<a.size();x++) if(a[x]>=0||b[x]>=0){used++;different+=a[x]!=b[x];}
    return used?(double)different/used:0.;
}

// Quality and assignment diversity, with an unconditionally protected best.
static void gw_trim(vector<Cand>& pop,size_t capacity) {
    stable_sort(pop.begin(),pop.end(),[](const Cand&a,const Cand&b){return a.f>b.f;});
    vector<Cand> unique;
    for(auto& c:pop) {
        bool duplicate=false;
        for(const auto& p:unique)if(gw_distance(c.asg,p.asg)<.025){duplicate=true;break;}
        if(!duplicate)unique.push_back(move(c));
    }
    if(unique.size()<=capacity){pop.swap(unique);return;}
    vector<size_t> selected{0};vector<char> used(unique.size(),0);used[0]=1;
    double scale=max(1.,fabs(unique[0].f));
    while(selected.size()<capacity) {
        double best=NEG;size_t bi=0;
        for(size_t i=1;i<unique.size();i++)if(!used[i]) {
            double d=1.;for(size_t j:selected)d=min(d,gw_distance(unique[i].asg,unique[j].asg));
            double value=unique[i].f/scale+.18*d;
            if(value>best){best=value;bi=i;}
        }
        used[bi]=1;selected.push_back(bi);
    }
    pop.clear();for(size_t i:selected)pop.push_back(move(unique[i]));
}

static vector<Cand> geometry_start_lane(const Inst& I,const Fast& F,
        const vector<Cand>& seeds,uint64_t seed,double end,double limit,int lane,int mode) {
    mt19937_64 rng(seed);uniform_real_distribution<double> U(0.,1.);
    vector<Pt> original(I.P.begin()+I.ns,I.P.end());
    vector<Cand> pop;long decoded=0,crosses=0,inherited=0,invalid=0,nonpositive=0,improved=0;
    double decode_cost=.001;int attempt=0;
    Pt center{0,0};for(auto p:original){center.x+=p.x;center.y+=p.y;}
    if(I.no){center.x/=I.no;center.y/=I.no;}
    auto parent=[&]()->const Cand& {
        size_t a=rng()%pop.size(),b=rng()%pop.size();
        // Alternate quality selection with uniform niche selection.
        return U(rng)<.5?pop[a]:(pop[a].f>pop[b].f?pop[a]:pop[b]);
    };
    while(elapsed()+min(.01,decode_cost*.05)<end) {
        double begin=elapsed();
        double slice=min(end,begin+max(.08,min(.012*limit,max(.08,(end-begin)/4))));
        Cand c;c.h.assign(I.no,0.);c.G=original;
        Sol s;bool crossed=false;int family=(attempt+lane*3)%6;
        if(mode>=2&&pop.size()>=3&&attempt>(int)seeds.size()/2&&U(rng)<.45) {
            // Inherit complete parental zones on opposite sides of a spatial cut.
            // Reject a whole zone transaction if its input-point footprint or staff conflicts.
            const Cand a=parent(),b=parent();
            double angle=U(rng)*6.283185307179586;
            Pt u{cos(angle),sin(angle)};vector<double> projections;
            for(int o=0;o<I.no;o++)if(a.open[o]||b.open[o])
                projections.push_back(original[o].x*u.x+original[o].y*u.y);
            sort(projections.begin(),projections.end());
            double cut=projections.empty()?0.:projections[rng()%projections.size()];
            vector<pair<int,int>> zones;
            for(int o=0;o<I.no;o++) {
                int side=(original[o].x*u.x+original[o].y*u.y<=cut)?0:1;
                if((side?b:a).open[o])zones.push_back({o,side});
                else if((side?a:b).open[o]&&U(rng)<.3)zones.push_back({o,1-side});
            }
            shuffle(zones.begin(),zones.end(),rng);s.init(I);Engine E(s);E.rec=true;
            for(auto z:zones) {
                if(elapsed()>=slice)break;
                const Cand& p=z.second?b:a;size_t mark=E.jr.size();
                E.doOpen(z.first);bool ok=s.isopen[z.first];
                for(int x=0;x<I.ns&&ok;x++)if(p.asg[x]==z.first)ok=E.doAdd(x,z.first);
                if(ok)ok=s.greedy_workers(nullptr);
                if(!ok)E.undo(mark);else {inherited++;E.jr.clear();}
            }
            crossed=true;crosses++;
        } else {
            // Initial portfolio preserves cardinality and office-set niches from the old proxy.
            if(attempt<(int)seeds.size())c=seeds[(attempt+lane*7)%seeds.size()];
            else if(pop.size()>=2&&U(rng)<.8) {
                Cand a=parent(),b=parent();vector<char> aa(I.no,0),bb(I.no,0);
                for(int o:a.op)aa[o]=1;for(int o:b.op)bb[o]=1;
                double angle=U(rng)*6.283185307179586;
                Pt u{cos(angle),sin(angle)};
                double cut=center.x*u.x+center.y*u.y+(U(rng)-.5)*I.ext;
                for(int o=0;o<I.no;o++) {
                    const Cand& p=(original[o].x*u.x+original[o].y*u.y<cut)?a:b;
                    bool choose=(&p==&a)?aa[o]:bb[o];
                    if(U(rng)<1./max(1,I.no))choose=!choose;
                    if(!choose)continue;c.op.push_back(o);c.h[o]=p.h[o];c.G[o]=p.G[o];
                    // Region centroid guides the next power-diagram geometry.
                    Pt centroid=original[o];double weight=1.;
                    for(int x=0;x<I.ns;x++)if(p.asg[x]==o) {
                        double w=max(1e-9,I.pr(o,x));centroid.x+=w*I.P[x].x;centroid.y+=w*I.P[x].y;weight+=w;
                    }
                    centroid.x/=weight;centroid.y/=weight;
                    double step=(attempt%3==0?.1:(attempt%3==1?.35:.7));
                    c.G[o].x=(1-step)*c.G[o].x+step*centroid.x;
                    c.G[o].y=(1-step)*c.G[o].y+step*centroid.y;
                    c.h[o]+=(U(rng)-.5)*F.scale2*(1+attempt%3);
                }
            } else {
                // Spatially spread immigrants, across all feasible cardinalities.
                int k=1+rng()%max(1,I.no);vector<int> available(I.no);iota(available.begin(),available.end(),0);
                int first=rng()%I.no;c.op.push_back(first);available.erase(find(available.begin(),available.end(),first));
                while((int)c.op.size()<k&&!available.empty()) {
                    double best=-1.;int bo=-1;
                    for(int o:available) {
                        double nearest=1e300;for(int p:c.op) {
                            double dx=original[o].x-original[p].x,dy=original[o].y-original[p].y;
                            nearest=min(nearest,dx*dx+dy*dy);
                        }
                        double v=nearest*(.25+U(rng));if(v>best){best=v;bo=o;}
                    }
                    c.op.push_back(bo);available.erase(find(available.begin(),available.end(),bo));
                }
            }
            sort(c.op.begin(),c.op.end());
            vector<int> clean;for(int o:c.op) {
                bool duplicate=false;for(int p:clean)if(pteq(original[o],original[p])){duplicate=true;break;}
                if(!duplicate&&I.maxsize[o]>0)clean.push_back(o);
            }
            c.op.swap(clean);if(c.op.empty()){attempt++;continue;}
            // Feasibility restoration of the power diagram, then bounded refinement.
            for(int k=0;k<5&&!F.offices_in_own_cell(c.op,c.h,c.G);k++)for(int o:c.op) {
                c.h[o]*=.5;c.G[o].x=(c.G[o].x+original[o].x)*.5;c.G[o].y=(c.G[o].y+original[o].y)*.5;
            }
            if(!F.offices_in_own_cell(c.op,c.h,c.G)){c.h.assign(I.no,0.);c.G=original;}
            vector<int> labels(I.ns,-1);
            if(family<=1) {
                if(elapsed()<slice)F.search(c.op,c.h,c.G,I.ns>2000?1:3,min(slice,elapsed()+.15*(slice-begin)));
                if(family==0) {
                    vector<vector<int>> mem;
                    F.evaluate(c.op,c.h,c.G,&mem);
                    if(!mem.empty())for(int o:c.op)for(int x:mem[o])labels[x]=o;
                } else {
                    vector<int> cell;F.cells(c.op,c.h,c.G,cell);
                    for(int x=0;x<I.ns;x++)labels[x]=c.op[cell[x]];
                }
            } else if(family==2)labels=ctor_road(I,c.op);
            else if(family==3)labels=ctor_sector(I,c.op,center);
            else if(family==4)labels=ctor_guillotine(I,c.op,rng);
            else labels=ctor_sector(I,c.op,{center.x+(U(rng)-.5)*I.ext,center.y+(U(rng)-.5)*I.ext});
            realize(s,I,c.op,labels,slice,&rng,attempt%4==3?.15+.35*U(rng):0.);
        }
        repair_sizes(s);
        if(elapsed()<slice){resize_dp(s,slice);repair_sizes(s);}
        Engine E(s);
        for(int o=0;o<I.no;o++)if(s.isopen[o]&&!s.size_[o])E.doClose(o);
        s.recompute_psum();
        if(elapsed()<slice)greedy_fill(s,E,slice);
        s.recompute_psum();
        double f=s.objective(),before=f;
        if(!pop.empty()&&attempt%3==2&&elapsed()+.02<slice) {
            // True feasible fitness after a short local search: a memetic genome.
            auto saved=s.asg;auto opened=s.isopen;
            lns(s,rng,slice,slice,false,.25,1.,true);s.recompute_psum();
            if(s.objective()+1e-9<f)s.load_state(saved,opened);
        }
        for(int o=0;o<I.no;o++)if(s.isopen[o]&&!s.size_[o])E.doClose(o);
        vector<int> workers;double value=0.;
        bool valid=s.greedy_workers(&workers)&&verify(I,s.asg,s.isopen,workers,&value);
        if(valid&&value>0.) {
            improved+=value>before+1e-9;
            c.f=value;c.asg=s.asg;c.open=s.isopen;c.op.clear();
            for(int o=0;o<I.no;o++)if(s.isopen[o]&&s.size_[o])c.op.push_back(o);
            if(crossed){c.h.assign(I.no,0.);c.G=original;}
            offer(I,s);pop.push_back(move(c));gw_trim(pop,18);
        } else {invalid+=!valid;nonpositive+=valid&&value<=0.;}
        if(getenv("GW_TRACE"))fprintf(stderr,"GWTRACE lane=%d attempt=%d family=%d cross=%d valid=%d objective=%.9f before=%.9f pop=%zu t=%.6f\n",lane,attempt,family,crossed,valid,value,before,pop.size(),elapsed());
        decoded++;attempt++;decode_cost=max(.001,.7*decode_cost+.3*(elapsed()-begin));
    }
    gw_trim(pop,8);
    double diversity=0.;int pairs=0;
    for(size_t i=0;i<pop.size();i++)for(size_t j=0;j<i;j++){diversity+=gw_distance(pop[i].asg,pop[j].asg);pairs++;}
    fprintf(stderr,"GEOWARM lane=%d mode=%d decoded=%ld crosses=%ld inherited=%ld invalid=%ld nonpositive=%ld localwins=%ld kept=%zu distance=%.6f best=%.9f t=%.3f\n",
            lane,mode,decoded,crosses,inherited,invalid,nonpositive,improved,pop.size(),pairs?diversity/pairs:0.,pop.empty()?0.:pop[0].f,elapsed());
    return pop;
}

static vector<Cand> geometry_start(const Inst& I,const Fast& F,const map<vector<int>,Cand>& cache,
        uint64_t seed,double end,double limit,int mode) {
    vector<Cand> sorted;for(const auto& kv:cache)if(kv.second.f>NEG/2)sorted.push_back(kv.second);
    stable_sort(sorted.begin(),sorted.end(),[](const Cand&a,const Cand&b){return a.f>b.f;});
    vector<Cand> seeds;set<vector<int>> have;set<size_t> sizes;
    for(size_t i=0;i<min<size_t>(4,sorted.size());i++){seeds.push_back(sorted[i]);have.insert(sorted[i].op);sizes.insert(sorted[i].op.size());}
    for(const auto& c:sorted)if(sizes.insert(c.op.size()).second){seeds.push_back(c);have.insert(c.op);}
    for(const auto& c:sorted)if(seeds.size()<24&&have.insert(c.op).second)seeds.push_back(c);
    int nt=min(2,detect_cpus());
    // Warm threads precede the native workers: apply their arena limit here too.
    mallopt(M_ARENA_MAX,nt+2);
    vector<vector<Cand>> results(nt);vector<thread> threads;
    for(int t=1;t<nt;t++)threads.emplace_back([&,t](){results[t]=geometry_start_lane(I,F,seeds,seed^(0xBAD5EEDULL*t),end,limit,t,mode);});
    results[0]=geometry_start_lane(I,F,seeds,seed,end,limit,0,mode);
    for(auto& t:threads)t.join();vector<Cand> merged;
    for(auto& v:results)for(auto& c:v)merged.push_back(move(c));gw_trim(merged,12);
    for(const auto& c:merged){Sol s;s.init(I);s.load_state(c.asg,c.open);try_elite(I,s);}
    fprintf(stderr,"GEOWARM merged=%zu t=%.3f\n",merged.size(),elapsed());
    return merged;
}
