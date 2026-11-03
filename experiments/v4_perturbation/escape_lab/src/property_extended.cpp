#define main frozen_escape_main
#include "escape_v4.cpp"
#undef main
#include "../../shared/checkpoint.h"
int main(int argc,char**argv){
 if(argc!=3)return 2;g_wdfs_deadline=100;Inst I=load_instance(argv[1]);g_geo_grid.init(I);Sol s;checkpoint_load(I,argv[2],s);
 setenv("ESCAPE_MODE","0",1);EscapeControl off(s,100,1);Engine E(s);E.rec=true;Guide G(s,0);double cur=G.val();
 mt19937_64 a(717),b(717);uniform_real_distribution<double>u(0,1);long checks=0;
 auto initial=s.asg;auto opened=s.isopen;
 for(int j=0;j<10000;j++){double d=(j%29-17)*.125,T=.001+(j%113)*.01;bool x=d>-1e-12||u(a)<exp(d/max(1e-12,T));bool y=off.accept(d,T,b,u,E);if(x!=y)return 3;checks++;}
 if(a()!=b())return 4;off.tick(E,G,a,cur,elapsed());off.finish(E,G,cur);if(s.asg!=initial||s.isopen!=opened)return 5;
 setenv("ESCAPE_MODE","3",1);EscapeControl c(s,100,1);mt19937_64 rng(991);
 for(int j=0;j<2000;j++){
  c.hash=c.state_hash();size_t mark=E.jr.size();int x=rng()%max(1,I.ns);
  if(I.ns&&s.asg[x]>=0){int o=s.asg[x];E.doRemove(x);if(c.trial_hash(E)!=c.state_hash())return 6;if(rng()%2)E.doAdd(x,o);}
  else if(I.ns){for(int o=0;o<I.no;o++)if(s.isopen[o]){E.doAdd(x,o);break;}}
  if(c.trial_hash(E)!=c.state_hash())return 7;
  E.undo(mark);if(c.hash!=c.state_hash())return 8;
  if(s.asg!=initial||s.isopen!=opened)return 9;checks++;
 }

 for(int o=0;o<I.no;o++){
  c.hash=c.state_hash();size_t mark=E.jr.size();
  if(s.isopen[o])E.doClose(o);else E.doOpen(o);
  if(c.trial_hash(E)!=c.state_hash())return 11;
  E.undo(mark);if(c.hash!=c.state_hash()||s.asg!=initial||s.isopen!=opened)return 12;checks++;
 }
 Sol rebuilt;rebuilt.init(I);rebuilt.load_state(initial,opened);
 if(s.size_!=rebuilt.size_||s.load!=rebuilt.load||s.need!=rebuilt.need||s.cntSkill!=rebuilt.cntSkill||s.cov!=rebuilt.cov||s.incov!=rebuilt.incov||s.sig!=rebuilt.sig)return 13;
 vector<int>w;double v;if(!s.greedy_workers(&w)||!verify(I,s.asg,s.isopen,w,&v))return 10;
 fprintf(stderr,"property checks=%ld all_off_rng_equal=1 journal_hash_equal=1 rollback_equal=1 state_rebuild_equal=1 office_journal_equal=1 valid=1\n",checks);return 0;
}
