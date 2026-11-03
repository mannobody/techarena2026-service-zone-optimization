#include <cassert>
#define main candidate_main
#include "../artifacts/main.cpp"
#undef main
static uint64_t canonical(const Sol&s){uint64_t h=0;const Inst&I=*s.I;
    for(int o=0;o<I.no;o++){if(s.isopen[o])h^=s.sigkey[(size_t)I.no*I.nsk+o];
        for(int k=0;k<I.nsk;k++)if(s.need[o][k])h^=s.sigkey[(size_t)o*I.nsk+k];}return h;}
int main(int argc,char**argv){
    if(argc!=2)return 2;Inst I=load_instance(argv[1]);g_geo_grid.init(I);g_wdfs_deadline=10;
    Sol s;s.init(I);s.open_office(0);assert(s.sig==canonical(s));s.close_office(0);
    bool closed_ok=s.sig==canonical(s);
    s.init(I);s.open_office(0);s.open_office(1);Engine E(s);bool a=E.doAdd(0,0),b=E.doAdd(1,1);
    vector<int>w;double f;assert(a&&b&&s.greedy_workers(&w)&&verify(I,s.asg,s.isopen,w,&f));
    Sol rebuilt;rebuilt.init(I);rebuilt.load_state(s.asg,s.isopen);assert(s.cov==rebuilt.cov&&s.sig==rebuilt.sig);
    mt19937_64 rng(991);int checks=0;
    for(int it=0;it<2000;it++){
        int x=rng()%I.ns,o=rng()%I.no;
        if(s.asg[x]>=0)s.remove_site(x);else E.doAdd(x,o);
        rebuilt.load_state(s.asg,s.isopen);
        assert(s.cov==rebuilt.cov&&s.incov==rebuilt.incov&&s.size_==rebuilt.size_&&s.load==rebuilt.load&&s.need==rebuilt.need&&s.sig==rebuilt.sig);checks++;
    }
    printf("{\"close_signature_ok\":%s,\"crossing_accepted\":true,\"state_checks\":%d}\n",closed_ok?"true":"false",checks);
}
