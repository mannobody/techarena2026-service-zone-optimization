// Immutable uniform-grid index of ALL input points, including closed offices/unassigned sites.
// Query is only a broad phase; original predicates remain unchanged.
struct GeoGrid{
 const Inst* inst=nullptr;int side=1;double minx=0,miny=0,sx=1,sy=1;bool enabled=true;
 vector<vector<int>>bucket;vector<int>all;
 int bx(double x)const{double v=(x-minx)*sx;if(v<=0)return 0;if(v>=side)return side-1;return (int)v;}
 int by(double y)const{double v=(y-miny)*sy;if(v<=0)return 0;if(v>=side)return side-1;return (int)v;}
 void init(const Inst&I){inst=&I;enabled=!getenv("GEO_INDEX")||atoi(getenv("GEO_INDEX"));int n=I.P.size();all.resize(n);iota(all.begin(),all.end(),0);side=max(1,min(128,(int)sqrt(max(1,n)/12.)));bucket.assign(side*side,{});if(!n)return;
  minx=miny=1e300;double maxx=-1e300,maxy=-1e300;for(Pt p:I.P){minx=min(minx,p.x);miny=min(miny,p.y);maxx=max(maxx,p.x);maxy=max(maxy,p.y);}sx=side/max(1e-100,maxx-minx);sy=side/max(1e-100,maxy-miny);
  for(int i=0;i<n;i++)bucket[by(I.P[i].y)*side+bx(I.P[i].x)].push_back(i);
 }
 const vector<int>& query(const Inst&I,double x0,double x1,double y0,double y1)const{
  if(!enabled||inst!=&I||side==1)return all;int a=bx(x0),b=bx(x1),c=by(y0),d=by(y1);
  if((b-a+1)*(d-c+1)*2>side*side)return all;
  static thread_local vector<int>v;v.clear();for(int y=c;y<=d;y++)for(int x=a;x<=b;x++)v.insert(v.end(),bucket[y*side+x].begin(),bucket[y*side+x].end());return v;
 }
};
static GeoGrid g_geo_grid;
