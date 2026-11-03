int main(int argc,char**argv){
    if(argc<7)return 2;
    Inst I=load_instance(argv[1]);
    // Research JSON assignments, one integer per site. Never part of runtime solver.
    ifstream f(argv[2]);vector<int>a(I.ns,-1);vector<char>open(I.no,0);
    for(int&v:a){f>>v;if(v>=0)open[v]=1;}if(!f)return 3;
    Sol s;s.init(I);s.load_state(a,open);double before=s.objective();
    int method=atoi(argv[4]),style=atoi(argv[5]);mt19937_64 rng(strtoull(argv[6],nullptr,10));
    double end=elapsed()+atof(argv[3]);g_wdfs_deadline=end;
    boundary_polish(s,rng,end,method,style);
    vector<int>w;double val=0;bool valid=s.greedy_workers(&w)&&verify(I,s.asg,s.isopen,w,&val);
    const auto&st=boundary_stats;
    fprintf(stderr,"{\"before\":%.12g,\"after\":%.12g,\"valid\":%s,\"time\":%.6f,\"calls\":%ld,\"nodes\":%ld,\"pruned\":%ld,\"geo\":%ld,\"leaves\":%ld,\"wfail\":%ld,\"complete\":%ld,\"wins\":%ld}\n",before,val,valid?"true":"false",elapsed(),st.calls,st.nodes,st.pruned,st.geo,st.leaves,st.wfail,st.complete,st.wins);
    if(!valid)return 4;
    printf("[");bool first=true;for(int o=0;o<I.no;o++)if(s.size_[o]){
        printf("%s{\"officeId\":%d,\"sites\":[",first?"":",",o);first=false;
        for(size_t k=0;k<s.members[o].size();k++)printf("%s%d",k?",":"",s.members[o][k]);
        printf("],\"workers\":[");bool fw=true;for(int j=0;j<I.nw;j++)if(w[j]==o){printf("%s%d",fw?"":",",j);fw=false;}printf("]}");}
    printf("]\n");return 0;
}
