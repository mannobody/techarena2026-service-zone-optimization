// Known-feasible staffing constructed first, then hidden from native worker DFS.
// Stop at first false rejection or a fixed ten-second audit budget.
#define main candidate_main
#include "../artifacts/candidate_v2/main.cpp"
#undef main
int main(int argc,char**argv){
    if(argc!=2)return 2;g_wdfs_deadline=12;mt19937_64 rng(20261020);int trials=0;
    while(elapsed()<10&&trials<30000){trials++;Inst I;I.no=5;I.ns=5;I.nw=15;I.nsk=10;I.A=0;I.alpha=0;
        I.maxsize.assign(I.no,1);I.cost.assign(I.no,1);I.reward.assign(I.ns,10);I.prof.assign(I.no*I.ns,10);I.D.assign(I.no*I.ns,0);
        I.P.resize(I.ns+I.no);I.skillset.resize(I.ns);I.ntask.resize(I.ns);I.wskills.resize(I.nw);I.wmask.assign(I.nw,vector<char>(I.nsk));I.Nk.assign(I.nsk,0);I.simple_workers=false;
        vector<vector<char>>known(I.no,vector<char>(I.nsk));vector<int>certificate(I.nw);
        for(int w=0;w<I.nw;w++){
            int o=w/3;certificate[w]=o;
            for(int k=0;k<I.nsk;k++)if(rng()%100<32){I.wskills[w].push_back(k);I.wmask[w][k]=1;I.Nk[k]++;known[o][k]=1;}
        }
        for(int o=0;o<I.no;o++){
            I.P[o]={(double)(o*10),1};I.P[I.ns+o]={(double)(o*10),0};
            for(int k=0;k<I.nsk;k++)if(known[o][k]&&rng()%100<62)I.skillset[o].push_back(k);
            I.ntask[o]=I.skillset[o].size();I.totalTasks+=I.ntask[o];
        }
        g_geo_grid.init(I);Sol s;s.init(I);for(int o=0;o<I.no;o++){s.open_office(o);s.force_add(o,o);}
        long before=g_wdfs_nodes.load();bool ok=s.greedy_workers(nullptr);long nodes=g_wdfs_nodes.load()-before;
        if(!ok&&elapsed()<10){double value; if(!verify(I,s.asg,s.isopen,certificate,&value))return 3;
            FILE*f=fopen(argv[1],"w");fprintf(f,"{\"sites\":[");
            for(int o=0;o<I.no;o++){if(o)fprintf(f,",");fprintf(f,"{\"x\":%d,\"y\":1,\"reward\":10,\"tasks\":[",o*10);
                for(size_t j=0;j<I.skillset[o].size();j++)fprintf(f,"%s%d",j?",":"",I.skillset[o][j]);fprintf(f,"]}");}
            fprintf(f,"],\"offices\":[");for(int o=0;o<I.no;o++)fprintf(f,"%s{\"x\":%d,\"y\":0,\"cost\":1,\"maxSize\":1}",o?",":"",o*10);
            fprintf(f,"],\"workers\":[");for(int w=0;w<I.nw;w++){fprintf(f,"%s[",w?",":"");for(size_t j=0;j<I.wskills[w].size();j++)fprintf(f,"%s%d",j?",":"",I.wskills[w][j]);fprintf(f,"]");}
            fprintf(f,"],\"distances\":[[0,0,0,0,0],[0,0,0,0,0],[0,0,0,0,0],[0,0,0,0,0],[0,0,0,0,0]],\"maxDifference\":0,\"balanceCoefficient\":0}");fclose(f);
            bool timeout=false;vector<int>exact;double t=elapsed();bool recovered=xn_workers(s,exact,12,timeout);
            fprintf(stdout,"{\"trials\":%d,\"native_rejected\":true,\"native_nodes\":%ld,\"known_certificate_value\":%.6f,\"exact_recovered\":%s,\"exact_seconds\":%.6f,\"timeout\":%s}\n",trials,nodes,value,recovered?"true":"false",elapsed()-t,timeout?"true":"false");return 0;
        }
    }
    printf("{\"trials\":%d,\"native_rejected\":false,\"seconds\":%.6f,\"note\":\"bounded audit found no default-budget counterexample\"}\n",trials,elapsed());
}
