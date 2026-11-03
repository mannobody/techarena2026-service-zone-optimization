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
 DPWindowResult result;int K=at.size(),G=grid.size();if(!G||!K)return result;DPWindowTree tree(G);
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
