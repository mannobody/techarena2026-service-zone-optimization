#define main service_zone_main
#include "../../../solver/solve.cpp"
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
        I.P.insert(I.P.end(),{{-12,-12},{12,-12},{0,12}});I.build_grid();g_geo_grid.init(I);
        Sol s;s.init(I);Engine E(s);for(int o=0;o<I.no;o++)E.doOpen(o);
        for(int x=0;x<I.ns;x++){
            auto old=s.asg;auto op=s.isopen;
            E.doAdd(x,rng()%I.no);
            if(E.size_viol(-1,-1)>0 || !s.greedy_workers(nullptr))s.load_state(old,op);
        }
        E.rec=true;
        for(int i=0;i<300;i++){
            auto old=s.asg;auto opened=s.isopen;size_t mark=E.jr.size();
            vector<int> xs(I.ns);iota(xs.begin(),xs.end(),0);shuffle(xs.begin(),xs.end(),rng);
            vector<pair<int,int>> changes;
            for(int k=0;k<(i%3==0?2:i%3==1?4:6);k++)changes.push_back({xs[k],int(rng()%(I.no+1))-1});
            bool ok=exchange_apply(E,changes);tested++;
            if(ok){accepted++;vector<int> w;double f;assert(s.greedy_workers(&w));assert(verify(I,s.asg,s.isopen,w,&f));state_equal(s);E.undo(mark);}
            else rejected++;
            assert(s.asg==old && s.isopen==opened && E.jr.size()==mark);state_equal(s);
        }
    }
    printf("exchange transaction oracle: checks=%ld accepted=%ld rejected=%ld\n",tested,accepted,rejected);
}
