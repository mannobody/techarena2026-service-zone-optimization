// Offline deterministic microbenchmark: no submission code path.
#define main service_zone_main
#include "lab.cpp"
#undef main
#include <cassert>
int main(int argc,char**argv){
 if(argc!=4)return 2;
 Inst I=load_instance(argv[1]);g_geo_grid.init(I);Sol s;s.init(I);
 ifstream f(argv[2]);string text((istreambuf_iterator<char>(f)),{});JReader j(text.data(),text.data()+text.size());
 vector<int> asg(I.ns,-1);vector<char> opened(I.no,0);j.need('[');
 if(!j.eat(']'))do{j.need('{');int o=-1;vector<int> sites;do{string k=j.str();j.need(':');if(k=="officeId")o=j.num();else if(k=="sites"){j.need('[');if(!j.eat(']')){do{sites.push_back(j.num());}while(j.eat(','));j.need(']');}}else j.skip();}while(j.eat(','));j.need('}');if(o<0||o>=I.no)return 3;opened[o]=1;for(int x:sites)asg[x]=o;}while(j.eat(','));
 s.load_state(asg,opened);vector<int> assigned;for(int x=0;x<I.ns;x++)if(asg[x]>=0)assigned.push_back(x);
 int loops=atoi(argv[3]);vector<vector<int>> work;mt19937_64 rng(91827);
 for(int i=0;i<loops;i++){shuffle(assigned.begin(),assigned.end(),rng);work.emplace_back(assigned.begin(),assigned.begin()+min(32,(int)assigned.size()));}
 for(int rep=0;rep<3;rep++)for(int batch=0;batch<=1;batch++) {
  setenv("LAB_BATCH",batch?"1":"0",1);s.load_state(asg,opened);Engine E(s);E.rec=true;double start=elapsed();
  for(auto&xs:work) {s.begin_defer();for(int x:xs)E.doRemove(x);s.end_defer();E.undo(0);}
  double sec=elapsed()-start;assert(s.asg==asg);Sol ref;ref.init(I);ref.load_state(asg,opened);assert(s.cov==ref.cov && s.incov==ref.incov && s.load==ref.load && s.need==ref.need);
  printf("{\"kind\":\"batch\",\"rep\":%d,\"on\":%d,\"loops\":%d,\"seconds\":%.9f}\n",rep,batch,loops,sec);
 }
 if(!I.simple_workers)for(int rep=0;rep<3;rep++)for(int memo=0;memo<=1;memo++) {
  setenv("LAB_MEMO",memo?"1":"0",1);double start=elapsed();int success=0;vector<int>w;
  for(int i=0;i<loops*10;i++) success+=s.greedy_workers(&w);
  printf("{\"kind\":\"memo\",\"rep\":%d,\"on\":%d,\"loops\":%d,\"success\":%d,\"seconds\":%.9f}\n",rep,memo,loops*10,success,elapsed()-start);
 }
}
