// Certified routes; no learned instance identifier and no external solver library.
namespace specialists {
using namespace std;
using spatial::Inst;
static bool nonnegative_costs(const Inst&I){return all_of(I.cost.begin(),I.cost.end(),[](double x){return x>=0;});}
static bool publish(const Inst&I,const vector<int>&asg,const vector<char>&op,const vector<int>&workers,double expected,const char*method){
 double value=0;if(!spatial::verify(I,asg,op,workers,&value))return false;
 if(fabs(value-expected)>1e-7*max(1.,fabs(value)))return false;
 portfolio::submit(1,value,spatial::serialize(I,asg,op,workers),&asg,&op);
 fprintf(stderr,"AP_ROUTE method=%s objective=%.9f certified=1 sites=%d offices=%d t=%.6f\n",method,value,I.ns,I.no,portfolio::elapsed());return true;
}
static bool single_office(const Inst&I){
 if(I.no!=1||!nonnegative_costs(I))return false;
 vector<pair<double,int>>p;for(int s=0;s<I.ns;s++)if(I.servable[s]&&I.pr(0,s)>0)p.push_back({I.pr(0,s),s});
 sort(p.rbegin(),p.rend());if(p.size()>(size_t)I.maxsize[0])p.resize(I.maxsize[0]);
 double gain=-I.cost[0];for(auto q:p)gain+=q.first;
 vector<int>a(I.ns,-1),w(I.nw,-1);vector<char>op(1,0);
 if(gain>0&&!p.empty()){for(auto q:p)a[q.second]=0;fill(w.begin(),w.end(),0);op[0]=1;}
 return publish(I,a,op,w,max(0.,gain),"single_office_exact");
}
static bool collinear(const Inst&I,double limit){
 if(I.ns>256||I.no>16||I.no<1||I.alpha!=0||!nonnegative_costs(I)||I.A<*max_element(I.maxsize.begin(),I.maxsize.end()))return false;
 vector<int>required(I.nsk,0);for(const auto&k:I.skillset)for(int s:k)required[s]=1;
 bool tasks=any_of(required.begin(),required.end(),[](int k){return k;});
 if(tasks){
  if(I.nw<I.no)return false;
  for(int w=0;w<I.nw;w++)for(int k=0;k<I.nsk;k++)if(required[k]&&!I.wmask[w][k])return false;
 }
 int b=1;while(b<(int)I.P.size()&&spatial::pteq(I.P[0],I.P[b]))b++;
 if(b<(int)I.P.size())for(auto p:I.P)if(spatial::geo_orientation(I.P[0],I.P[b],p)!=0)return false;
 bool usex=b==(int)I.P.size()||I.P[b].x!=I.P[0].x;
 vector<double>coords;for(auto p:I.P)coords.push_back(usex?p.x:p.y);
 vector<double>unique=coords;sort(unique.begin(),unique.end());unique.erase(std::unique(unique.begin(),unique.end()),unique.end());int n=unique.size();
 vector<int>rank;for(double x:coords)rank.push_back(lower_bound(unique.begin(),unique.end(),x)-unique.begin());
 vector<vector<int>>at(n);for(int s=0;s<I.ns;s++)at[rank[s]].push_back(s);
 vector<double>zone((size_t)n*n,0.);vector<int>office((size_t)n*n,-1);
 // Every true interval is represented. Extra unselected points inside its hull are allowed.
 for(int o=0;o<I.no;o++){
  int cap=I.maxsize[o];if(cap<=0)continue;
  for(int l=0;l<=rank[I.ns+o];l++){
   if(portfolio::elapsed()>limit-.1)return false;
   vector<double>heap;double sum=0;
   for(int r=l;r<n;r++){
    for(int s:at[r])if(I.pr(o,s)>0){
     double p=I.pr(o,s);heap.push_back(p);push_heap(heap.begin(),heap.end(),greater<double>());sum+=p;
     if(heap.size()>(size_t)cap){pop_heap(heap.begin(),heap.end(),greater<double>());sum-=heap.back();heap.pop_back();}
    }
    if(r<rank[I.ns+o]||heap.empty())continue;size_t k=(size_t)l*n+r;double gain=sum-I.cost[o];
    if(gain>zone[k]){zone[k]=gain;office[k]=o;}
   }
  }
 }
 vector<double>dp(n+1,0);vector<int>left(n+1,-1),chosen(n+1,-1);
 for(int r=0;r<n;r++){
  dp[r+1]=dp[r];
  for(int l=0;l<=r;l++)if(office[(size_t)l*n+r]>=0){double value=dp[l]+zone[(size_t)l*n+r];if(value>dp[r+1]+1e-10){dp[r+1]=value;left[r+1]=l;chosen[r+1]=office[(size_t)l*n+r];}}
 }
 vector<int>a(I.ns,-1),w(I.nw,-1);vector<char>op(I.no,0);int worker=0;
 for(int end=n;end>0;){
  if(chosen[end]<0){end--;continue;}int o=chosen[end],l=left[end];if(op[o])return false;op[o]=1;
  vector<pair<double,int>>p;for(int s=0;s<I.ns;s++)if(rank[s]>=l&&rank[s]<end&&I.pr(o,s)>0)p.push_back({I.pr(o,s),s});
  sort(p.rbegin(),p.rend());if(p.size()>(size_t)I.maxsize[o])p.resize(I.maxsize[o]);for(auto q:p)a[q.second]=o;
  if(tasks)w[worker++]=o;end=l;
 }
 return publish(I,a,op,w,dp[n],"collinear_interval_exact");
}
}
