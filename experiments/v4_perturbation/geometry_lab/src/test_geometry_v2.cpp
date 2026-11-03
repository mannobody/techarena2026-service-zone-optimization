#define main frozen_main
#include "../../../v4_local_search/baseline/frozen_v4.cpp"
#undef main
#include "geometry_perturb_v2.h"
#include <cassert>
static void check(const Sol&s){
 Sol r;r.init(*s.I);r.load_state(s.asg,s.isopen);
 assert(s.size_==r.size_&&s.load==r.load&&s.need==r.need&&s.cntSkill==r.cntSkill);
 assert(s.cov==r.cov&&s.incov==r.incov&&s.sig==r.sig);
 assert(fabs(s.psum-r.psum)<1e-7);
 for(int o=0;o<s.I->no;++o){auto a=s.covlist[o],b=r.covlist[o];sort(a.begin(),a.end());sort(b.begin(),b.end());assert(a==b);assert(gp_hull_equal(s.hull[o],r.hull[o]));}
 vector<int>w;double value;assert(s.greedy_workers(&w));assert(verify(*s.I,s.asg,s.isopen,w,&value));
}
int main(){
 g_wdfs_deadline=1e6;long accepted=0,rejected=0,tested=0;
 for(int seed=0;seed<100;++seed){
  mt19937_64 rng(seed);Inst I;I.ns=24;I.no=3;I.nw=6;I.nsk=2;I.A=24;
  I.ext=40;I.eps_len=1e-10;I.eps_cr=1e-10;I.alpha=seed%2?100:0;
  I.reward.assign(I.ns,100);I.cost.assign(I.no,1);I.D.assign(I.ns*I.no,0);
  I.prof.resize(I.ns*I.no);for(auto&v:I.prof)v=10+rng()%90;
  I.ntask.resize(I.ns);for(auto&v:I.ntask)v=seed%3?1:rng()%3;
  I.maxsize.assign(I.no,12);I.servable.assign(I.ns,1);I.Nk.assign(2,3);
  I.skillset.resize(I.ns);for(auto&v:I.skillset)v={int(rng()%2)};
  I.wskills={{0},{0},{0},{1},{1},{1}};I.wmask={{1,0},{1,0},{1,0},{0,1},{0,1},{0,1}};
  if(seed%4==0){I.simple_workers=false;I.wskills={{0,1},{0,1},{0},{1}};I.wmask={{1,1},{1,1},{1,0},{0,1}};I.nw=4;}
  for(int x=0;x<I.ns;++x)I.P.push_back({double(int(rng()%15)-7),seed%5==0?0.:double(int(rng()%15)-7)});
  I.P.insert(I.P.end(),{{-12,-12},{12,-12},{0,12}});g_geo_grid.init(I);
  Sol s;s.init(I);Engine E(s);for(int o=0;o<I.no;++o)E.doOpen(o);
  for(int x=0;x<I.ns;++x){auto old=s.asg;auto op=s.isopen;E.doAdd(x,rng()%I.no);if(E.size_viol(-1,-1)||!s.greedy_workers(nullptr))s.load_state(old,op);}
  for(int it=0;it<300;++it){
   Sol old=s;vector<int>xs,to;int x=rng()%I.ns,y=rng()%I.ns,z=rng()%I.ns;
   if(it%3==0){xs={x,y};to={s.asg[y],s.asg[x]};}
   else if(it%3==1){xs={x,y,z};to={s.asg[y],s.asg[z],s.asg[x]};}
   else {int w=rng()%I.ns;xs={x,y,z,w};to={s.asg[z],s.asg[w],s.asg[x],s.asg[y]};}
   GeometryStats st;bool ok=gp_transaction(s,xs,to,1000,st,it%2);++tested;
   if(ok){++accepted;assert(s.size_==old.size_&&s.load==old.load&&s.isopen==old.isopen);}
   else{++rejected;assert(s.asg==old.asg&&s.isopen==old.isopen);}
   check(s);s=old;
  }
 }
 printf("checks=%ld accepted=%ld rejected=%ld full_rebuild=30000 independent_verify=30000\n",tested,accepted,rejected);
}
