// Research harness only. Contest main.cpp does not include this file.
#define main contest_main_not_called
#include "../artifacts/v2/main.cpp"
#undef main
#include <cassert>
int main(int argc,char**argv) {
    assert(argc==2);Inst I=load_instance(argv[1]);g_geo_grid.init(I);
    vector<int>a{0,0,-1,-1,-1},b{-1,-1,1,1,-1};vector<char>oa{1,0},ob{0,1};
    Sol sa,sb;sa.init(I);sb.init(I);sa.load_state(a,oa);sb.load_state(b,ob);
    vector<int>wa,wb;double fa,fb;
    assert(sa.greedy_workers(&wa)&&verify(I,a,oa,wa,&fa));
    assert(sb.greedy_workers(&wb)&&verify(I,b,ob,wb,&fb));
    assert(fabs(fa-20.)<1e-9&&fabs(fb-20.)<1e-9);
    setenv("GW_MODE","0",1);push_elite(fa,a,oa);push_elite(fb,b,ob);
    size_t legacy=g_elite.size();assert(legacy==1);g_elite.clear();
    setenv("GW_MODE","2",1);push_elite(fa,a,oa);push_elite(fb,b,ob);
    size_t spatial=g_elite.size();assert(spatial==2);
    vector<Pt>G(I.P.begin()+I.ns,I.P.end());vector<Cand>p;
    Cand ca;ca.f=fa;ca.asg=a;ca.open=oa;ca.op={0};ca.h={0.,0.};ca.G=G;
    Cand cb=ca;cb.asg=b;cb.open=ob;cb.op={1};p={ca,ca,cb,cb};gw_trim(p,2);
    assert(p.size()==2&&gw_distance(p[0].asg,p[1].asg)==1.);
    // Intact spatially disjoint zones can be joined atomically into objective 40.
    Sol child;child.init(I);Engine E(child);E.rec=true;
    for(auto* parent:{&ca,&cb})for(int o:parent->op){
        size_t mark=E.jr.size();E.doOpen(o);bool ok=child.isopen[o];
        for(int x=0;x<I.ns&&ok;x++)if(parent->asg[x]==o)ok=E.doAdd(x,o);
        if(!ok||!child.greedy_workers(nullptr))E.undo(mark);else E.jr.clear();
    }
    child.recompute_psum();vector<int>w;double f;
    assert(child.greedy_workers(&w)&&verify(I,child.asg,child.isopen,w,&f));assert(f==40.);
    // A second zone containing a witness already covered by zone 0 must roll back.
    Sol conflict;conflict.init(I);conflict.load_state(a,oa);Engine C(conflict);C.rec=true;
    size_t mark=C.jr.size();C.doOpen(1);bool ok=conflict.isopen[1]&&C.doAdd(4,1);
    if(!ok)C.undo(mark);assert(conflict.asg==a&&conflict.isopen==oa);
    printf("{\"parent_objectives\":[20,20],\"legacy_equal_score_elites\":%zu,\"new_elites\":%zu,\"assignment_distance\":1,\"whole_zone_child\":%.0f,\"conflict_rollback\":true}\n",legacy,spatial,f);
}
