#define main candidate_main
#include "../artifacts/candidate_v2/main.cpp"
#undef main
#include "../../v4_perturbation/shared/checkpoint.h"
static void search(Sol&s,mt19937_64&r,double end,int mode,int tid){
    if(mode==4){while(elapsed()<end)xn_packets(s,r,min(end,elapsed()+.04));}
    else if(mode==5){Engine E(s);E.rec=true;greedy_fill(s,E,end);s.recompute_psum();offer(*s.I,s);}
    else if(mode==6){Engine E(s);E.rec=true;try_open_office(s,E,end);s.recompute_psum();offer(*s.I,s);}
    else if(mode==7){Engine E(s);E.rec=true;Guide G(s,0);recreate(E,G,r,false,6,end);s.recompute_psum();offer(*s.I,s);}
    else if(mode==0){while(elapsed()<end){long n=boundary_stats.calls;boundary_move(s,r,min(end,elapsed()+.04),1,1,24);
        if(n==boundary_stats.calls)break;if(s.objective_fast()>g_best.load()+1e-9)offer(*s.I,s);}}
    else{while(elapsed()<end){XNStats st;xn_move(s,r,min(end,elapsed()+.04),mode,12,&st);if(!st.nodes)break;}}
}
int main(int argc,char**argv){return checkpoint_main(argc,argv,search);}
