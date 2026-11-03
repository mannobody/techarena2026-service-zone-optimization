// base.h: заголовки std, время (elapsed), глобальные флаги отладки.
// Часть solve.cpp (одна единица трансляции): включается только из него, порядок важен.

#include <algorithm>
#include <array>
#include <atomic>
#include <chrono>
#include <climits>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <iterator>
#include <memory>
#include <mutex>
#include <numeric>
#include <random>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <thread>
#include <unistd.h>
#include <fcntl.h>
#include <sched.h>
#include <malloc.h>
#include <csignal>
#include <vector>
#include <map>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

using namespace std;
using Clock = chrono::steady_clock;
static const Clock::time_point T0 = Clock::now();
static inline double elapsed() { return chrono::duration<double>(Clock::now() - T0).count(); }

static const double NEG = -1e300;
static bool DBG = false, DBG2 = false;

// Exact optimization of the SAME grid-window objective as legacy resize_dp.
// Monotone maxima stacks + range-add segment tree: O(K G log G).
struct DPWindowResult {int lo=-1,hi=-1;long double score=0;bool complete=true;};
struct DPWindowTree {
 struct Node{int bad=100000000,where=0,lazy_bad=0;long double value=0,lazy_value=0;};
 int n;vector<Node>t;
 DPWindowTree(int n_):n(n_),t(4*n_+4){}
 void apply(int p,int b,long double v){t[p].bad+=b;t[p].value+=v;t[p].lazy_bad+=b;t[p].lazy_value+=v;}
 void down(int p){if(t[p].lazy_bad||t[p].lazy_value){apply(p*2,t[p].lazy_bad,t[p].lazy_value);apply(p*2+1,t[p].lazy_bad,t[p].lazy_value);t[p].lazy_bad=0;t[p].lazy_value=0;}}
 void pull(int p){const auto&a=t[p*2];const auto&b=t[p*2+1];const auto&v=(a.bad<b.bad||(a.bad==b.bad&&(a.value>b.value||(a.value==b.value&&a.where<b.where))))?a:b;t[p].bad=v.bad;t[p].value=v.value;t[p].where=v.where;}
 void set(int p,int l,int r,int x,int bad,long double value){if(l==r){t[p]={bad,x,0,value,0};return;}down(p);int m=(l+r)/2;if(x<=m)set(p*2,l,m,x,bad,value);else set(p*2+1,m+1,r,x,bad,value);pull(p);}
 void add(int p,int l,int r,int a,int b,int bad,long double value){if(a>r||b<l)return;if(a<=l&&r<=b){apply(p,bad,value);return;}down(p);int m=(l+r)/2;add(p*2,l,m,a,b,bad,value);add(p*2+1,m+1,r,a,b,bad,value);pull(p);}
};
static DPWindowResult dp_fast_window(const vector<vector<double>>&at,const vector<vector<double>>&blk,const vector<int>&grid,const vector<double>&cost,double alpha,bool allow_close,double deadline){
 DPWindowResult result;int K=at.size(),G=grid.size();if(!G||!K)return result;
 // Small grids have too little work to amortize segment-tree overhead.
 if(G<=128){
  vector<double>run(K);
  for(int l=0;l<G;l++){
   if((l&31)==0&&elapsed()>=deadline){result.complete=false;break;}
   for(int k=0;k<K;k++)run[k]=at[k][l];
   for(int r=l;r<G;r++){
    long double score=-(long double)alpha*(grid[r]-grid[l]);bool valid=true;
    for(int k=0;k<K;k++){
     if(r>l)run[k]=max(run[k],blk[k][r]);
     if(run[k]<=NEG/2){if(!allow_close)valid=false;}
     else score+=allow_close?max((long double)0,(long double)run[k]-cost[k]):(long double)run[k]-cost[k];
    }
    if(valid&&score>result.score+1e-9L){result.score=score;result.lo=l;result.hi=r;}
   }
  }return result;
 }
 DPWindowTree tree(G);
 struct Item{int left;long double value;bool feasible;};vector<vector<Item>>st(K);
 auto item=[&](int o,double f,int left){bool ok=f>NEG/2;long double v=ok?(long double)f-cost[o]:0;if(allow_close){ok=true;v=max((long double)0,v);}return Item{left,v,ok};};
 auto le=[](const Item&a,const Item&b){return !a.feasible || (b.feasible&&a.value<=b.value);};
 for(int r=0;r<G;r++){
  if((r&31)==0&&elapsed()>=deadline){result.complete=false;break;}
  int bad=0;long double val=(long double)alpha*grid[r];for(int o=0;o<K;o++){auto a=item(o,at[o][r],r);bad+=!a.feasible;val+=a.value;}
  tree.set(1,0,G-1,r,bad,val);
  for(int o=0;o<K;o++){
   auto b=item(o,blk[o][r],r);int left=r;
   while(!st[o].empty()&&le(st[o].back(),b)){
    auto old=st[o].back();st[o].pop_back();tree.add(1,0,G-1,old.left,left-1,(int)!b.feasible-(int)!old.feasible,b.value-old.value);left=old.left;
   }
   if(left<r){b.left=left;st[o].push_back(b);}
   auto a=item(o,at[o][r],r);
   if(st[o].empty()||st[o].back().feasible!=a.feasible||st[o].back().value!=a.value)st[o].push_back(a);
  }
  if(tree.t[1].bad==0){long double value=tree.t[1].value-(long double)alpha*grid[r];if(value>result.score+1e-9L){result.score=value;result.lo=tree.t[1].where;result.hi=r;}}
 }
 return result;
}

int main(){mt19937_64 rng(221000);int checks=0;for(int test=0;test<2000;test++){
 int K=1+rng()%12,G=1+rng()%400;vector<int>grid(G);for(int i=1;i<G;i++)grid[i]=grid[i-1]+1+rng()%6;
 vector<vector<double>>at(K,vector<double>(G,NEG)),blk=at;vector<double>cost(K);
 for(int k=0;k<K;k++){cost[k]=(int)(rng()%50)-10;for(int j=0;j<G;j++)for(int l=j?grid[j-1]+1:0;l<=grid[j];l++){double f=rng()%4?((int)(rng()%2000)-400)/10.:NEG;blk[k][j]=max(blk[k][j],f);if(l==grid[j])at[k][j]=f;}}
 double alpha=test%7==0?1e10:(rng()%100)/10.;bool close=test%2;long double best=0;
 for(int l=0;l<G;l++){vector<double>run(K);for(int k=0;k<K;k++)run[k]=at[k][l];for(int r=l;r<G;r++){long double value=-(long double)alpha*(grid[r]-grid[l]);bool ok=true;
  for(int k=0;k<K;k++){if(r>l)run[k]=max(run[k],blk[k][r]);if(run[k]<=NEG/2){if(!close)ok=false;}else value+=close?max((long double)0,(long double)run[k]-cost[k]):(long double)run[k]-cost[k];}
  if(ok)best=max(best,value);
 }}
 auto got=dp_fast_window(at,blk,grid,cost,alpha,close,1e9);if(!got.complete||fabsl(best-got.score)>1e-6L){fprintf(stderr,"FAIL test=%d K=%d G=%d expected=%.18Lg got=%.18Lg\n",test,K,G,best,got.score);return 1;}checks++;
 }printf("{\"seed\":221000,\"checks\":%d}\n",checks);}
