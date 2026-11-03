#include <functional>
#define main native_solver_main
#ifndef NATIVE_SOURCE
#define NATIVE_SOURCE "artifacts/warm.cpp"
#endif
#include NATIVE_SOURCE
#undef main

// Independent exhaustive oracle: every worker may stay idle or join one office.
static bool oracle(const Inst& i,const Sol& s,int w,vector<unsigned>& have) {
    bool covered=true;
    for(int o=0;o<i.no;o++)for(int k=0;k<i.nsk;k++)
        if(s.need[o][k]&&!(have[o]&(1u<<k)))covered=false;
    if(covered)return true;
    if(w==i.nw)return false;
    unsigned mask=0;for(int k=0;k<i.nsk;k++)if(i.wmask[w][k])mask|=1u<<k;
    for(int o=0;o<i.no;o++) {
        unsigned old=have[o];have[o]|=mask;
        if(have[o]!=old&&oracle(i,s,w+1,have))return true;
        have[o]=old;
    }
    return oracle(i,s,w+1,have);
}

int main() {
    setenv("WORKER_DFS","1",1);g_wdfs_deadline=1e100;
    long tests=0,legacy_misses=0,fallback_misses=0;
    auto check=[&](int no,int nsk,const vector<int>& workers,const vector<int>& needs) {
        Inst i;i.no=no;i.nsk=nsk;i.nw=workers.size();
        i.wmask.assign(i.nw,vector<char>(nsk));i.wskills.resize(i.nw);
        for(int w=0;w<i.nw;w++)for(int k=0;k<nsk;k++)if(workers[w]&(1<<k)) {
            i.wmask[w][k]=1;i.wskills[w].push_back(k);
            if(w&1)i.wskills[w].push_back(k); // duplicate input skill entries
        }
        Sol s;s.init(i);
        for(int o=0;o<no;o++) {
            s.isopen[o]=1;s.size_[o]=1;
            for(int k=0;k<nsk;k++)s.need[o][k]=(needs[o]>>k)&1;
        }
        vector<unsigned> have(no);bool exact=oracle(i,s,0,have);
        vector<int> result;bool old=s.legacy_workers(nullptr),now=s.greedy_workers(&result);
        if(old&&!exact)throw runtime_error("legacy false positive");
        if(now&&!exact)throw runtime_error("fallback false positive");
        if(now) {
            vector<int> cov(no,0);
            if((int)result.size()!=i.nw)throw runtime_error("worker output size");
            for(int w=0;w<i.nw;w++)if(result[w]>=0)cov.at(result[w])|=workers[w];
            for(int o=0;o<no;o++)if((cov[o]&needs[o])!=needs[o])throw runtime_error("invalid worker output");
        }
        tests++;legacy_misses+=exact&&!old;fallback_misses+=exact&&!now;
    };
    // Every multiset of <=4 worker skill masks over three skills, two offices.
    vector<int> workers;
    function<void(int,int)> enumerate=[&](int remaining,int low) {
        if(!remaining) {
            for(int a=0;a<8;a++)for(int b=0;b<8;b++)check(2,3,workers,{a,b});
            return;
        }
        for(int m=low;m<8;m++){workers.push_back(m);enumerate(remaining-1,m);workers.pop_back();}
    };
    for(int nw=0;nw<=4;nw++)enumerate(nw,0);
    mt19937 rng(918273);
    for(int t=0;t<3000;t++) {
        int no=1+rng()%3,nsk=1+rng()%6,nw=rng()%9;
        vector<int> w(nw),need(no);
        for(int& m:w)m=rng()%(1<<nsk);
        for(int& m:need)m=rng()%(1<<nsk);
        check(no,nsk,w,need);
    }
    { // The production representation must also work beyond machine-word masks.
        Inst i;i.no=2;i.nsk=80;i.nw=2;
        i.wmask.assign(2,vector<char>(80));i.wskills={{0,79},{0}};
        i.wmask[0][0]=i.wmask[0][79]=i.wmask[1][0]=1;
        Sol s;s.init(i);s.isopen={1,1};s.size_={1,1};s.need[0][0]=s.need[1][79]=1;
        vector<int> result;
        if(s.legacy_workers(nullptr)||!s.greedy_workers(&result)||result!=vector<int>({1,0}))
            throw runtime_error("80-skill trap");
        tests++;legacy_misses++;
    }
    printf("{\"tests\":%ld,\"legacy_false_negatives\":%ld,\"fallback_false_negatives\":%ld,\"fallback_calls\":%ld,\"fallback_successes\":%ld,\"nodes\":%ld}\n",
        tests,legacy_misses,fallback_misses,g_wdfs_calls.load(),g_wdfs_success.load(),g_wdfs_nodes.load());
    return fallback_misses?1:0;
}
