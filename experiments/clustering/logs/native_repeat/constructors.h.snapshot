// Research constructors; only instance/solution I/O, no external libraries.
static bool cluster_linear_solve(vector<double> a, vector<double> b, vector<double>& x) {
    int n=b.size();x.assign(n,0.);
    for(int k=0;k<n;k++) {
        int p=k;for(int i=k+1;i<n;i++)if(fabs(a[i*n+k])>fabs(a[p*n+k]))p=i;
        if(fabs(a[p*n+k])<1e-14)return false;
        if(p!=k){for(int j=k;j<n;j++)swap(a[k*n+j],a[p*n+j]);swap(b[k],b[p]);}
        for(int i=k+1;i<n;i++) {
            double f=a[i*n+k]/a[k*n+k];
            for(int j=k;j<n;j++)a[i*n+j]-=f*a[k*n+j];b[i]-=f*b[k];
        }
    }
    for(int k=n-1;k>=0;k--){double v=b[k];for(int j=k+1;j<n;j++)v-=a[k*n+j]*x[j];x[k]=v/a[k*n+k];}
    return true;
}

struct ClusterCosts {
    int n,k;double scale=1.;vector<double> geo,road;vector<array<double,3>> phi,office;
    ClusterCosts(const Inst&I,const vector<int>&op):n(I.ns),k(op.size()),geo((size_t)n*k),road(geo.size()),phi(n),office(k) {
        double span=max(I.ext,1e-12),ox=I.P[I.ns+op[0]].x,oy=I.P[I.ns+op[0]].y;
        double gs=0.,rs=0.;
        for(int b=0;b<k;b++)office[b]={(I.P[I.ns+op[b]].x-ox)/span,(I.P[I.ns+op[b]].y-oy)/span,1.};
        for(int s=0;s<n;s++) {
            phi[s]={(I.P[s].x-ox)/span,(I.P[s].y-oy)/span,1.};
            double gl=1e300,gh=-1e300,rl=1e300,rh=-1e300;
            for(int b=0;b<k;b++) {
                double dx=phi[s][0]-office[b][0],dy=phi[s][1]-office[b][1];
                double g=dx*dx+dy*dy,r=I.d(op[b],s);geo[(size_t)s*k+b]=g;road[(size_t)s*k+b]=r;
                gl=min(gl,g);gh=max(gh,g);rl=min(rl,r);rh=max(rh,r);
            }
            gs+=gh-gl;rs+=rh-rl;
            for(int b=0;b<k;b++){geo[(size_t)s*k+b]-=gl;road[(size_t)s*k+b]-=rl;}
        }
        scale=max(gs/max(1,n),1e-12);rs=max(rs/max(1,n),1e-12);
        for(double&v:geo)v/=scale;for(double&v:road)v/=rs;
    }
    vector<int> labels(const vector<double>&cost) const {
        vector<int> cell(n);
        for(int s=0;s<n;s++)for(int b=1;b<k;b++)if(cost[(size_t)s*k+b]<cost[(size_t)s*k+cell[s]])cell[s]=b;
        return cell;
    }
};

static vector<int> cluster_mixed(const Inst&I,const vector<int>&op,int which) {
    ClusterCosts c(I,op);double lambda=(which+1)/4.;
    for(size_t j=0;j<c.geo.size();j++)c.geo[j]=lambda*c.geo[j]+(1.-lambda)*c.road[j];
    auto cell=c.labels(c.geo);for(int&v:cell)v=op[v];return cell;
}

static vector<int> cluster_ot(const Inst&I,const vector<int>&op,int which,double deadline) {
    ClusterCosts c(I,op);int K=c.k;vector<double> h(K,0.),mass(c.n,1.);double total=0.;
    for(int s=0;s<c.n;s++){mass[s]=I.servable[s]?(which?I.ntask[s]:1.):0.;total+=mass[s];}
    double target=total/max(1,K);
    auto value=[&](const vector<double>&hh,double tau,vector<double>*grad,vector<double>*H)->double {
        if(grad)grad->assign(K,-target);if(H)H->assign((size_t)K*K,0.);
        vector<double> p(K);double f=-target*accumulate(hh.begin(),hh.end(),0.);
        for(int s=0;s<c.n;s++)if(mass[s]>0) {
            if((s&127)==0&&elapsed()>=deadline)return numeric_limits<double>::infinity();
            double mx=-1e300;
            for(int b=0;b<K;b++){p[b]=(hh[b]-c.geo[(size_t)s*K+b])/tau;mx=max(mx,p[b]);}
            double sum=0.;for(double&v:p){v=exp(v-mx);sum+=v;}
            f+=mass[s]*tau*(mx+log(sum));
            if(grad){for(int b=0;b<K;b++){p[b]/=sum;(*grad)[b]+=mass[s]*p[b];}}
            if(H)for(int a=0;a<K;a++)for(int b=0;b<K;b++)
                (*H)[a*K+b]+=mass[s]*((a==b?p[a]:0.)-p[a]*p[b])/tau;
        }
        return f;
    };
    // Project weight differences so every office stays in its own power cell.
    auto anchor=[&](vector<double>&hh)->bool {
        for(int pass=0;pass<4*K;pass++) {
            double worst=0.;
            for(int a=0;a<K;a++)for(int b=a+1;b<K;b++) {
                double dx=c.office[a][0]-c.office[b][0],dy=c.office[a][1]-c.office[b][1];
                double bound=(dx*dx+dy*dy)/c.scale*(1.-1e-9);
                double d=hh[a]-hh[b];double excess=fabs(d)-bound;worst=max(worst,excess);
                if(excess>0){double v=copysign(.5*excess,d);hh[a]-=v;hh[b]+=v;}
            }
            if(worst<1e-10)return true;
        }
        return false;
    };
    if(K>1&&total>0)for(int stage=0;stage<3&&elapsed()<deadline;stage++) {
        double tau=pow(max(1,c.n),-.25*stage);
        for(int it=0;it<12&&elapsed()<deadline;it++) {
            vector<double> g,H;double old=value(h,tau,&g,&H);
            if(!isfinite(old))break;
            double residual=0.;for(double v:g)residual=max(residual,fabs(v));
            if(residual<max(1e-5,total*1e-4))break;
            vector<double>a((K-1)*(K-1)),b(K-1),delta;
            for(int i=0;i<K-1;i++){b[i]=-g[i];for(int j=0;j<K-1;j++)a[i*(K-1)+j]=H[i*K+j];a[i*(K-1)+i]+=max(1e-10,total*1e-10);}
            if(!cluster_linear_solve(a,b,delta))break;delta.push_back(0.);
            bool accepted=false;
            for(double step=1.;step>1e-5&&elapsed()<deadline;step*=.5) {
                auto next=h;for(int j=0;j<K;j++)next[j]+=step*delta[j];
                if(!anchor(next))continue;
                double f=value(next,tau,nullptr,nullptr);
                if(f<old-1e-10){h.swap(next);accepted=true;break;}
            }
            if(!accepted)break;
        }
    }
    for(int s=0;s<c.n;s++)for(int b=0;b<K;b++)c.geo[(size_t)s*K+b]-=h[b];
    auto cell=c.labels(c.geo);for(int&v:cell)v=op[v];return cell;
}

static vector<int> cluster_affine(const Inst&I,const vector<int>&op,int which,double deadline) {
    ClusterCosts c(I,op);int K=c.k;vector<array<double,3>> theta(K);
    auto dot=[](const array<double,3>&a,const array<double,3>&b){return a[0]*b[0]+a[1]*b[1]+a[2]*b[2];};
    for(int b=0;b<K;b++)theta[b]={2*c.office[b][0],2*c.office[b][1],-dot(c.office[b],c.office[b])+1.};
    double sep=1e300;
    for(int a=0;a<K;a++)for(int b=a+1;b<K;b++) {
        double dx=c.office[a][0]-c.office[b][0],dy=c.office[a][1]-c.office[b][1];sep=min(sep,dx*dx+dy*dy);
    }
    if(sep<1e-20){auto cell=c.labels(c.geo);for(int&v:cell)v=op[v];return cell;}
    double margin=K>1?sep*.01:0.;
    auto project=[&](vector<array<double,3>>&t) {
        for(int pass=0;pass<max(8,4*K)&&elapsed()<deadline;pass++) {
            double worst=0.;
            for(int a=0;a<K;a++)for(int b=0;b<K;b++)if(a!=b) {
                double v=dot(t[b],c.office[a])-dot(t[a],c.office[a])+margin;worst=max(worst,v);
                if(v>0){double d=v/(2*dot(c.office[a],c.office[a]));for(int j=0;j<3;j++){t[a][j]+=d*c.office[a][j];t[b][j]-=d*c.office[a][j];}}
            }
            if(worst<1e-9)break;
        }
    };
    if(!which) {
        vector<double> gram(9,0.);
        for(const auto&x:c.phi)for(int i=0;i<3;i++)for(int j=0;j<3;j++)gram[i*3+j]+=x[i]*x[j];
        for(int j=0;j<3;j++)gram[j*3+j]+=max(1,c.n)*1e-8;
        for(int b=0;b<K&&elapsed()<deadline;b++) {
            vector<double> rhs(3,0.),sol;
            for(int s=0;s<c.n;s++)for(int j=0;j<3;j++)rhs[j]-=c.road[(size_t)s*K+b]*c.phi[s][j];
            if(cluster_linear_solve(gram,rhs,sol))for(int j=0;j<3;j++)theta[b][j]=sol[j];
        }
        project(theta);
    } else {
        vector<double> teacher=c.road;
        for(int s=0;s<c.n;s++) {
            double sum=0.;for(int b=0;b<K;b++){auto&v=teacher[(size_t)s*K+b];v=exp(-v);sum+=v;}
            for(int b=0;b<K;b++)teacher[(size_t)s*K+b]/=sum;
        }
        double lipschitz=0.;for(auto&x:c.phi)lipschitz+=dot(x,x);double rate=1./max(1e-12,.5*lipschitz/max(1,c.n));
        for(int it=0;it<80&&elapsed()<deadline;it++) {
            vector<array<double,3>> grad(K,array<double,3>{0.,0.,0.});vector<double> prob(K);
            for(int s=0;s<c.n;s++) {
                double mx=-1e300;for(int b=0;b<K;b++){prob[b]=dot(theta[b],c.phi[s]);mx=max(mx,prob[b]);}
                double sum=0.;for(double&v:prob){v=exp(v-mx);sum+=v;}
                for(int b=0;b<K;b++)for(int j=0;j<3;j++)grad[b][j]+=(prob[b]/sum-teacher[(size_t)s*K+b])*c.phi[s][j];
            }
            for(int b=0;b<K;b++)for(int j=0;j<3;j++)theta[b][j]-=rate*grad[b][j]/max(1,c.n);
            project(theta);
        }
    }
    bool valid=true;
    for(int a=0;a<K;a++)for(int b=0;b<K;b++)if(a!=b&&dot(theta[a],c.office[a])<dot(theta[b],c.office[a])+margin*.5)valid=false;
    vector<int> cell=c.labels(c.geo);
    if(valid)for(int s=0;s<c.n;s++){cell[s]=0;for(int b=1;b<K;b++)if(dot(theta[b],c.phi[s])>dot(theta[cell[s]],c.phi[s]))cell[s]=b;}
    for(int&v:cell)v=op[v];return cell;
}

static vector<int> ctor_cluster(const Inst&I,const vector<int>&op,int mode,int which,double deadline) {
    if(mode==1)return cluster_mixed(I,op,which);
    if(mode==2)return cluster_ot(I,op,which,deadline);
    return cluster_affine(I,op,which,deadline);
}
