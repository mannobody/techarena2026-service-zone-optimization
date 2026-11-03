// Safe enlarged envelopes + exact grouped selection/count/load/worker MILP.
// Only runs after native workers have joined. The best published solution survives failures.
static bool v5_offer(const Inst&I,const vector<int>&asg,const vector<char>&op,const vector<int>&wof){
 double score=0;if(!verify(I,asg,op,wof,&score))return false;
 lock_guard<mutex>lk(g_best_mx);if(score<=g_best.load()+1e-9)return false;
 g_best.store(score);g_best_asg=asg;g_best_open=op;g_best_staff=wof;publish(serialize(I,asg,op,wof));push_elite(score,asg,op);return true;
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
static void v5_finish(const Inst&I,double limit){
 if(!v5_api().ready||g_best.load()<=0)return;double end=limit-.35;if(elapsed()>=end-.05)return;
 vector<int>old,staff;vector<char>op;{lock_guard<mutex>lk(g_best_mx);old=g_best_asg;op=g_best_open;staff=g_best_staff;}Sol env;env.init(I);env.load_state(old,op);if(staff.size()!=(size_t)I.nw){g_wdfs_deadline=end;if(!env.greedy_workers(&staff))return;}
 int mode=getenv("MIP_MODE")?atoi(getenv("MIP_MODE")):2;
 // Mode 0: fixed territory; mode 1/2: safe expansion; mode 3: also new offices.
 if(mode>=3){vector<pair<double,int>>rank;for(int o=0;o<I.no;o++)if(!op[o]&&I.maxsize[o]>0&&!env.cov[I.ns+o]){vector<double>p;for(int s=0;s<I.ns;s++)if(I.servable[s]&&!env.cov[s]&&I.pr(o,s)>0)p.push_back(I.pr(o,s));sort(p.rbegin(),p.rend());double b=-I.cost[o];for(int j=0;j<min((int)p.size(),I.maxsize[o]);j++)b+=p[j];rank.push_back({b,o});}sort(rank.rbegin(),rank.rend());int count=0;for(auto e:rank)if(count<3&&e.first>0&&!env.cov[I.ns+e.second]){env.isopen[e.second]=1;env.set_hull(e.second,{I.P[I.ns+e.second]});count++;}}
 if(mode>=1&&elapsed()<end-.05){vector<tuple<double,int,int>>offers;for(int o=0;o<I.no;o++)if(env.isopen[o]){vector<pair<double,int>>v;for(int s=0;s<I.ns;s++)if(I.servable[s]&&!env.cov[s]&&I.pr(o,s)>0)v.push_back({I.pr(o,s),s});sort(v.rbegin(),v.rend());for(int j=0;j<min(64,(int)v.size());j++)offers.emplace_back(v[j].first,o,v[j].second);}sort(offers.rbegin(),offers.rend());int attempts=0,accepted=0;double growend=min(end-.05,elapsed()+.25);for(auto e:offers){if(attempts>=320||elapsed()>=growend)break;int o=get<1>(e),s=get<2>(e);if(env.cov[s])continue;attempts++;vector<Pt>h;if(env.geo_ok(s,o,h)){if(!h.empty())env.set_hull(o,h);accepted++;}}if(DBG)fprintf(stderr,"v5_envelope attempts=%d accepted=%d t=%.6f\n",attempts,accepted,elapsed());}
 bool joint=mode>=2;
 if(joint){double left=end-elapsed();if(left>.08)v5_select(I,env,old,op,staff,min(end,elapsed()+min(.45,left*.4)),false);
  {lock_guard<mutex>lk(g_best_mx);old=g_best_asg;op=g_best_open;}
  if(elapsed()<end-.04)v5_select(I,env,old,op,staff,end,true);
 }else v5_select(I,env,old,op,staff,end,false);
}
