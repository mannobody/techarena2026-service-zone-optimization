#define main candidate_main
#include "../artifacts/main.cpp"
#undef main
#include "../../v4_perturbation/shared/checkpoint.h"
static void search(Sol&s,mt19937_64&r,double end,int mode,int tid){
    if(mode==0){while(elapsed()<end){long n=boundary_stats.calls;boundary_move(s,r,min(end,elapsed()+.04),1,1,24);
        if(n==boundary_stats.calls)break;if(s.objective_fast()>g_best.load()+1e-9)offer(*s.I,s);}}
    else if(mode==4){while(elapsed()<end)lns(s,r,end,end,true);}
    else{int calls=0;int q=getenv("XN_Q")?atoi(getenv("XN_Q")):12;
        while(elapsed()<end){XNStats st;int use=mode==3?(++calls%2?1:2):mode;
            xn_move(s,r,min(end,elapsed()+.04),use,q,&st);if(!st.nodes)break;}}
}
int main(int argc,char**argv){return checkpoint_main(argc,argv,search);}
