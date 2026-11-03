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
int main(int argc,char**argv){
    long tested=0,accepted=0,rejected=0;g_wdfs_deadline=1e6;
    for(int seed=atoi(argv[1]);seed<=atoi(argv[1]);seed++){
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
        I.simple_workers=false;Sol s;s.init(I);setenv("LAB_MEMO","1",1);
        for(int it=0;it<1500;it++) {
            vector<int>a(I.ns);vector<char>op(I.no,1);for(int&x:a)x=int(rng()%(I.no+1))-1;s.load_state(a,op);
            vector<int>w,ref;bool uncached=s.uncached_workers(&ref);
            for(int hit=0;hit<3;hit++) {
                bool ok=s.greedy_workers(&w);assert(!uncached || ok);
                if(ok){assert((int)w.size()==I.nw);for(int k=0;k<I.nw;k++)if(w[k]>=0)assert(w[k]<I.no && s.isopen[w[k]] && s.size_[w[k]]>0);
                    for(int o=0;o<I.no;o++)for(int k=0;k<I.nsk;k++)if(s.need[o][k]>0){bool have=false;for(int z=0;z<I.nw;z++)if(w[z]==o && I.wmask[z][k])have=true;assert(have);}accepted++;}
                else rejected++;tested++;
            }
        }
    }
    printf("memo certificate checks=%ld true=%ld false=%ld\n",tested,accepted,rejected);
}
