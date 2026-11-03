// Original exact dyadic fallback for finite binary64 inputs; no external library.
// Filter principle follows robust orientation literature; fallback sums six exact products.
static bool g_geo_exact=!getenv("GEO_EXACT")||atoi(getenv("GEO_EXACT"));
struct GeoDyadic{uint64_t m;int e;bool neg;};
static GeoDyadic geo_decode(double x){uint64_t u;memcpy(&u,&x,8);int e=(u>>52)&2047;return{(u&((1ULL<<52)-1))|(e?(1ULL<<52):0),e?e-1023-52:-1074,(bool)(u>>63)};}
static int geo_exact_orientation(Pt a,Pt b,Pt c){
 GeoDyadic v[6]={geo_decode(a.x),geo_decode(a.y),geo_decode(b.x),geo_decode(b.y),geo_decode(c.x),geo_decode(c.y)};
 const int ij[6][3]={{0,3,0},{2,5,0},{4,1,0},{1,2,1},{3,4,1},{5,0,1}};int emin=10000;
 for(auto&t:ij)if(v[t[0]].m&&v[t[1]].m)emin=min(emin,v[t[0]].e+v[t[1]].e);if(emin==10000)return 0;
 array<uint64_t,70>pos{},neg{};
 auto addword=[](array<uint64_t,70>&arr,int i,uint64_t z){while(z&&i<70){uint64_t old=arr[i];arr[i]+=z;z=arr[i]<old;i++;}};
 for(auto&t:ij){auto u=v[t[0]],w=v[t[1]];if(!u.m||!w.m)continue;unsigned __int128 product=(unsigned __int128)u.m*w.m;int shift=u.e+w.e-emin,word=shift/64,bit=shift%64;auto&arr=(u.neg^w.neg^(bool)t[2])?neg:pos;
  uint64_t lo=(uint64_t)product,hi=(uint64_t)(product>>64);addword(arr,word,lo<<bit);addword(arr,word+1,hi<<bit);
  if(bit){addword(arr,word+1,lo>>(64-bit));addword(arr,word+2,hi>>(64-bit));}}
 for(int i=69;i>=0;i--)if(pos[i]!=neg[i])return pos[i]>neg[i]?1:-1;return 0;
}
static int geo_orientation(Pt a,Pt b,Pt c){
 double ax=a.x-c.x,bx=b.x-c.x,ay=a.y-c.y,by=b.y-c.y;
 double left=ax*by,right=ay*bx,det=left-right,sum=fabs(left)+fabs(right);
 if(isfinite(sum)&&sum>1e-280&&fabs(det)>1.7763568394002505e-15*sum)return det>0?1:-1;
 return geo_exact_orientation(a,b,c);
}
static double geo_turn(Pt a,Pt b,Pt c){return g_geo_exact?(double)geo_orientation(a,b,c):cr(a,b,c);}
static bool geo_on_segment(Pt a,Pt b,Pt p){return geo_orientation(a,b,p)==0&&p.x>=min(a.x,b.x)&&p.x<=max(a.x,b.x)&&p.y>=min(a.y,b.y)&&p.y<=max(a.y,b.y);}
static bool geo_exact_covers(const vector<Pt>&h,Pt p){
 int m=h.size();if(!m)return false;if(m==1)return pteq(h[0],p);if(m==2)return geo_on_segment(h[0],h[1],p);
 if(m<=8){for(int i=0;i<m;i++)if(geo_orientation(h[i],h[(i+1)%m],p)<0)return false;return true;}
 int a=geo_orientation(h[0],h[1],p),b=geo_orientation(h[0],h[m-1],p);if(a<0||b>0)return false;
 if(a==0)return geo_on_segment(h[0],h[1],p);if(b==0)return geo_on_segment(h[0],h[m-1],p);
 int lo=1,hi=m-1;while(hi-lo>1){int mid=(lo+hi)/2;if(geo_orientation(h[0],h[mid],p)>=0)lo=mid;else hi=mid;}return geo_orientation(h[lo],h[hi],p)>=0;
}
