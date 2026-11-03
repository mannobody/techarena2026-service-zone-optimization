#define main original_main
#include "../../../v4_local_search/baseline/frozen_v4.cpp"
#undef main
#include <cassert>
int main(int argc,char**argv){
 Inst I=load_instance(argv[1]);g_geo_grid.init(I);Sol s;s.init(I);
 vector<int>a{0,0,0,1,1,1};vector<char>op{1,1};s.load_state(a,op);
 double initial=s.objective();resize_dp(s,elapsed()+10);double relaxed=s.objective();
 int c0=s.size_[0],c1=s.size_[1];repair_sizes(s);double repaired=s.objective();
 vector<int>joint{0,0,-1,1,1,-1};s.load_state(joint,op);double exact=s.objective();
 assert(fabs(initial-65)<1e-9);assert(fabs(relaxed-135)<1e-9);
 assert(c0==2 && c1==3);assert(fabs(repaired-10)<1e-9);assert(fabs(exact-110)<1e-9);
 assert(s.greedy_workers(nullptr));Engine E(s);assert(E.size_viol(-1,-1)==0);
 printf("{\"initial\":%.9f,\"load_dp\":%.9f,\"repaired\":%.9f,\"joint\":%.9f,\"pass\":true}\n",initial,relaxed,repaired,exact);
}
