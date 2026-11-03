#define main frozen_v4_main
#include "../baseline/frozen_v4.cpp"
#undef main
#include "checkpoint.h"
static void search(Sol&s,mt19937_64&r,double end,int mode,int tid){
 if(mode==0)lns(s,r,end,end,true);
 else if(mode==1)polish(s,r,end,end);
 else if(mode==2){while(elapsed()<end){long n=boundary_stats.calls;boundary_move(s,r,min(end,elapsed()+.04),1,1,24);if(n==boundary_stats.calls)break;if(s.objective_fast()>g_best.load()+1e-9)offer(*s.I,s);}}
}
int main(int argc,char**argv){return checkpoint_main(argc,argv,search);}
