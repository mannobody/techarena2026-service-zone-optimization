#define main service_zone_main
#include "lab.cpp"
#undef main
#include <cassert>
static uint64_t rebuilt_signature(const Sol&s){Sol r;r.init(*s.I);r.load_state(s.asg,s.isopen);return r.sig;}
int main(){
 Inst I;I.ns=1;I.no=1;I.nw=1;I.nsk=1;I.A=1;I.ext=10;I.alpha=0;I.eps_len=I.eps_cr=1e-10;
 I.P={{1,1},{0,0}};I.reward={10};I.cost={1};I.D={1};I.prof={9};I.ntask={1};I.skillset={{0}};I.Nk={1};I.maxsize={2};I.servable={1};I.wskills={{0}};I.wmask={{1}};g_geo_grid.init(I);
 for(int fix=0;fix<2;fix++) {
  Sol s;s.init(I);s.open_office(0);s.force_add(0,0);assert(s.sig==rebuilt_signature(s));
  s.close_office(0);if(fix)s.sig_open(0); // Exactly the proposed one-line correction.
  bool close_ok=s.sig==rebuilt_signature(s);
  s.open_office(0);bool reopen_ok=s.sig==rebuilt_signature(s);
  printf("sig_fix=%d direct_close_matches=%d reopen_matches=%d\n",fix,close_ok,reopen_ok);
  assert(close_ok==bool(fix) && reopen_ok==bool(fix));
 }
}
