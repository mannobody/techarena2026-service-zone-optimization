// Restricted-vertex maximum-weight island. All original points participate in weights/obstacles.
// The simple fan DP is O(K^4 + K^3*N), not the optimized cubic algorithm in the literature.
static bool gi_inside(const vector<Pt>&h,Pt p,double eps){
    if(h.empty())return false;
    if(h.size()==1)return hypot(h[0].x-p.x,h[0].y-p.y)<=eps;
    if(h.size()==2){double dx=h[1].x-h[0].x,dy=h[1].y-h[0].y;
        return fabs(cr(h[0],h[1],p))<=eps && (p.x-h[0].x)*dx+(p.y-h[0].y)*dy>=-eps && (p.x-h[1].x)*dx+(p.y-h[1].y)*dy<=eps;}
    for(size_t i=0;i<h.size();i++)if(cr(h[i],h[(i+1)%h.size()],p)<-eps)return false;
    return true;
}
struct IslandResult{double score=-1e100;vector<Pt> hull;long triangles=0;bool complete=true;};
static IslandResult gi_island(const vector<Pt>&points,const vector<double>&weight,const vector<char>&red,
                              vector<int> vertices,int mandatory,double end,double eps=1e-12){
    IslandResult result; const double BAD=-1e90;
    sort(vertices.begin(),vertices.end(),[&](int a,int b){return ptless(points[a],points[b]);});
    vertices.erase(unique(vertices.begin(),vertices.end(),[&](int a,int b){return pteq(points[a],points[b]);}),vertices.end());
    int K=vertices.size(),N=points.size();vector<double>w=weight;
    double bonus=1;for(double v:w)bonus+=fabs(v);if(mandatory>=0)w[mandatory]+=bonus;
    auto score=[&](const vector<Pt>&poly){double v=0;for(int x=0;x<N;x++)if(gi_inside(poly,points[x],eps)){if(red[x])return BAD;v+=w[x];}return v;};
    auto take=[&](double value,vector<Pt> poly){if(value>BAD/2 && value>result.score && (mandatory<0||gi_inside(poly,points[mandatory],eps))){result.score=value;result.hull=move(poly);}};
    vector<vector<double>> seg(K,vector<double>(K,BAD));
    for(int i=0;i<K;i++){
        take(score({points[vertices[i]]}),{points[vertices[i]]});
        for(int j=i+1;j<K;j++){if(elapsed()>end){result.complete=false;goto done;}
            vector<Pt>h={points[vertices[i]],points[vertices[j]]};seg[i][j]=score(h);take(seg[i][j],h);}}
    for(int a=0;a<K;a++){
        Pt p=points[vertices[a]];vector<int>v;for(int j=a+1;j<K;j++)v.push_back(j);
        sort(v.begin(),v.end(),[&](int i,int j){double c=cr(p,points[vertices[i]],points[vertices[j]]);if(c!=0)return c>0;return hypot(points[vertices[i]].x-p.x,points[vertices[i]].y-p.y)<hypot(points[vertices[j]].x-p.x,points[vertices[j]].y-p.y);});
        int k=v.size();vector<vector<double>>dp(k,vector<double>(k,BAD));vector<vector<int>>prev(k,vector<int>(k,-1));
        for(int j=0;j<k;j++)for(int i=0;i<j;i++){
            if(elapsed()>end){result.complete=false;goto done;}
            Pt u=points[vertices[v[i]]],z=points[vertices[v[j]]];if(cr(p,u,z)<=eps)continue;
            vector<Pt>tri={p,u,z};double tw=score(tri);result.triangles++;if(tw<=BAD/2)continue;
            double best=tw;int pred=-1;
            for(int t=0;t<i;t++)if(dp[t][i]>BAD/2&&cr(points[vertices[v[t]]],u,z)>eps){double val=dp[t][i]+tw-seg[a][v[i]];if(val>best){best=val;pred=t;}}
            dp[i][j]=best;prev[i][j]=pred;
            if(best>result.score){vector<Pt>poly;int ci=i,cj=j;poly.push_back(z);
                for(;;){poly.push_back(points[vertices[v[ci]]]);int t=prev[ci][cj];if(t<0)break;cj=ci;ci=t;}
                poly.push_back(p);reverse(poly.begin(),poly.end());take(best,move(poly));}
        }
    }
    done: if(mandatory>=0&&result.score>BAD/2)result.score-=bonus;return result;
}
// Exact nonnegative weighted removal for one forbidden point, with protected anchors.
// A retained finite hull excludes q iff some strict halfplane through q contains it.
struct TrimResult{double loss=1e100;vector<int> remove;};
static TrimResult gi_trim(const vector<Pt>&pts,const vector<int>&members,const vector<double>&cost,
                          Pt q,const vector<Pt>&protect,double end,double eps){
    TrimResult res;vector<double>angles;const double PI=acos(-1.0),TAU=2*PI;
    for(int x:members){Pt p=pts[x];double a=atan2(p.y-q.y,p.x-q.x)+PI/2;for(int i=0;i<2;i++){double t=fmod(a+i*PI+TAU,TAU);angles.push_back(t);}}
    for(Pt p:protect){if(hypot(p.x-q.x,p.y-q.y)<=eps)return res;double a=atan2(p.y-q.y,p.x-q.x)+PI/2;for(int i=0;i<2;i++)angles.push_back(fmod(a+i*PI+TAU,TAU));}
    sort(angles.begin(),angles.end());angles.erase(unique(angles.begin(),angles.end()),angles.end());
    for(size_t i=0;i<angles.size();i++){
        if(elapsed()>end)break;double t=(angles[i]+(i+1<angles.size()?angles[i+1]:angles[0]+TAU))/2,dx=cos(t),dy=sin(t);bool ok=true;
        for(Pt p:protect)if(dx*(p.x-q.x)+dy*(p.y-q.y)<=eps){ok=false;break;}if(!ok)continue;
        double val=0;vector<int>rm;
        for(int x:members)if(dx*(pts[x].x-q.x)+dy*(pts[x].y-q.y)<=eps){val+=cost[x];rm.push_back(x);}
        if(val<res.loss){res.loss=val;res.remove=move(rm);}
    }return res;
}
// Event sweep; recompute the best few candidate directions against geometric tolerances.
static TrimResult gi_trim_sweep(const vector<Pt>&pts,const vector<int>&members,const vector<double>&cost,
                          Pt q,const vector<Pt>&protect,double end,double eps){
    struct Event{double a,d;int b;};vector<Event>ev;const double PI=acos(-1.),TAU=2*PI;TrimResult res;
    auto events=[&](Pt p,double w,int b){if(hypot(p.x-q.x,p.y-q.y)<=eps)return;double phi=atan2(p.y-q.y,p.x-q.x);
        ev.push_back({fmod(phi-PI/2+TAU,TAU),-w,-b});ev.push_back({fmod(phi+PI/2+TAU,TAU),w,b});};
    for(int x:members)events(pts[x],cost[x],0);
    for(Pt p:protect){if(hypot(p.x-q.x,p.y-q.y)<=eps)return res;events(p,0,1);}
    if(ev.empty())return res;sort(ev.begin(),ev.end(),[](auto&a,auto&b){return a.a<b.a;});
    double start=fmod((ev.back().a+TAU+ev.front().a)/2,TAU),loss=0;int bad=0;
    auto dot=[&](Pt p,double t){return cos(t)*(p.x-q.x)+sin(t)*(p.y-q.y);};
    for(int x:members)if(dot(pts[x],start)<=0)loss+=cost[x];for(Pt p:protect)bad+=dot(p,start)<=0;
    vector<pair<double,double>>rank;if(!bad)rank.push_back({loss,start});
    for(size_t i=0;i<ev.size();){if(elapsed()>end)break;size_t j=i;while(j<ev.size()&&ev[j].a==ev[i].a){loss+=ev[j].d;bad+=ev[j].b;j++;}
        double t=(ev[i].a+(j<ev.size()?ev[j].a:ev.front().a+TAU))/2;if(!bad)rank.push_back({loss,t});i=j;}
    sort(rank.begin(),rank.end());
    for(size_t j=0;j<min<size_t>(16,rank.size());j++){double t=rank[j].second;bool ok=true;for(Pt p:protect)if(dot(p,t)<=eps)ok=false;if(!ok)continue;
        double c=0;vector<int>rm;for(int x:members)if(dot(pts[x],t)<=eps){c+=cost[x];rm.push_back(x);}if(c<res.loss){res.loss=c;res.remove=move(rm);}}
    return res;
}
