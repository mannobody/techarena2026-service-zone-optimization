// Exact alpha=0 selection within fixed convex territories and fixed staff teams.
// Sites inside those hulls can be added without expanding any footprint.
static bool cluster_territory_select(Sol& s,double deadline) {
    const Inst&I=*s.I;if(I.alpha!=0.||elapsed()>=deadline)return false;
    vector<int> staff;if(!s.greedy_workers(&staff))return false;
    vector<vector<char>> have(I.no,vector<char>(I.nsk,0));
    for(int w=0;w<I.nw;w++)if(staff[w]>=0)for(int k=0;k<I.nsk;k++)have[staff[w]][k]|=I.wmask[w][k];
    vector<vector<int>> pool(I.no);vector<vector<double>> prefix(I.no);vector<int> positive(I.no,0),cap(I.no,0);
    for(int x=0;x<I.ns;x++) {
        if((x&127)==0&&elapsed()>=deadline)return false;
        if(!I.servable[x])continue;int o=s.asg[x];
        if(o<0&&s.cov[x])for(int p=0;p<I.no;p++)if(s.isopen[p]&&s.size_[p]>0&&s.incov[(size_t)p*s.np+x]){o=p;break;}
        if(o<0)continue;bool ok=true;for(int k:I.skillset[x])if(!have[o][k]){ok=false;break;}
        if(ok)pool[o].push_back(x);
    }
    int largest=0;
    for(int o=0;o<I.no;o++) {
        auto&v=pool[o];sort(v.begin(),v.end(),[&](int a,int b){return I.pr(o,a)>I.pr(o,b);});
        cap[o]=min((int)v.size(),I.maxsize[o]);prefix[o].assign(cap[o]+1,0.);
        for(int j=0;j<cap[o];j++){prefix[o][j+1]=prefix[o][j]+I.pr(o,v[j]);positive[o]+=I.pr(o,v[j])>0.;}
        largest=max(largest,cap[o]);
    }
    double before=s.objective(),best=before;vector<int> chosen(I.no,0),trial(I.no,0);
    for(int lo=1;lo<=largest;lo++) {
        if((lo&31)==0&&elapsed()>=deadline)return false;
        double score=0.;fill(trial.begin(),trial.end(),0);
        for(int o=0;o<I.no;o++)if(cap[o]>=lo) {
            int hi=(int)min((long long)cap[o],lo+I.A),n=max(lo,min(hi,positive[o]));
            double value=prefix[o][n]-I.cost[o];if(value>0.){trial[o]=n;score+=value;}
        }
        if(score>best+1e-9){best=score;chosen=trial;}
    }
    if(best<=before+1e-9||elapsed()>=deadline)return false;
    vector<int>a(I.ns,-1);vector<char>open(I.no,0);
    for(int o=0;o<I.no;o++)if(chosen[o]) {
        open[o]=1;for(int j=0;j<chosen[o];j++)a[pool[o][j]]=o;
    }
    s.load_state(a,open);s.recompute_psum();return true;
}
