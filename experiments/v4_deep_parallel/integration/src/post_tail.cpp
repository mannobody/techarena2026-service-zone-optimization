#define main original_main
#ifdef POST_HYBRID
#include "hybrid_frozen.cpp"
#else
#include "../../../v4_local_search/baseline/frozen_v4.cpp"
#endif
#undef main
int main(int argc,char**argv){
 if(argc!=6)return 2;Inst I=load_instance(argv[1]);g_geo_grid.init(I);Sol s;s.init(I);
 ifstream f(argv[2]);string text((istreambuf_iterator<char>(f)),{});JReader j(text.data(),text.data()+text.size());
 vector<int>asg(I.ns,-1);vector<char>op(I.no,0);j.need('[');
 if(!j.eat(']'))do{j.need('{');int o=-1;vector<int>ss;
 do{string k=j.str();j.need(':');if(k=="officeId")o=j.num();else if(k=="sites"){j.need('[');if(!j.eat(']')){do{ss.push_back(j.num());}while(j.eat(','));j.need(']');}}else j.skip();}while(j.eat(','));j.need('}');
 if(o<0||o>=I.no)return 3;op[o]=1;for(int x:ss){if(x<0||x>=I.ns)return 4;asg[x]=o;}
 }while(j.eat(','));
 s.load_state(asg,op);double initial=s.objective();g_wdfs_deadline=elapsed()+atof(argv[4]);
 offer(I,s);double start=elapsed();double limit=start+atof(argv[4])+.25;
 #ifdef POST_HYBRID
 if(atoi(argv[5])){geom_finish(I,limit);joint_territory_finish(I,limit);}
 #endif
 boundary_finish(I,limit);double finish=elapsed();
 int idx=g_idx.load();ofstream out(argv[3]);if(idx>=0)out<<g_buf[idx];else out<<"[]";
 fprintf(stderr,"tail_post before=%.12f after=%.12f mode=%d stage_seconds=%.6f wall=%.6f threads=%d\n",initial,g_best.load(),atoi(argv[5]),finish-start,elapsed(),detect_cpus());
}
