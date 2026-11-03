// Optional HiGHS C API, compatible with the documented 32-bit HighsInt ABI.
// Library absence or ABI mismatch disables only the MIP tail.
#include <dlfcn.h>
struct V5Highs {
 void* lib=nullptr;bool ready=false;
 void*(*create)()=nullptr;void(*destroy)(void*)=nullptr;
 int(*intsize)(const void*)=nullptr;
 int(*setbool)(void*,const char*,int)=nullptr;
 int(*setint)(void*,const char*,int)=nullptr;
 int(*setdouble)(void*,const char*,double)=nullptr;
 int(*pass)(void*,int,int,int,int,int,double,const double*,const double*,const double*,const double*,const double*,const int*,const int*,const double*,const int*)=nullptr;
 int(*setsol)(void*,const double*,const double*,const double*,const double*)=nullptr;
 int(*getsol)(const void*,double*,double*,double*,double*)=nullptr;
 int(*getint)(const void*,const char*,int*)=nullptr;
 int(*run)(void*)=nullptr;int(*status)(const void*)=nullptr;
 template<class T>bool bind(T&f,const char*n){f=reinterpret_cast<T>(dlsym(lib,n));return f!=nullptr;}
 V5Highs(){
  lib=dlopen("libhighs.so",RTLD_NOW|RTLD_LOCAL);if(!lib)lib=dlopen("libhighs.so.1",RTLD_NOW|RTLD_LOCAL);if(!lib)return;
  ready=bind(create,"Highs_create")&&bind(destroy,"Highs_destroy")&&bind(intsize,"Highs_getSizeofHighsInt")&&bind(setbool,"Highs_setBoolOptionValue")&&bind(setint,"Highs_setIntOptionValue")&&bind(setdouble,"Highs_setDoubleOptionValue")&&bind(pass,"Highs_passMip")&&bind(setsol,"Highs_setSolution")&&bind(getsol,"Highs_getSolution")&&bind(getint,"Highs_getIntInfoValue")&&bind(run,"Highs_run")&&bind(status,"Highs_getModelStatus");
  if(ready){void*h=create();ready=h&&intsize(h)==sizeof(int);if(h)destroy(h);}
 }
};
static V5Highs&v5_api(){static V5Highs a;return a;}
struct V5Model {
 vector<double>cost,lb,ub,rl,ru,av,warm;vector<int>integer,rs{0},ai;
 int var(double c,double low,double high,int integral,double w=0){int j=cost.size();cost.push_back(c);lb.push_back(low);ub.push_back(high);integer.push_back(integral);warm.push_back(w);return j;}
 void row(vector<pair<int,double>> r,double low,double high){sort(r.begin(),r.end());for(size_t i=0;i<r.size();){size_t j=i+1;double v=r[i].second;while(j<r.size()&&r[j].first==r[i].first)v+=r[j++].second;if(v){ai.push_back(r[i].first);av.push_back(v);}i=j;}rs.push_back(ai.size());rl.push_back(low);ru.push_back(high);}
};

// Safe enlarged envelopes + exact grouped selection/count/load/worker MILP.
// Only runs after native workers have joined. The best published solution survives failures.
static bool v5_offer(const Inst&I,const vector<int>&asg,const vector<char>&op,const vector<int>&wof){
 double score=0;if(!verify(I,asg,op,wof,&score))return false;
 lock_guard<mutex>lk(g_best_mx);if(score<=g_best.load()+1e-9)return false;
 g_best.store(score);g_best_asg=asg;g_best_open=op;publish(serialize(I,asg,op,wof));push_elite(score,asg,op);return true;
}
struct V5Group{int o,w;vector<int>skills,sites,x;int q=-1;};
static bool v5_select(const Inst&I,Sol&env,const vector<int>&old,const vector<char>&oldop,const vector<int>&staff,double deadline,bool joint){
 auto&A=v5_api();if(!A.ready||elapsed()>=deadline-.02)return false;
 double begin=elapsed(),before=g_best.load();const double inf=1e30;
 vector<vector<char>>have(I.no,vector<char>(I.nsk));for(int w=0;w<I.nw;w++)if(staff[w]>=0)for(int k=0;k<I.nsk;k++)have[staff[w]][k]|=I.wmask[w][k];
 map<vector<int>,int>lookup;vector<V5Group>groups;vector<int>ops;vector<int>poolsize(I.no);vector<long long>maxload(I.no);
 for(int o=0;o<I.no;o++)if(env.isopen[o]){
  for(int s:env.covlist[o])if(s<I.ns&&I.servable[s]){
   bool ok=true;if(!joint)for(int k:I.skillset[s])if(!have[o][k]){ok=false;break;}if(!ok)continue;
   vector<int>key{o,I.ntask[s]};if(joint)key.insert(key.end(),I.skillset[s].begin(),I.skillset[s].end());
   auto it=lookup.find(key);int g;if(it==lookup.end()){g=groups.size();lookup[key]=g;groups.push_back({o,I.ntask[s],joint?I.skillset[s]:vector<int>{},{},{},-1});}else g=it->second;
   groups[g].sites.push_back(s);poolsize[o]++;maxload[o]+=I.ntask[s];
  }
  if(poolsize[o]&&I.maxsize[o]>0)ops.push_back(o);
 }
 if(ops.empty()||elapsed()>=deadline-.02)return false;
 V5Model M;vector<vector<int>>og(I.no);vector<int>y(I.no,-1);long long T=1;
 for(auto&g:groups){sort(g.sites.begin(),g.sites.end(),[&](int a,int b){double pa=I.pr(g.o,a),pb=I.pr(g.o,b);return pa!=pb?pa>pb:a<b;});int n=0;for(int s:g.sites)n+=old[s]==g.o;g.q=M.var(0,0,g.sites.size(),1,n);og[g.o].push_back(&g-&groups[0]);}
 for(int o:ops){y[o]=M.var(I.cost[o],oldop[o]?1:0,1,1,oldop[o]);T=max(T,maxload[o]);}
 long long oldmin=LLONG_MAX,oldmax=0;for(int o:ops)if(oldop[o]){long long w=0;for(int s=0;s<I.ns;s++)if(old[s]==o)w+=I.ntask[s];oldmin=min(oldmin,w);oldmax=max(oldmax,w);}
 int hi=M.var(I.alpha,0,T,0,oldmax),lo=M.var(-I.alpha,0,T,0,oldmin==LLONG_MAX?0:oldmin);
 map<vector<int>,vector<int>>profiles;for(int w=0;w<I.nw;w++){vector<int>p;for(int k=0;k<I.nsk;k++)if(I.wmask[w][k])p.push_back(k);if(!p.empty())profiles[p].push_back(w);}
 vector<vector<int>>pk,pw;for(auto&e:profiles){pk.push_back(e.first);pw.push_back(e.second);}int P=pk.size();vector<vector<int>>u(I.no,vector<int>(P,-1));
 if(joint)for(int o:ops)for(int p=0;p<P;p++){bool used=false;for(int w:pw[p])used|=staff[w]==o;u[o][p]=M.var(0,0,1,1,used);M.row({{u[o][p],1},{y[o],-1}},-inf,0);}
 if(joint)for(int p=0;p<P;p++){vector<pair<int,double>>r;for(int o:ops)r.push_back({u[o][p],1});M.row(r,-inf,pw[p].size());}
 for(auto&g:groups){vector<pair<int,double>>r{{g.q,-1}};int warmn=lround(M.warm[g.q]);for(int j=0;j<(int)g.sites.size();j++){int x=M.var(-I.pr(g.o,g.sites[j]),0,1,0,j<warmn);g.x.push_back(x);r.push_back({x,1});}M.row(r,0,0);
  if(joint)for(int k:g.skills){vector<pair<int,double>>c{{g.q,1}};for(int p=0;p<P;p++)if(binary_search(pk[p].begin(),pk[p].end(),k))c.push_back({u[g.o][p],-(double)g.sites.size()});M.row(c,-inf,0);}
 }
 for(int o:ops){vector<pair<int,double>>cnt,load;for(int g:og[o]){cnt.push_back({groups[g].q,1});load.push_back({groups[g].q,(double)groups[g].w});}
  auto r=cnt;r.push_back({y[o],-(double)I.maxsize[o]});M.row(r,-inf,0);r=cnt;r.push_back({y[o],-1});M.row(r,0,inf);
  for(int p:ops)if(p!=o){r=cnt;for(int g:og[p])r.push_back({groups[g].q,-1});r.push_back({y[o],(double)I.maxsize[o]});r.push_back({y[p],(double)I.maxsize[o]});M.row(r,-inf,I.A+2.*I.maxsize[o]);}
  r=load;r.push_back({hi,-1});M.row(r,-inf,0);r.clear();for(auto e:load)r.push_back({e.first,-e.second});r.push_back({lo,1});r.push_back({y[o],(double)T});M.row(r,-inf,T);
 }
 M.row({{lo,1},{hi,-1}},-inf,0);if(elapsed()>=deadline-.02)return false;
 void*h=A.create();if(!h)return false;A.setbool(h,"output_flag",0);A.setint(h,"threads",1);A.setint(h,"random_seed",1);A.setdouble(h,"mip_rel_gap",1e-8);
 int rc=A.pass(h,M.cost.size(),M.rl.size(),M.ai.size(),2,1,0,M.cost.data(),M.lb.data(),M.ub.data(),M.rl.data(),M.ru.data(),M.rs.data(),M.ai.data(),M.av.data(),M.integer.data());
 if(rc<0){A.destroy(h);return false;}
 A.setsol(h,M.warm.data(),nullptr,nullptr,nullptr);double prep=elapsed()-begin;A.setdouble(h,"time_limit",max(.001,deadline-elapsed()-.03));A.run(h);
 vector<double>v(M.cost.size());int feasible=0;A.getint(h,"primal_solution_status",&feasible);int status=A.status(h);bool improved=false;
 if(feasible==2&&A.getsol(h,v.data(),nullptr,nullptr,nullptr)>=0){vector<int>asg(I.ns,-1),wof(I.nw,-1);vector<char>open(I.no,0);bool good=true;
  for(auto&g:groups){double z=v[g.q];int n=lround(z);if(!isfinite(z)||fabs(z-n)>1e-4||n<0||n>(int)g.sites.size()){good=false;break;}if(n)open[g.o]=1;for(int j=0;j<n;j++)asg[g.sites[j]]=g.o;}
  if(joint){for(int p=0;p<P;p++){int w=0;for(int o:ops)if(v[u[o][p]]>.5&&open[o]){if(w>=(int)pw[p].size()){good=false;break;}wof[pw[p][w++]]=o;}}}else for(int w=0;w<I.nw;w++)if(staff[w]>=0&&open[staff[w]])wof[w]=staff[w];
  if(good)improved=v5_offer(I,asg,open,wof);
 }
 A.destroy(h);if(DBG)fprintf(stderr,"v5_mip joint=%d groups=%zu vars=%zu rows=%zu status=%d prep=%.6f seconds=%.6f before=%.12f after=%.12f\n",joint,groups.size(),M.cost.size(),M.rl.size(),status,prep,elapsed()-begin,before,g_best.load());return improved;
}
// Read the already published worker certificate from memory, after all workers joined.
static bool v5_saved_staff(const Inst&I,vector<int>&staff){
 staff.assign(I.nw,-1);int ix=g_idx.load(memory_order_acquire);if(ix<0)return false;
 const string&text=g_buf[ix];JReader r(text.data(),text.data()+text.size());
 try{r.need('[');if(r.eat(']'))return true;
  while(true){r.need('{');int o=-1;vector<int>ws;
   while(true){string key=r.str();r.need(':');if(key=="officeId")o=(int)r.num();else if(key=="workers"){r.need('[');if(!r.eat(']')){while(true){ws.push_back((int)r.num());if(r.eat(']'))break;r.need(',');}}}else r.skip();if(r.eat('}'))break;r.need(',');}
   if(o<0||o>=I.no)return false;for(int w:ws){if(w<0||w>=I.nw||staff[w]>=0)return false;staff[w]=o;}
   if(r.eat(']'))break;r.need(',');
  }
 }catch(...){return false;}return true;
}
static void v5_finish(const Inst&I,double limit){
 double end=limit-.15;if(elapsed()>=end-.05||g_best.load()<=0)return;if(!v5_api().ready)return;
 vector<int>old,staff;vector<char>op;{lock_guard<mutex>lk(g_best_mx);old=g_best_asg;op=g_best_open;}Sol env;env.init(I);env.load_state(old,op);if(!v5_saved_staff(I,staff))return;
 int mode=getenv("MIP_MODE")?atoi(getenv("MIP_MODE")):2;
 // Mode 0: fixed territory; mode 1/2: safe expansion; mode 3: also new offices.
 if(mode>=3){vector<pair<double,int>>rank;for(int o=0;o<I.no;o++)if(!op[o]&&I.maxsize[o]>0&&!env.cov[I.ns+o]){vector<double>p;for(int s=0;s<I.ns;s++)if(I.servable[s]&&!env.cov[s]&&I.pr(o,s)>0)p.push_back(I.pr(o,s));sort(p.rbegin(),p.rend());double b=-I.cost[o];for(int j=0;j<min((int)p.size(),I.maxsize[o]);j++)b+=p[j];rank.push_back({b,o});}sort(rank.rbegin(),rank.rend());int count=0;for(auto e:rank)if(count<3&&e.first>0&&!env.cov[I.ns+e.second]){env.isopen[e.second]=1;env.set_hull(e.second,{I.P[I.ns+e.second]});count++;}}
 if(mode>=1&&elapsed()<end-.05){vector<tuple<double,int,int>>offers;for(int o=0;o<I.no;o++)if(env.isopen[o]){vector<pair<double,int>>v;for(int s=0;s<I.ns;s++)if(I.servable[s]&&!env.cov[s]&&I.pr(o,s)>0)v.push_back({I.pr(o,s),s});sort(v.rbegin(),v.rend());for(int j=0;j<min(64,(int)v.size());j++)offers.emplace_back(v[j].first,o,v[j].second);}sort(offers.rbegin(),offers.rend());int attempts=0,accepted=0;double growend=min(end-.05,elapsed()+.25);for(auto e:offers){if(attempts>=320||elapsed()>=growend)break;int o=get<1>(e),s=get<2>(e);if(env.cov[s])continue;attempts++;vector<Pt>h;if(env.geo_ok(s,o,h)){if(!h.empty())env.set_hull(o,h);accepted++;}}if(DBG)fprintf(stderr,"v5_envelope attempts=%d accepted=%d t=%.6f\n",attempts,accepted,elapsed());}
 bool joint=mode>=2;
 if(joint && end-elapsed()>.65){double left=end-elapsed();if(left>.08)v5_select(I,env,old,op,staff,min(end,elapsed()+min(.45,left*.4)),false);
  {lock_guard<mutex>lk(g_best_mx);old=g_best_asg;op=g_best_open;}
  if(elapsed()<end-.04)v5_select(I,env,old,op,staff,end,true);
 }else v5_select(I,env,old,op,staff,end,false);
}

// v5.2 research: select convex envelopes with exact finite input-point packing.
static double v52_publish(const Inst&I,const vector<int>&asg,const vector<char>&op,const vector<int>&staff){
 double value=0;if(!verify(I,asg,op,staff,&value))return 0;lock_guard<mutex>lk(g_best_mx);double before=g_best.load();if(value<=before+1e-9)return 0;
 g_best.store(value);g_best_asg=asg;g_best_open=op;publish(serialize(I,asg,op,staff));push_elite(value,asg,op);return value-before;
}
struct V52Region {int o;vector<int> sites,foot;int tag;};
static vector<V52Region> v52_regions(const Inst&I,const vector<int>&old,const vector<char>&op,vector<int>&base,double end,int mode){
 vector<char>active(I.no,0);for(int o:old)if(o>=0&&o<I.no)active[o]=1;
 vector<V52Region>regions;set<pair<int,vector<int>>>seen;Sol E,tmp;E.init(I);E.load_state(old,active);tmp.init(I);base.assign(I.no,-1);vector<int>ops;
 auto add=[&](int o,const vector<int>&ss,int tag,const vector<char>*blocked)->int{
  vector<Pt>h;h.reserve(ss.size()+1);for(int s:ss)h.push_back(I.P[s]);h.push_back(I.P[I.ns+o]);hull_of(h);tmp.set_hull(o,h);auto foot=tmp.covlist[o];tmp.clear_cov(o);sort(foot.begin(),foot.end());
  if(blocked)for(int p:foot)if((*blocked)[p])return -1;
  if(!seen.insert({o,foot}).second)return -1;vector<int>pool;for(int p:foot)if(p<I.ns&&I.servable[p])pool.push_back(p);if(pool.empty()||I.maxsize[o]<=0)return -1;
  int e=regions.size();regions.push_back({o,move(pool),move(foot),tag});return e;
 };
 for(int o=0;o<I.no;o++)if(active[o]){int e=add(o,E.members[o],0,nullptr);if(e>=0){ops.push_back(o);base[o]=e;}}
 if(ops.empty())return regions;
 vector<tuple<double,int,int>>pairs;
 for(int j=0;j<(int)ops.size();j++)for(int k=j+1;k<(int)ops.size();k++){
  int o=ops[j],p=ops[k];double gain=0;for(int s:regions[base[o]].sites)gain+=max(0.,I.pr(p,s)-I.pr(o,s));for(int s:regions[base[p]].sites)gain+=max(0.,I.pr(o,s)-I.pr(p,s));Pt a=I.P[I.ns+o],b=I.P[I.ns+p];pairs.emplace_back(gain/(1+hypot(a.x-b.x,a.y-b.y)),o,p);
 }
 sort(pairs.rbegin(),pairs.rend());
 if(mode!=2)for(int pi=0;pi<min(3,(int)pairs.size())&&elapsed()<end;pi++){
  int o=get<1>(pairs[pi]),p=get<2>(pairs[pi]);vector<char>blocked(I.ns+I.no);for(int s=0;s<I.ns+I.no;s++)blocked[s]=E.cov[s]-E.incov[(size_t)o*E.np+s]-E.incov[(size_t)p*E.np+s]>0;
  vector<int>pool=regions[base[o]].sites;pool.insert(pool.end(),regions[base[p]].sites.begin(),regions[base[p]].sites.end());vector<pair<double,int>>free;
  for(int s=0;s<I.ns;s++)if(I.servable[s]&&!E.cov[s])free.push_back({max(I.pr(o,s),I.pr(p,s)),s});sort(free.rbegin(),free.rend());for(int j=0;j<min(256,(int)free.size());j++)pool.push_back(free[j].second);sort(pool.begin(),pool.end());pool.erase(unique(pool.begin(),pool.end()),pool.end());
  Pt a=I.P[I.ns+o],b=I.P[I.ns+p];double dx=b.x-a.x,dy=b.y-a.y;if(dx==0&&dy==0)continue;
  for(auto rt:vector<pair<double,double>>{{0,.25},{0,.5},{0,.75},{.5,.5},{-.5,.5}}){if(elapsed()>=end)break;double nx=dx-rt.first*dy,ny=dy+rt.first*dx,cut=(1-rt.second)*(a.x*nx+a.y*ny)+rt.second*(b.x*nx+b.y*ny);
   for(int side=0;side<2;side++){int office=side?p:o;vector<int>ss;for(int s:pool){double v=I.P[s].x*nx+I.P[s].y*ny;if(side?v>cut:v<cut)ss.push_back(s);}
    if(add(office,ss,1,&blocked)<0){sort(ss.begin(),ss.end(),[&](int x,int y){double px=I.pr(office,x),py=I.pr(office,y);return px!=py?px>py:x<y;});vector<int>cur;int attempts=0;
     for(int s:ss){if(elapsed()>=end||attempts++>=256)break;vector<Pt>h;for(int t:cur)h.push_back(I.P[t]);h.push_back(I.P[s]);h.push_back(I.P[I.ns+office]);hull_of(h);tmp.set_hull(office,h);bool ok=true;for(int t:tmp.covlist[office])if(blocked[t]){ok=false;break;}tmp.clear_cov(office);if(ok)cur.push_back(s);}
     add(office,cur,2,&blocked);
    }
   }
  }
 }
 if(mode!=1&&elapsed()<end){vector<pair<double,int>>rank;for(int o=0;o<I.no;o++)if(!active[o]&&I.maxsize[o]>0){vector<double>pp;for(int s=0;s<I.ns;s++)if(I.servable[s])pp.push_back(I.pr(o,s));sort(pp.rbegin(),pp.rend());double v=-I.cost[o];for(int j=0;j<min(I.maxsize[o],(int)pp.size());j++)v+=max(0.,pp[j]);rank.push_back({v,o});}sort(rank.rbegin(),rank.rend());
  for(int nr=0;nr<(rank.empty()?1:2)&&elapsed()<end;nr++){int neo=nr?rank[0].second:-1;vector<int>oo=ops;if(neo>=0)oo.push_back(neo);double scale=1e300;if(neo>=0)for(int o:ops){Pt a=I.P[I.ns+neo],b=I.P[I.ns+o];scale=min(scale,(a.x-b.x)*(a.x-b.x)+(a.y-b.y)*(a.y-b.y));}
   for(double bias:(neo<0?vector<double>{0}:vector<double>{-.45,0,.45})){if(elapsed()>=end)break;vector<vector<int>>ss(I.no);vector<int>owner(I.no,-1);
    for(int s=0;s<I.ns+I.no;s++){double best=1e300,second=1e300;int who=-1;for(int o:oo){Pt a=I.P[s],b=I.P[I.ns+o];double d=(a.x-b.x)*(a.x-b.x)+(a.y-b.y)*(a.y-b.y)+(o==neo?bias*scale:0);if(d<best){second=best;best=d;who=o;}else second=min(second,d);}if(s<I.ns){if(I.servable[s]&&best<second)ss[who].push_back(s);}else owner[s-I.ns]=who;}
    for(int o:oo)if(owner[o]==o)add(o,ss[o],neo<0?3:4,nullptr);
   }
  }
 }
 return regions;
}
struct V52Group {int e,o,w,q,v;vector<int>skills,sites;};
static bool v52_select(const Inst&I,const vector<V52Region>&R,const vector<int>&base,const vector<int>&old,const vector<char>&op,const vector<int>&staff,double end,bool joint){
 auto&A=v5_api();if(!A.ready||elapsed()>=end-.03||R.empty())return false;double start=elapsed(),before=g_best.load(),inf=1e30;V5Model M;vector<int>ops,y(I.no,-1),z;vector<vector<int>>oe(I.no),og(I.no);vector<vector<char>>have(I.no,vector<char>(I.nsk));
 for(int w=0;w<I.nw;w++)if(staff[w]>=0)for(int k=0;k<I.nsk;k++)have[staff[w]][k]|=I.wmask[w][k];
 for(int e=0;e<(int)R.size();e++){int o=R[e].o;oe[o].push_back(e);z.push_back(M.var(0,0,1,1,base[o]==e));}
 for(int o=0;o<I.no;o++)if(!oe[o].empty()){ops.push_back(o);y[o]=M.var(I.cost[o],0,1,1,op[o]);}
 vector<V52Group>G;map<vector<int>,int>lookup;long long T=1;int C=1;
 for(int e=0;e<(int)R.size();e++){int o=R[e].o;vector<int>weights;C=max(C,I.maxsize[o]);for(int s:R[e].sites){bool ok=true;if(!joint)for(int k:I.skillset[s])if(!have[o][k]){ok=false;break;}if(!ok)continue;
   vector<int>key{e,I.ntask[s]};if(joint)key.insert(key.end(),I.skillset[s].begin(),I.skillset[s].end());auto it=lookup.find(key);int g;if(it==lookup.end()){g=G.size();lookup[key]=g;og[o].push_back(g);G.push_back({e,o,I.ntask[s],-1,-1,joint?I.skillset[s]:vector<int>{},{}});}else g=it->second;G[g].sites.push_back(s);weights.push_back(I.ntask[s]);}
  sort(weights.rbegin(),weights.rend());long long load=0;for(int j=0;j<min(I.maxsize[o],(int)weights.size());j++)load+=weights[j];T=max(T,load);
 }
 for(auto&g:G){sort(g.sites.begin(),g.sites.end(),[&](int a,int b){double pa=I.pr(g.o,a),pb=I.pr(g.o,b);return pa!=pb?pa>pb:a<b;});int n=0;for(int s:g.sites)n+=base[g.o]==g.e&&old[s]==g.o;int cap=min(I.maxsize[g.o],(int)g.sites.size());g.q=M.var(0,0,cap,1,n);double warm=0;for(int j=0;j<n;j++)warm+=I.pr(g.o,g.sites[j]);g.v=M.var(-1,-inf,inf,0,warm);M.row({{g.q,1},{z[g.e],-(double)cap}},-inf,0);
  double prefix=0,last=0;for(int j=0;j<(int)g.sites.size();j++){double p=I.pr(g.o,g.sites[j]);if(!j||p!=last)M.row({{g.v,1},{g.q,-p},{z[g.e],-(prefix-j*p)}},-inf,0);prefix+=p;last=p;}
 }
 map<vector<int>,vector<int>>profiles;for(int w=0;w<I.nw;w++){vector<int>ks;for(int k=0;k<I.nsk;k++)if(I.wmask[w][k])ks.push_back(k);if(!ks.empty())profiles[ks].push_back(w);}vector<vector<int>>pk,pw;for(auto&a:profiles){pk.push_back(a.first);pw.push_back(a.second);}int P=pk.size();vector<vector<int>>u(I.no,vector<int>(P,-1));
 if(joint){for(int o:ops)for(int p=0;p<P;p++){bool warm=false;for(int w:pw[p])warm|=staff[w]==o;u[o][p]=M.var(0,0,1,1,warm);M.row({{u[o][p],1},{y[o],-1}},-inf,0);}for(int p=0;p<P;p++){vector<pair<int,double>>row;for(int o:ops)row.push_back({u[o][p],1});M.row(row,-inf,pw[p].size());}for(auto&g:G)for(int k:g.skills){vector<pair<int,double>>row{{g.q,1}};for(int p=0;p<P;p++)if(binary_search(pk[p].begin(),pk[p].end(),k))row.push_back({u[g.o][p],-(double)min(I.maxsize[g.o],(int)g.sites.size())});M.row(row,-inf,0);}}
 long long minload=T,maxload=0;int mincount=C,maxcount=0;for(int o:ops)if(op[o]){long long load=0;int n=0;for(int s=0;s<I.ns;s++)if(old[s]==o){n++;load+=I.ntask[s];}minload=min(minload,load);maxload=max(maxload,load);mincount=min(mincount,n);maxcount=max(maxcount,n);}
 if(!maxcount){mincount=0;minload=0;}
 int hi=M.var(I.alpha,0,T,0,maxload),lo=M.var(-I.alpha,0,T,0,minload),ch=M.var(0,0,C,0,maxcount),cl=M.var(0,0,C,0,mincount);
 for(int o:ops){vector<pair<int,double>>row{{y[o],-1}},cnt,load;for(int e:oe[o])row.push_back({z[e],1});M.row(row,0,0);for(int g:og[o]){cnt.push_back({G[g].q,1});load.push_back({G[g].q,(double)G[g].w});}
  row=cnt;row.push_back({y[o],-(double)I.maxsize[o]});M.row(row,-inf,0);row=cnt;row.push_back({y[o],-1});M.row(row,0,inf);row=cnt;row.push_back({ch,-1});M.row(row,-inf,0);row.clear();for(auto a:cnt)row.push_back({a.first,-a.second});row.push_back({cl,1});row.push_back({y[o],(double)C});M.row(row,-inf,C);
  row=load;row.push_back({hi,-1});M.row(row,-inf,0);row.clear();for(auto a:load)row.push_back({a.first,-a.second});row.push_back({lo,1});row.push_back({y[o],(double)T});M.row(row,-inf,T);
 }
 M.row({{lo,1},{hi,-1}},-inf,0);M.row({{cl,1},{ch,-1}},-inf,0);M.row({{ch,1},{cl,-1}},-inf,I.A);
 vector<vector<int>>covers(I.ns+I.no);for(int e=0;e<(int)R.size();e++)for(int p:R[e].foot)covers[p].push_back(e);set<vector<int>>conflicts;for(auto&es:covers)if(es.size()>1){bool mixed=false;for(int e:es)mixed|=R[e].o!=R[es[0]].o;if(mixed)conflicts.insert(es);}for(auto&es:conflicts){vector<pair<int,double>>row;for(int e:es)row.push_back({z[e],1});M.row(row,-inf,1);}
 if(elapsed()>=end-.03)return false;void*h=A.create();if(!h)return false;A.setbool(h,"output_flag",0);A.setint(h,"threads",1);A.setint(h,"random_seed",1);A.setdouble(h,"mip_rel_gap",1e-8);int rc=A.pass(h,M.cost.size(),M.rl.size(),M.ai.size(),2,1,0,M.cost.data(),M.lb.data(),M.ub.data(),M.rl.data(),M.ru.data(),M.rs.data(),M.ai.data(),M.av.data(),M.integer.data());if(rc<0){A.destroy(h);return false;}
 A.setsol(h,M.warm.data(),nullptr,nullptr,nullptr);double prep=elapsed()-start;A.setdouble(h,"time_limit",max(.001,end-elapsed()-.04));A.run(h);int feasible=0,status=A.status(h);A.getint(h,"primal_solution_status",&feasible);bool improved=false;double own_gain=0;
 if(feasible==2){vector<double>v(M.cost.size());if(A.getsol(h,v.data(),nullptr,nullptr,nullptr)>=0){vector<int>asg(I.ns,-1),wof(I.nw,-1);vector<char>open(I.no,0);bool good=true;
  for(auto&g:G){double val=v[g.q];if(!isfinite(val)){good=false;break;}int n=lround(val);if(fabs(val-n)>1e-4||n<0||n>(int)g.sites.size()){good=false;break;}for(int j=0;j<n;j++){int s=g.sites[j];if(asg[s]>=0){good=false;break;}asg[s]=g.o;open[g.o]=1;}}
  if(joint){for(int p=0;p<P;p++){int w=0;for(int o:ops)if(open[o]&&v[u[o][p]]>.5){if(w>=(int)pw[p].size()){good=false;break;}wof[pw[p][w++]]=o;}}}else for(int w=0;w<I.nw;w++)if(staff[w]>=0&&open[staff[w]])wof[w]=staff[w];
  if(good){own_gain=v52_publish(I,asg,open,wof);improved=own_gain>0;}
 }}
 A.destroy(h);if(DBG)fprintf(stderr,"v52_mip joint=%d regions=%zu groups=%zu vars=%zu rows=%zu status=%d prep=%.6f seconds=%.6f before=%.12f after=%.12f own_gain=%.12f\n",joint,R.size(),G.size(),M.cost.size(),M.rl.size(),status,prep,elapsed()-start,before,g_best.load(),own_gain);return improved;
}
static void v52_finish(const Inst&I,double end){
 if(elapsed()>=end-.1||g_best.load()<=0)return;if(!v5_api().ready)return;vector<int>old,staff,base;vector<char>op;{lock_guard<mutex>lk(g_best_mx);old=g_best_asg;op=g_best_open;if(!v5_saved_staff(I,staff))return;}
 fill(op.begin(),op.end(),0);for(int o:old)if(o>=0&&o<I.no)op[o]=1;
 int mode=getenv("REGION_MODE")?atoi(getenv("REGION_MODE")):0;bool joint=getenv("REGION_JOINT")&&atoi(getenv("REGION_JOINT"));double start=elapsed();auto regions=v52_regions(I,old,op,base,min(end-.06,elapsed()+min(.5,(end-elapsed())*.2)),mode);if(DBG)fprintf(stderr,"v52_regions n=%zu seconds=%.6f\n",regions.size(),elapsed()-start);v52_select(I,regions,base,old,op,staff,end,joint);
}

