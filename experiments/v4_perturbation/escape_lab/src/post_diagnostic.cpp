#define main frozen_escape_main
#include "escape_diagnostic_v4.cpp"
#undef main
#include "../../shared/checkpoint.h"
static void escape_search(Sol&s,mt19937_64&r,double end,int mode,int tid){lns(s,r,end,end,true);}
int main(int argc,char**argv){if(argc!=6)return 2;setenv("ESCAPE_MODE",argv[5],1);return checkpoint_main(argc,argv,escape_search);}
