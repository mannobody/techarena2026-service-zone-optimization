#define main frozen_candidate_main
#include "../artifacts/final/main.cpp"
#undef main
int main(int argc,char**argv){
    if(argc!=3)return 2;Inst I=load_instance(argv[1]);g_geo_grid.init(I);g_wdfs_deadline=10;
    Sol s;s.init(I);for(int o=0;o<I.no;o++){s.open_office(o);s.force_add(o,o);}
    vector<int>w;double start=elapsed();bool ok=s.greedy_workers(&w);double sec=elapsed()-start;
    vector<int>known(I.nw);for(int j=0;j<I.nw;j++)known[j]=j/3;
    double value=0;bool valid=verify(I,s.asg,s.isopen,ok?w:known,&value);
    ofstream f(argv[2]);f<<serialize(I,s.asg,s.isopen,ok?w:known);
    printf("{\"accepted\":%s,\"valid_certificate\":%s,\"objective\":%.6f,\"seconds\":%.9f,\"nodes\":%ld}\n",ok?"true":"false",valid?"true":"false",value,sec,g_wdfs_nodes.load());
    return valid?0:3;
}
