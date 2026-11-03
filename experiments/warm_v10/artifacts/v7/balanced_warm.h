// Capacity/load-directed power-cell geometry. A proposal only; final fitness is feasible.
static double gw_balance_cells(const Inst&I,const Fast&F,const vector<int>&op,
        vector<double>&h,const vector<Pt>&G,vector<int>&labels,double end) {
    const int K=op.size();F.cells(op,h,G,labels);
    if(K<=1||elapsed()>=end)return 0.;
    vector<int>index(I.no,-1);int mincap=INT_MAX;
    for(int b=0;b<K;b++){index[op[b]]=b;mincap=min(mincap,I.maxsize[op[b]]);}
    vector<double>count(K),load(K),target(K),curCount,curLoad;
    double sumProfit=0.,total=0.,tasks=0.;
    auto masses=[&](const vector<int>&cell,vector<double>&cnt,vector<double>&ld){
        cnt.assign(K,0.);ld.assign(K,0.);vector<char>allow;
        plan_skills(I,op,cell,allow);
        for(int x=0;x<I.ns;x++) {
            int o=cell[x];if(o<0||!I.servable[x]||I.pr(o,x)<=0)continue;
            int b=index[o];if(b<0)continue;bool ok=true;
            for(int k:I.skillset[x])if(!allow[(size_t)b*I.nsk+k]){ok=false;break;}
            if(ok){cnt[b]++;ld[b]+=I.ntask[x];}
        }
    };
    // cells() returns local indices; constructors/skill planning use office IDs.
    for(int&x:labels)x=op[x];masses(labels,count,load);
    for(int x=0;x<I.ns;x++)if(I.servable[x]&&I.pr(labels[x],x)>0){sumProfit+=I.pr(labels[x],x);total++;tasks+=I.ntask[x];}
    if(total<=0)return 0.;
    double meanCount=total/K,meanLoad=tasks/K;
    double beta=max(0.,I.alpha)*(tasks/max(1.,total));
    beta=beta/(max(1e-12,sumProfit/total)+beta);
    for(int b=0;b<K;b++)target[b]=max(1.,min({(double)I.maxsize[op[b]],(double)mincap+(double)I.A,meanCount}));
    auto loss=[&](const vector<double>&cnt,const vector<double>&ld){
        double v=0.;for(int b=0;b<K;b++){
            double c=(cnt[b]-target[b])/max(1.,target[b]);
            double l=(ld[b]-meanLoad)/max(1.,meanLoad);v+=c*c+beta*l*l;
        }return v;
    };
    double current=loss(count,load),best=current,step=max(F.scale2,.05*I.ext*I.ext);
    vector<double>working=h,bestH=h,trial=h,gradient(K);vector<int>cell,trialLabels;
    for(int iter=0;iter<40&&elapsed()<end&&best>1e-10;iter++) {
        for(int b=0;b<K;b++)gradient[b]=(target[b]-count[b])/max(1.,target[b])+beta*(meanLoad-load[b])/max(1.,meanLoad);
        bool accepted=false;
        for(int bt=0;bt<10&&elapsed()<end;bt++) {
            trial=working;for(int b=0;b<K;b++)trial[op[b]]+=step*gradient[b];
            if(!F.offices_in_own_cell(op,trial,G)){step*=.5;continue;}
            F.cells(op,trial,G,cell);trialLabels.resize(I.ns);
            for(int x=0;x<I.ns;x++)trialLabels[x]=op[cell[x]];
            masses(trialLabels,curCount,curLoad);double value=loss(curCount,curLoad);
            bool unchanged=trialLabels==labels;
            if(value<current-1e-10||unchanged) {
                working=trial;labels=trialLabels;count=curCount;load=curLoad;current=value;accepted=true;
                if(value<best-1e-10){best=value;bestH=working;}
                step*=unchanged?1.3:1.1;break;
            }
            step*=.5;
        }
        if(!accepted||step<1e-12*max(1.,F.scale2))break;
    }
    h=bestH;F.cells(op,h,G,cell);labels.resize(I.ns);
    for(int x=0;x<I.ns;x++)labels[x]=op[cell[x]];
    return best;
}
