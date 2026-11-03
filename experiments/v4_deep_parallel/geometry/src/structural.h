// Offline structural operators. Every accepted state uses the exact Engine and full offer verifier.
static bool geom_feasible(Sol&s){Engine E(s);return E.size_viol(-1,-1)==0&&(s.I->simple_workers||s.greedy_workers(nullptr));}
static vector<int> geom_neighbors(Sol&s,mt19937_64&rng,int k){
 const Inst&I=*s.I;vector<int>op;for(int o=0;o<I.no;o++)if(s.isopen[o]&&s.size_[o])op.push_back(o);
 if(op.empty())return{};int a=op[rng()%op.size()];
 auto dist=[&](int b){double d=1e300;for(Pt p:s.hull[a])for(Pt q:s.hull[b])d=min(d,(p.x-q.x)*(p.x-q.x)+(p.y-q.y)*(p.y-q.y));return d;};
 stable_sort(op.begin(),op.end(),[&](int b,int c){return (b==a?-1.:dist(b))<(c==a?-1.:dist(c));});
 if((int)op.size()>k)op.resize(k);return op;
}
static bool geom_ruin(Engine&E,mt19937_64&rng,int mode,double end){
 Sol&s=E.s;const Inst&I=E.I;auto op=geom_neighbors(s,rng,2+(rng()%2));if(op.size()<2)return false;
 vector<int>rem;int layers=1+rng()%2;
 for(int o:op){auto m=s.members[o];for(int l=0;l<layers&&!m.empty();l++){
  vector<Pt>h;h.push_back(I.P[I.ns+o]);for(int x:m)h.push_back(I.P[x]);hull_of(h);
  vector<int>rest;for(int x:m){bool v=false;for(Pt p:h)if(pteq(p,I.P[x])){v=true;break;}if(v)rem.push_back(x);else rest.push_back(x);}m.swap(rest);
 }}
 if(mode==5){vector<int>all;for(int o:op)all.insert(all.end(),s.members[o].begin(),s.members[o].end());shuffle(all.begin(),all.end(),rng);all.resize(min(all.size(),rem.size()));rem.swap(all);}
 for(int x:rem)E.doRemove(x);
 Guide G(s,0.);recreate(E,G,rng,false,I.no,end);return true;
}
static bool geom_triple(Engine&E,mt19937_64&rng,double end){
 Sol&s=E.s;const Inst&I=E.I;auto op=geom_neighbors(s,rng,3);if(op.size()!=3)return false;
 vector<int>U;vector<int>quota(I.no);for(int o:op){quota[o]=s.size_[o];U.insert(U.end(),s.members[o].begin(),s.members[o].end());}
 for(int x=0;x<I.ns;x++)if(s.asg[x]<0&&I.servable[x]){bool good=false;for(int o:op)if(I.pr(o,x)>0)good=true;if(good)U.push_back(x);}
 double scale=max(1e-20,I.ext*I.ext);array<double,3>w;for(double&v:w)v=((double)(rng()%10001)/10000.-.5)*scale*.2;
 vector<pair<double,pair<int,int>>>order;Guide G(s,0.);
 for(int x:U){double best=1e300;int bo=-1;for(int j=0;j<3;j++){int o=op[j];double dx=I.P[x].x-I.P[I.ns+o].x,dy=I.P[x].y-I.P[I.ns+o].y;double d=dx*dx+dy*dy-w[j];if(d<best){best=d;bo=o;}}
  if(bo>=0&&G.eff(bo,x)>0)order.push_back({G.eff(bo,x),{x,bo}});
 }
 for(int x:U)if(s.asg[x]>=0)E.doRemove(x);
 sort(order.rbegin(),order.rend());for(auto&e:order){if(elapsed()>=end)break;int o=e.second.second;if(s.size_[o]<quota[o])E.doAdd(e.second.first,o);}
 recreate(E,G,rng,false,I.no,end);return true;
}
static bool geom_eject(Engine&E,mt19937_64&rng,double end){
 Sol&s=E.s;const Inst&I=E.I;vector<pair<double,pair<int,int>>>cand;
 for(int x=0;x<I.ns;x++)if(s.asg[x]<0&&I.servable[x])for(int o:I.cand[x])if(s.isopen[o]&&I.pr(o,x)>0){cand.push_back({I.pr(o,x),{x,o}});break;}
 if(cand.empty())return false;sort(cand.rbegin(),cand.rend());auto c=cand[rng()%min((size_t)20,cand.size())];int x=c.second.first,o=c.second.second;
 vector<Pt>h=s.hull[o];h.push_back(I.P[x]);hull_of(h);int removed=0,limit=max(12,I.ns/15);
 for(int q=0;q<I.no;q++)if(q!=o&&s.isopen[q]){
  for(int step=0;step<5&&elapsed()<end;step++){
   int z=-1;for(int p=0;p<I.ns+I.no;p++)if(geo_exact_covers(h,I.P[p])&&geo_exact_covers(s.hull[q],I.P[p])){z=p;break;}
   if(z<0)break;if(z==I.ns+q)return false;
   vector<int>best;double cost=1e300;
   for(int a=0;a<24;a++){
    double th=2*M_PI*a/24,dx=cos(th),dy=sin(th);Pt p=I.P[z],office=I.P[I.ns+q];
    if((office.x-p.x)*dx+(office.y-p.y)*dy<=0)continue;
    vector<int>cut;double loss=0;for(int y:s.members[q])if((I.P[y].x-p.x)*dx+(I.P[y].y-p.y)*dy<=0){cut.push_back(y);loss+=max(0.,I.pr(q,y));}
    if(!cut.empty()&&loss<cost){best=move(cut);cost=loss;}
   }
   if(best.empty()||removed+(int)best.size()>limit)return false;
   removed+=best.size();for(int y:best)E.doRemove(y);
  }
 }
 if(s.size_[o]>=I.maxsize[o]){int worst=-1;for(int y:s.members[o])if(worst<0||I.pr(o,y)<I.pr(o,worst))worst=y;if(worst>=0)E.doRemove(worst);}
 if(!E.doAdd(x,o))return false;Guide G(s,0.);recreate(E,G,rng,false,I.no,end);return true;
}
static void structural_search(Sol&s,mt19937_64&rng,double end,int mode){
 const Inst&I=*s.I;long tries=0,valid=0,win=0;double start=s.objective();
 while(elapsed()<end){auto a=s.asg;auto op=s.isopen;double f=s.objective();Engine E(s);E.rec=true;bool ok;
  double sub=min(end,elapsed()+.25);
  if(mode==4||mode==5)ok=geom_ruin(E,rng,mode,sub);else if(mode==6)ok=geom_triple(E,rng,sub);else ok=geom_eject(E,rng,sub);
  ++tries;
  if(ok&&elapsed()<end){repair_sizes(s);resize_dp(s,min(end,elapsed()+.05),false);repair_sizes(s);}
  s.recompute_psum();if(ok&&geom_feasible(s)){++valid;if(s.objective()>f+1e-9){++win;offer(I,s);continue;}}
  s.load_state(a,op);
 }
 fprintf(stderr,"geometry mode=%d tries=%ld valid=%ld accepted=%ld gain=%.9f\n",mode,tries,valid,win,s.objective()-start);
}
