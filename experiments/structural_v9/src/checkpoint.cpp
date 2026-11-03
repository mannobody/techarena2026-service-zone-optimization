// Research-only harness. NOT linked or packaged into the contest executable.
// It reads a second file solely for fixed-checkpoint mechanism tests.
#define main contest_main_not_called
#include "../artifacts/final_research/main.cpp"
#undef main
int main(int argc,char**argv) {
    if(argc!=6)return 2;
    Inst I=load_instance(argv[1]);g_geo_grid.init(I);g_wdfs_deadline=1000;
    ifstream in(argv[2]);string text((istreambuf_iterator<char>(in)),{});
    JReader r(text.data(),text.data()+text.size());vector<int>a(I.ns,-1);vector<char>op(I.no,0);
    r.need('[');if(!r.eat(']'))while(true) {
        r.need('{');int o=-1;vector<int>sites;
        if(!r.eat('}'))while(true) {
            string key=r.str();r.need(':');
            if(key=="officeId")o=(int)llround(r.num());
            else if(key=="sites") {r.need('[');if(!r.eat(']'))while(true){sites.push_back((int)llround(r.num()));if(r.eat(','))continue;r.need(']');break;}}
            else r.skip();
            if(r.eat(','))continue;r.need('}');break;
        }
        if(o<0||o>=I.no)return 3;op[o]=1;for(int x:sites){if(x<0||x>=I.ns)return 3;a[x]=o;}
        if(r.eat(','))continue;r.need(']');break;
    }
    g_fd=open(argv[3],O_WRONLY|O_CREAT|O_TRUNC,0644);publish("[]\n");
    Sol s;s.init(I);s.load_state(a,op);if(!offer(I,s)&&s.objective()>0)return 4;
    double before=g_best.load();double end=elapsed()+atof(argv[4]);
    if(string(argv[5])=="signed")zm_signed_finish(I,end);
    else if(string(argv[5])=="master")zm::finish(I,end+.25);
    else if(string(argv[5])=="legacy_dp") {
        resize_dp(s,end);double afterdp=s.objective();repair_sizes(s);s.recompute_psum();
        vector<int>w;double actual=0;bool valid=s.greedy_workers(&w)&&verify(I,s.asg,s.isopen,w,&actual);
        if(valid){ofstream current(string(argv[3])+".current.json");current<<serialize(I,s.asg,s.isopen,w);offer(I,s);}
        fprintf(stderr,"LEGACY_DP after_dp=%.9f after_repair=%.9f valid=%d\n",afterdp,s.objective(),valid);
    }
    else if(string(argv[5])=="exact") {
        zm::Master m(I,end,true);m.enumerate();if(m.complete){m.prepare();m.search(0,0,INT_MAX,0,INT_MAX,0);}
        fprintf(stderr,"EXACT complete=%d nodes=%ld\n",m.complete,m.nodes);
    }
    else return 5;
    fprintf(stderr,"CHECKPOINT before=%.9f after=%.9f\n",before,g_best.load());
}
