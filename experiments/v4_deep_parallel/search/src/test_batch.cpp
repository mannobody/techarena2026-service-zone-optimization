#define main service_zone_main
#include "lab.cpp"
#undef main
#include <cassert>
static void state_equal(const Sol& s) {
    Sol ref;ref.init(*s.I);ref.load_state(s.asg,s.isopen);
    assert(s.size_==ref.size_ && s.load==ref.load && s.need==ref.need && s.cntSkill==ref.cntSkill);
    assert(s.cov==ref.cov && s.incov==ref.incov && s.sig==ref.sig && !s.defer);
    assert(fabs(s.objective()-ref.objective())<1e-7);
    for(int o=0;o<s.I->no;o++){
        auto a=s.covlist[o],b=ref.covlist[o];sort(a.begin(),a.end());sort(b.begin(),b.end());assert(a==b);
    }
}
int main(){
    long tested=0,accepted=0,rejected=0;g_wdfs_deadline=1e6;
    for(int seed=0;seed<80;seed++){
        mt19937_64 rng(seed);Inst I;I.ns=12;I.no=3;I.nw=6;I.nsk=2;I.A=seed%3==0?0:12;
        I.ext=40;I.eps_len=1e-10;I.eps_cr=1e-10;I.alpha=seed%2?100:0;
        I.reward.assign(I.ns,100);I.cost.assign(I.no,1);I.D.assign(I.ns*I.no,0);
        I.prof.resize(I.ns*I.no);for(auto&x:I.prof)x=10+rng()%90;
        I.ntask.resize(I.ns);for(auto&x:I.ntask)x=rng()%5;
        I.maxsize.assign(I.no,6);I.servable.assign(I.ns,1);I.Nk.assign(2,3);
        I.skillset.resize(I.ns);for(auto&v:I.skillset)v={int(rng()%2)};
        I.wskills={{0},{0},{0},{1},{1},{1}};I.wmask={{1,0},{1,0},{1,0},{0,1},{0,1},{0,1}};
        if(seed%4==0){I.simple_workers=false;I.wskills={{0,1},{0,1},{0},{1}};I.wmask={{1,1},{1,1},{1,0},{0,1}};I.nw=4;}
        for(int x=0;x<I.ns;x++)I.P.push_back({double(int(rng()%15)-7),seed%5==0?0.:double(int(rng()%15)-7)});
        I.P.insert(I.P.end(),{{-12,-12},{12,-12},{0,12}});g_geo_grid.init(I);
        Sol s;s.init(I);Engine E(s);for(int o=0;o<I.no;o++)E.doOpen(o);
        for(int x=0;x<I.ns;x++){
            auto old=s.asg;auto op=s.isopen;
            E.doAdd(x,rng()%I.no);
            if(E.size_viol(-1,-1)>0 || !s.greedy_workers(nullptr))s.load_state(old,op);
        }
        Sol a=s,b=s; Engine ea(a),eb(b); ea.rec=eb.rec=true;
        for(int i=0;i<300;i++) {
            vector<int> xs(I.ns);iota(xs.begin(),xs.end(),0);shuffle(xs.begin(),xs.end(),rng);
            vector<pair<int,int>> moves;for(int k=0;k<6;k++) moves.push_back({xs[k],int(rng()%(I.no+1))-1});
            auto run=[&](Sol& z,Engine& e,bool batch){
                setenv("LAB_BATCH",batch?"1":"0",1);size_t mark=e.jr.size();z.begin_defer();
                for(auto m:moves)if(z.asg[m.first]>=0)e.doRemove(m.first);z.end_defer();
                for(auto m:moves)if(m.second>=0)e.doAdd(m.first,m.second);
                state_equal(z);return mark;
            };
            size_t ma=run(a,ea,false),mb=run(b,eb,true);
            assert(a.asg==b.asg && a.isopen==b.isopen && a.cov==b.cov && a.incov==b.incov);
            setenv("LAB_BATCH","0",1);ea.undo(ma);setenv("LAB_BATCH","1",1);eb.undo(mb);
            state_equal(a);state_equal(b);assert(a.asg==s.asg && b.asg==s.asg);tested++;
        }
    }
    printf("batch differential transactions=%ld state checks=%ld\n",tested,4*tested);
}
