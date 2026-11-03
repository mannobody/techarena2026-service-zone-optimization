// Offline operator experiment only. This driver is NEVER packaged in a submission.
#define main service_zone_main
#include "../../../solver/solve.cpp"
#undef main
int main(int argc,char**argv){
    if(argc!=7)return 2;
    Inst I=load_instance(argv[1]);g_geo_grid.init(I);Sol s;s.init(I);
    ifstream f(argv[2]);string text((istreambuf_iterator<char>(f)),{});JReader j(text.data(),text.data()+text.size());
    vector<int> asg(I.ns,-1);vector<char> opened(I.no,0);j.need('[');
    if(!j.eat(']'))do{
        j.need('{');int o=-1;vector<int> sites;
        do{string k=j.str();j.need(':');if(k=="officeId")o=j.num();else if(k=="sites"){j.need('[');if(!j.eat(']')){do{sites.push_back(j.num());}while(j.eat(','));j.need(']');}}else j.skip();}while(j.eat(','));j.need('}');
        if(o<0 || o>=I.no)return 3;opened[o]=1;for(int x:sites){if(x<0 || x>=I.ns)return 4;asg[x]=o;}
    }while(j.eat(','));
    s.load_state(asg,opened);if(!search_valid(s))return 5;
    offer(I,s);
    double initial=s.objective(),seconds=atof(argv[4]);int mode=atoi(argv[5]);mt19937_64 rng(strtoull(argv[6],nullptr,10));
    g_wdfs_deadline=elapsed()+seconds;double end=elapsed()+seconds;setenv("SEARCH_TRACE","1",1);
    if(mode==8)boundary_finish(I,end+0.25);
    else if(mode==9){setenv("FINAL_EXCHANGE","2",1);setenv("BALANCED_CYCLE","1",1);exchange_finish(I,end+0.25);boundary_finish(I,end+0.25);}
    else if(mode==0)polish(s,rng,end,end,false);
    else if(mode<=2)exchange_descent(s,rng,end,mode);
    else if(mode==7)balanced_cycle_descent(s,rng,end);
    else research_search(s,rng,end,mode-2);
    offer(I,s);
    // Keep the already verified worker certificate, just like the submission.
    // Re-solving worker DFS after its deadline can reject a valid stored state.
    int idx=g_idx.load();if(idx<0)return 6;double objective=g_best.load();
    ofstream out(argv[3]);out<<g_buf[idx];
    fprintf(stderr,"post initial=%.12f final=%.12f gain=%.12f wall=%.6f\n",initial,objective,objective-initial,elapsed());
}
