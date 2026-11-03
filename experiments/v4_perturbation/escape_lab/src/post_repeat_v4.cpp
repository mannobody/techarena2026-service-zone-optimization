#define main frozen_v4_main
#include "../../../v4_local_search/baseline/frozen_v4.cpp"
#undef main
#include "../../shared/checkpoint.h"
static void repeat_search(Sol&s,mt19937_64&r,double end,int mode,int tid){while(elapsed()+.005<end)lns(s,r,end,end,true);}
int main(int argc,char**argv){return checkpoint_main(argc,argv,repeat_search);}
