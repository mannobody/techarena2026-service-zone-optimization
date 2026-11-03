// Optimize road utility directly over affine convex cells, with smooth labels.
// Capacity/count penalties and smoothed task range are surrogates. Realize/verify
// still decide feasibility and the actual objective.
struct SoftClusterProfit {
    const Inst& I;ClusterCosts c;bool reject;double scale=1.,alpha=0.;
    vector<double> profit;
    SoftClusterProfit(const Inst&in,const vector<int>&op,bool r):I(in),c(in,op),reject(r),profit((size_t)c.n*c.k) {
        double sum=0.;for(int s=0;s<c.n;s++)for(int b=0;b<c.k;b++)sum+=fabs(I.pr(op[b],s));
        scale=max(1e-12,sum/max(1,c.n*c.k));alpha=I.alpha/scale;
        for(int s=0;s<c.n;s++)for(int b=0;b<c.k;b++)profit[(size_t)s*c.k+b]=I.servable[s]?I.pr(op[b],s)/scale:-1.;
    }
    double eval(const vector<array<double,3>>&theta,const vector<int>&op,double tau,
                vector<array<double,3>>*grad,double deadline) const {
        int K=c.k,Q=K+(reject?1:0);vector<double> p((size_t)c.n*Q),count(K,0.),load(K,0.);
        double loss=0.;
        for(int s=0;s<c.n;s++) {
            if((s&127)==0&&elapsed()>=deadline)return numeric_limits<double>::infinity();
            if(!I.servable[s])continue;
            double mx=reject?0.:-1e300;
            for(int b=0;b<K;b++){double z=0.;for(int j=0;j<3;j++)z+=theta[b][j]*c.phi[s][j];p[(size_t)s*Q+b]=z/tau;mx=max(mx,z/tau);}
            if(reject)p[(size_t)s*Q+K]=0.;
            double sum=0.;for(int b=0;b<Q;b++){auto&v=p[(size_t)s*Q+b];v=exp(v-mx);sum+=v;}
            for(int b=0;b<Q;b++)p[(size_t)s*Q+b]/=sum;
            for(int b=0;b<K;b++){double v=p[(size_t)s*Q+b];count[b]+=v;load[b]+=v*I.ntask[s];loss-=v*profit[(size_t)s*K+b];}
        }
        vector<double> dc(K,0.),dl(K,0.);double beta=(double)K/max(1,c.n);
        for(int b=0;b<K;b++){double over=max(0.,count[b]-I.maxsize[op[b]]);loss+=.5*beta*over*over;dc[b]+=beta*over;}
        int hi=max_element(count.begin(),count.end())-count.begin(),lo=min_element(count.begin(),count.end())-count.begin();
        double over=max(0.,count[hi]-count[lo]-I.A);loss+=.5*beta*over*over;dc[hi]+=beta*over;dc[lo]-=beta*over;
        double tl=max(1.,sqrt((double)max(1,I.totalTasks))/max(1,K))*tau;
        double lh=*max_element(load.begin(),load.end()),ll=*min_element(load.begin(),load.end());
        double plus=0.,minus=0.;for(double v:load){plus+=exp((v-lh)/tl);minus+=exp((ll-v)/tl);}
        double range=lh-ll+tl*(log(plus)+log(minus)-2*log((double)K));
        loss+=alpha*max(0.,range);
        if(range>0)for(int b=0;b<K;b++)dl[b]=alpha*(exp((load[b]-lh)/tl)/plus-exp((ll-load[b])/tl)/minus);
        if(grad) {
            grad->assign(K,array<double,3>{0.,0.,0.});vector<double> du(K);
            for(int s=0;s<c.n;s++) {
                if((s&127)==0&&elapsed()>=deadline)return numeric_limits<double>::infinity();
                double mean=0.;
                for(int b=0;b<K;b++){du[b]=-profit[(size_t)s*K+b]+dc[b]+dl[b]*I.ntask[s];mean+=p[(size_t)s*Q+b]*du[b];}
                for(int b=0;b<K;b++)for(int j=0;j<3;j++)
                    (*grad)[b][j]+=p[(size_t)s*Q+b]*(du[b]-mean)*c.phi[s][j]/(tau*max(1,c.n));
            }
        }
        return loss/max(1,c.n);
    }
};

static vector<int> cluster_soft_profit(const Inst&I,const vector<int>&op,int which,double deadline) {
    SoftClusterProfit m(I,op,which!=0);int K=m.c.k;vector<array<double,3>>theta(K);
    auto dot=[](const array<double,3>&a,const array<double,3>&b){return a[0]*b[0]+a[1]*b[1]+a[2]*b[2];};
    double sep=1.;for(int a=0;a<K;a++)for(int b=a+1;b<K;b++){
        double dx=m.c.office[a][0]-m.c.office[b][0],dy=m.c.office[a][1]-m.c.office[b][1];sep=min(sep,dx*dx+dy*dy);
    }
    double margin=max(1e-12,sep*.01);
    for(int b=0;b<K;b++)theta[b]={2*m.c.office[b][0],2*m.c.office[b][1],2.-dot(m.c.office[b],m.c.office[b])};
    auto project=[&](vector<array<double,3>>&t){
        for(int pass=0;pass<max(8,4*K)&&elapsed()<deadline;pass++) {
            double worst=0.;
            for(int a=0;a<K;a++) {
                if(m.reject){double v=margin-dot(t[a],m.c.office[a]);worst=max(worst,v);
                    if(v>0)for(int j=0;j<3;j++)t[a][j]+=v*m.c.office[a][j]/dot(m.c.office[a],m.c.office[a]);}
                for(int b=0;b<K;b++)if(a!=b){
                    double v=dot(t[b],m.c.office[a])-dot(t[a],m.c.office[a])+margin;worst=max(worst,v);
                    if(v>0)for(int j=0;j<3;j++){double d=v*m.c.office[a][j]/(2*dot(m.c.office[a],m.c.office[a]));t[a][j]+=d;t[b][j]-=d;}
                }
            }
            if(worst<1e-9)break;
        }
    };
    double first=0.,last=0.;int accepted=0,maxTask=0;for(int t:I.ntask)maxTask=max(maxTask,t);
    for(int stage=0;stage<3&&elapsed()<deadline;stage++) {
        double tau=pow(max(2,m.c.n),-.25*stage);
        for(int it=0;it<25&&elapsed()<deadline;it++) {
            vector<array<double,3>> g;double before=m.eval(theta,op,tau,&g,deadline);
            if(!isfinite(before))break;
            if(stage==0&&it==0)first=before;last=before;
            bool ok=false;double rate=1./max(1.,m.alpha*maxTask+K);
            for(int back=0;back<14&&elapsed()<deadline;back++,rate*=.5) {
                auto next=theta;for(int b=0;b<K;b++)for(int j=0;j<3;j++)next[b][j]-=rate*g[b][j];
                project(next);double f=m.eval(next,op,tau,nullptr,deadline);
                if(f<before-1e-12){theta.swap(next);last=f;accepted++;ok=true;break;}
            }
            if(!ok)break;
        }
    }
    bool valid=sep>1e-20;
    for(int a=0;a<K;a++)for(int b=0;b<K;b++)if(a!=b&&dot(theta[a],m.c.office[a])<dot(theta[b],m.c.office[a])+margin*.5)valid=false;
    vector<int> cell(m.c.n,-1);
    vector<int> fallback;if(!valid)fallback=m.c.labels(m.c.geo);
    for(int s=0;s<m.c.n;s++) {
        if(!I.servable[s])continue;
        if(!valid){cell[s]=op[fallback[s]];continue;}
        int best=0;for(int b=1;b<K;b++)if(dot(theta[b],m.c.phi[s])>dot(theta[best],m.c.phi[s]))best=b;
        if(!m.reject||dot(theta[best],m.c.phi[s])>0)cell[s]=op[best];
    }
    if(getenv("CLUSTER_TRACE"))fprintf(stderr,"soft_profit reject=%d accepted=%d initial=%.6f final=%.6f anchor=%d\n",which,accepted,first,last,(int)valid);
    return cell;
}
