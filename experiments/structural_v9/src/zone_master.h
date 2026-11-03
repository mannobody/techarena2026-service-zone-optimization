// Whole-zone master. Full subset enumeration on small instances; restricted
// pattern optimization otherwise. No polygon-intersection surrogate is used.
#include <sys/time.h>
namespace zm {
static void deadline_signal(int signal) {
    static const char msg[]="ZM deadline_stop=1\n";
    (void)!write(STDERR_FILENO,msg,sizeof(msg)-1);on_signal(signal);
}
struct Zone {
    int office=0, count=0, load=0;
    double value=0;
    uint64_t skills=0;
    vector<int> sites;
    vector<uint64_t> footprint;
};
struct Master {
    const Inst& I;
    double end;
    bool full, complete=true;
    long nodes=0, worker_nodes=0, generated=0, checks=0;
    vector<vector<Zone>> zones;
    vector<uint64_t> worker, site_skill;
    vector<int> order, chosen, bestchosen;
    vector<uint64_t> occupied;
    vector<int> skill_use;
    vector<vector<double>> future_site;
    vector<double> future_zone;
    double incumbent=0;
    int words;
    Master(const Inst& in,double until,bool exhaustive):I(in),end(until),full(exhaustive),
        zones(I.no),worker(I.nw),site_skill(I.ns),occupied((I.ns+I.no+63)/64),skill_use(I.nsk),words(occupied.size()) {
        for(int w=0;w<I.nw;w++)for(int k:I.wskills[w])worker[w]|=1ULL<<k;
        for(int x=0;x<I.ns;x++)for(int k:I.skillset[x])site_skill[x]|=1ULL<<k;
        incumbent=g_best.load();
    }
    bool expired() { if(elapsed()<end)return false;complete=false;return true; }
    bool conflict(const Zone& z)const {
        for(int j=0;j<words;j++)if(z.footprint[j]&occupied[j])return true;
        return false;
    }
    void insert(int o,const vector<int>& sites) {
        if(sites.empty()||sites.size()>(size_t)I.maxsize[o])return;
        Zone z;z.office=o;z.sites=sites;z.count=sites.size();z.value=-I.cost[o];
        vector<Pt> h{I.P[I.ns+o]};
        for(int x:sites){if(!I.servable[x])return;z.load+=I.ntask[x];z.value+=I.pr(o,x);z.skills|=site_skill[x];h.push_back(I.P[x]);}
        // Deleting a nonpositive complete zone relaxes every constraint and
        // cannot increase the load range (alpha >= 0). Negative sites ARE kept.
        if(z.value<=0)return;
        hull_of(h);z.footprint.assign(words,0);
        for(int p=0;p<I.ns+I.no;p++)if(geo_exact_covers(h,I.P[p]))z.footprint[p/64]|=1ULL<<(p%64);
        generated++;zones[o].push_back(move(z));
    }
    void enumerate() {
        const unsigned M=1U<<I.ns;
        vector<int> counts(M),loads(M);vector<uint64_t> skills(M);
        for(unsigned m=1;m<M;m++){unsigned p=m&(m-1);int x=__builtin_ctz(m);counts[m]=counts[p]+1;loads[m]=loads[p]+I.ntask[x];skills[m]=skills[p]|site_skill[x];}
        for(int o=0;o<I.no;o++) {
            vector<double> profit(M,-I.cost[o]);
            for(unsigned m=1;m<M;m++) {
                if((m&127)==0&&expired())return;
                unsigned p=m&(m-1);int x=__builtin_ctz(m);profit[m]=profit[p]+I.pr(o,x);
                if(counts[m]>I.maxsize[o]||profit[m]<=0)continue;
                vector<int> v;for(unsigned t=m;t;t&=t-1)v.push_back(__builtin_ctz(t));
                insert(o,v);
            }
        }
    }
    void patterns(mt19937_64& rng) {
        // Keep every elite zone; add resized/reshaped versions and independent
        // road / radial / load-priced zones, including presently closed offices.
        vector<Elite> elite;{lock_guard<mutex> lk(g_el_mx);elite=g_elite;}
        for(auto&e:elite)for(int o=0;o<I.no;o++) {
            if(expired())return;
            vector<int> v;for(int x=0;x<I.ns;x++)if(e.asg[x]==o)v.push_back(x);
            if(v.empty())continue;insert(o,v);
            sort(v.begin(),v.end(),[&](int a,int b){return I.pr(o,a)>I.pr(o,b);});
            for(int d=1;d<=min(5,(int)v.size()-1);d++){auto q=v;q.resize(v.size()-d);insert(o,q);}
        }
        // Reshape intact donor territories. Count x task-load DP can change many
        // assignments together; the master decides which counts/loads/offices to
        // combine. This directly revisits the limited old intact-zone oracle.
        if(!elite.empty())for(int o=0;o<I.no&&!expired();o++) {
            vector<Pt> h{I.P[I.ns+o]};int oldcount=0;
            for(int x=0;x<I.ns;x++)if(elite[0].asg[x]==o){h.push_back(I.P[x]);oldcount++;}
            if(!oldcount)continue;hull_of(h);
            vector<int> pool;int W=0;
            for(int x=0;x<I.ns;x++)if(I.servable[x]&&geo_exact_covers(h,I.P[x])){pool.push_back(x);W+=I.ntask[x];}
            int C=min(I.maxsize[o],(int)pool.size()),stride=W+1;size_t states=(size_t)(C+1)*stride;
            if(states*pool.size()>12000000ULL||C>100||W>800)continue;
            vector<double> f(states,NEG);f[0]=0;
            size_t words=(states+63)/64;vector<uint64_t> take(pool.size()*words);
            for(int j=0;j<(int)pool.size();j++) {
                if(expired())return;int x=pool[j],w=I.ntask[x];double p=I.pr(o,x);
                for(int c=min(j+1,C);c>=1;c--)for(int l=W;l>=w;l--) {
                    size_t idx=(size_t)c*stride+l;double a=f[idx-stride-w];
                    if(a>NEG/2&&a+p>f[idx]+1e-12){f[idx]=a+p;take[(size_t)j*words+idx/64]|=1ULL<<(idx%64);}
                }
            }
            // All load states for nearby counts, coarse counts further away.
            for(int c=1;c<=C&&!expired();c++) {
                if(abs(c-oldcount)>3&&c%max(1,C/12)!=0&&c!=C)continue;
                for(int l=0;l<=W&&!expired();l++)if(f[(size_t)c*stride+l]-I.cost[o]>0) {
                    int cc=c,ll=l;vector<int> v;
                    for(int j=(int)pool.size()-1;j>=0&&cc;j--) {
                        size_t idx=(size_t)cc*stride+ll;
                        if(take[(size_t)j*words+idx/64]>>(idx%64)&1){int x=pool[j];v.push_back(x);cc--;ll-=I.ntask[x];}
                    }
                    if(!cc&&!ll)insert(o,v);
                }
            }
        }
        double scale=0;for(double r:I.reward)scale+=fabs(r);scale/=max(1,I.ns);
        for(int pass=0;pass<32&&!expired();pass++)for(int o=0;o<I.no&&!expired();o++) {
            vector<pair<double,int>> rank;
            uint64_t allowed=~0ULL;
            if(pass>=12&&I.nw){allowed=0;int n=1+rng()%max(1,I.nw);for(int j=0;j<n;j++)allowed|=worker[rng()%I.nw];}
            double price=pass<4?0:scale*((int)(rng()%17)-8)/8.;
            double theta=(rng()%1000000)*2*M_PI/1000000.;
            for(int x=0;x<I.ns;x++)if(I.servable[x]&&!(site_skill[x]&~allowed)) {
                double dx=I.P[x].x-I.P[I.ns+o].x,dy=I.P[x].y-I.P[I.ns+o].y;
                double metric=I.pr(o,x)+price*I.ntask[x];
                if(pass%4==1)metric-=scale*hypot(dx,dy)/max(1e-100,I.ext);
                if(pass%4==2)metric+=scale*(dx*cos(theta)+dy*sin(theta))/max(1e-100,I.ext);
                if(pass>=8)metric+=scale*((int)(rng()%10001)-5000)/10000.;
                rank.push_back({metric,x});
            }
            sort(rank.rbegin(),rank.rend());
            vector<int> v;int cap=min(I.maxsize[o],(int)rank.size());
            int stride=max(1,cap/24);
            for(int j=0;j<cap&&!expired();j++) {
                v.push_back(rank[j].second);
                if(j<8||(j+1)%stride==0||j+1==cap)insert(o,v);
            }
        }
    }
    void prepare() {
        for(int o=0;o<I.no;o++) {
            auto&v=zones[o];
            // Identical (count,load,skills,footprint) have identical master
            // constraints. Keep only maximum value, including full enumeration.
            sort(v.begin(),v.end(),[](const Zone&a,const Zone&b){
                if(a.count!=b.count)return a.count<b.count;if(a.load!=b.load)return a.load<b.load;
                if(a.skills!=b.skills)return a.skills<b.skills;if(a.footprint!=b.footprint)return a.footprint<b.footprint;return a.value>b.value;});
            v.erase(unique(v.begin(),v.end(),[](const Zone&a,const Zone&b){return a.count==b.count&&a.load==b.load&&a.skills==b.skills&&a.footprint==b.footprint;}),v.end());
            sort(v.begin(),v.end(),[](const Zone&a,const Zone&b){return a.value>b.value;});
            if(!v.empty())order.push_back(o);
        }
        sort(order.begin(),order.end(),[&](int a,int b){return zones[a][0].value>zones[b][0].value;});
        chosen.assign(I.no,-1);bestchosen=chosen;
        future_site.assign(order.size()+1,vector<double>(I.ns,0));future_zone.assign(order.size()+1,0);
        for(int d=(int)order.size()-1;d>=0;d--){int o=order[d];future_zone[d]=future_zone[d+1]+zones[o][0].value;
            for(int x=0;x<I.ns;x++)future_site[d][x]=max(future_site[d+1][x],I.servable[x]?max(0.,I.pr(o,x)):0.);}
    }
    // Exact staffing search: select an uncovered office/skill, assign one real
    // unused worker, reuse all its skills within that office. Equal profiles
    // are symmetric at a node. Deadline returns unknown, never false proof.
    bool staffing(vector<int>& assignment) {
        vector<uint64_t> need(I.no),have(I.no);assignment.assign(I.nw,-1);
        for(int o:order)if(chosen[o]>=0)need[o]=zones[o][chosen[o]].skills;
        auto dfs=[&](auto&&self)->bool {
            worker_nodes++;if((worker_nodes&63)==0&&expired())return false;
            int bo=-1,bk=-1,bn=INT_MAX;
            for(int o:order)for(uint64_t r=need[o]&~have[o];r;r&=r-1) {
                int k=__builtin_ctzll(r),n=0;for(int w=0;w<I.nw;w++)if(assignment[w]<0&&(worker[w]>>k&1))n++;
                if(!n)return false;if(n<bn){bo=o;bk=k;bn=n;}
            }
            if(bo<0)return true;
            vector<uint64_t> seen;vector<pair<int,int>> choices;
            for(int w=0;w<I.nw;w++)if(assignment[w]<0&&(worker[w]>>bk&1)) {
                if(find(seen.begin(),seen.end(),worker[w])!=seen.end())continue;seen.push_back(worker[w]);
                choices.push_back({__builtin_popcountll(worker[w]&need[bo]&~have[bo]),w});
            }
            sort(choices.rbegin(),choices.rend());uint64_t old=have[bo];
            for(auto p:choices){int w=p.second;assignment[w]=bo;have[bo]|=worker[w];
                if(self(self))return true;have[bo]=old;assignment[w]=-1;if(!complete)return false;}
            return false;
        };
        return dfs(dfs);
    }
    void accept(double value) {
        if(value<=incumbent+1e-9)return;
        checks++;vector<int> wof;if(!staffing(wof))return;
        vector<int> asg(I.ns,-1);vector<char> op(I.no,0);
        for(int o:order)if(chosen[o]>=0){op[o]=1;for(int x:zones[o][chosen[o]].sites)asg[x]=o;}
        double actual=0;if(!verify(I,asg,op,wof,&actual))throw runtime_error("zone master certificate mismatch");
        incumbent=actual;bestchosen=chosen;
        lock_guard<mutex> lk(g_best_mx);
        if(actual>g_best.load()+1e-9){g_best.store(actual);g_best_asg=asg;g_best_open=op;publish(serialize(I,asg,op,wof));push_elite(actual,asg,op);}
    }
    void search(int depth,double profit,int cmin,int cmax,int lmin,int lmax) {
        nodes++;if((nodes&63)==0&&expired())return;
        double penalty=lmin==INT_MAX?0:I.alpha*(lmax-lmin);
        if(depth==(int)order.size()){accept(profit-penalty);return;}
        accept(profit-penalty);
        // Independent relaxation: every still-uncovered site may choose its
        // best remaining office, with costs/geometry/workers all dropped.
        double sitebound=profit-penalty;
        for(int x=0;x<I.ns;x++)if(!(occupied[x/64]>>(x%64)&1))sitebound+=future_site[depth][x];
        if(sitebound<=incumbent+1e-9)return;
        double bound=profit-penalty;
        for(int d=depth;d<(int)order.size();d++) {
            for(auto&z:zones[order[d]]) {
                if(cmin!=INT_MAX&&(long long)max(cmax,z.count)-min(cmin,z.count)>I.A)continue;
                if(!conflict(z)){bound+=z.value;break;}
            }
        }
        if(bound<=incumbent+1e-9)return;
        int o=order[depth];
        for(int j=0;j<(int)zones[o].size();j++) {
            if((j&255)==0&&expired())return;
            const Zone&z=zones[o][j];int mn=min(cmin,z.count),mx=max(cmax,z.count);
            if(profit+z.value+future_zone[depth+1]-penalty<=incumbent+1e-9)break;
            if((long long)mx-mn>I.A||conflict(z))continue;
            bool enough=true;for(uint64_t sk=z.skills;sk;sk&=sk-1){int k=__builtin_ctzll(sk);if(skill_use[k]>=I.Nk[k]){enough=false;break;}}
            if(!enough)continue;
            for(int k=0;k<I.nsk;k++)skill_use[k]+=(z.skills>>k)&1;
            for(int k=0;k<words;k++)occupied[k]|=z.footprint[k];chosen[o]=j;
            search(depth+1,profit+z.value,mn,mx,min(lmin,z.load),max(lmax,z.load));
            chosen[o]=-1;for(int k=0;k<words;k++)occupied[k]^=z.footprint[k];
            for(int k=0;k<I.nsk;k++)skill_use[k]-=(z.skills>>k)&1;
            if(!complete)return;
        }
        search(depth+1,profit,cmin,cmax,lmin,lmax);
    }
};
static bool eligible(const Inst&I) {
    return g_geo_exact&&I.nsk<=63&&I.alpha>=0&&all_of(I.cost.begin(),I.cost.end(),[](double x){return x>=0;});
}
static bool tiny(const Inst&I,double limit) {
    if(!eligible(I)||I.ns>16||I.no>6||I.nw>32||getenv("ZM_DISABLE"))return false;
    double start=elapsed(),end=min(limit-max(.25,.002*limit),start+min(5.,.30*limit));
    if(end<=start)return false;Master m(I,end,true);m.enumerate();
    if(m.complete&&!m.expired()){m.prepare();m.search(0,0,INT_MAX,0,INT_MAX,0);}
    fprintf(stderr,"ZM full=1 complete=%d generated=%ld nodes=%ld workers=%ld objective=%.9f seconds=%.6f threads=1\n",m.complete,m.generated,m.nodes,m.worker_nodes,g_best.load(),elapsed()-start);
    return m.complete;
}
static void finish(const Inst&I,double limit) {
    if(getenv("ZM_DISABLE")||(getenv("ZM_POOL")&&!atoi(getenv("ZM_POOL")))||!eligible(I)||I.ns>1500||I.no>16||I.nw>128)return;
    double start=elapsed(),end=limit-max(.25,.002*limit);if(end-start<.08)return;
    Master m(I,end,false);uint64_t seed=getenv("SEED")?strtoull(getenv("SEED"),nullptr,10):0;mt19937_64 rng(seed^0x395ADE78ULL);
    m.end=min(end,start+.40*(end-start));m.patterns(rng);m.complete=true;m.end=end;
    m.prepare();m.search(0,0,INT_MAX,0,INT_MAX,0);
    fprintf(stderr,"ZM full=0 complete=%d generated=%ld nodes=%ld workers=%ld checks=%ld objective=%.9f seconds=%.6f\n",m.complete,m.generated,m.nodes,m.worker_nodes,m.checks,g_best.load(),elapsed()-start);
}
} // namespace zm
