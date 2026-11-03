from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parent;ROOT=R.parents[2]
s=(ROOT/'experiments/v4_local_search/baseline/frozen_v4.cpp').read_text()
assert hashlib.sha256(s.encode()).hexdigest()=='5b3914fa9791cb879f3232fb2876a915de83b848ad4b353b0dbf25b574998c25'
def rep(a,b):
 global s
 assert a in s,a[:80]
 s=s.replace(a,b)
# All switches default off. No draw/order changes in off mode.
pos=s.index('struct Sol {')
s=s[:pos]+'static bool lab_flag(const char* k) { const char* v=getenv(k); return v && atoi(v)>0; }\n'+s[pos:]
rep('    const Inst* I = nullptr;\n    vector<char> isopen;', '    const Inst* I = nullptr;\n    bool defer = false;\n    vector<char> dirty;\n    vector<char> isopen;')
rep('        np = I->ns + I->no;','        np = I->ns + I->no;\n        defer=false; dirty.assign(I->no,0);')
rep('    void rebuild_hull(int o) {','    void begin_defer() { if(lab_flag("LAB_BATCH")) defer=true; }\n    void end_defer() { defer=false; for(int o=0;o<I->no;o++) if(dirty[o]) {dirty[o]=0;rebuild_hull(o);} }\n    void rebuild_hull(int o) {\n        if(defer) {dirty[o]=1;return;}')
rep('        // полная пересборка\n', '        // полная пересборка\n        defer=false; fill(dirty.begin(),dirty.end(),0);\n')
rep('        while (!s.members[o].empty()) doRemove(s.members[o].back());\n        s.isopen[o] = 0;', '        bool wasdefer=s.defer; s.begin_defer();\n        while (!s.members[o].empty()) doRemove(s.members[o].back());\n        s.defer=wasdefer; s.dirty[o]=0;\n        s.isopen[o] = 0;')
rep('    void undo(size_t mark) {\n        while', '    void undo(size_t mark) {\n        s.begin_defer();\n        while')
rep('            rec = r;\n        }\n    }\n};','            rec = r;\n        }\n        s.end_defer();\n    }\n};')
rep('    for (int x : U) if (s.asg[x] >= 0) E.doRemove(x);','    s.begin_defer();\n    for (int x : U) if (s.asg[x] >= 0) E.doRemove(x);\n    s.end_defer();')
rep('        int mode = rng() % 100;\n        if (mode < 40', '        int mode = rng() % 100;\n        s.begin_defer();\n        if (mode < 40')
rep('            E.doOpen(o);\n        }\n        cnt[2][0]++;','            s.end_defer(); E.doOpen(o);\n        }\n        s.end_defer();\n        cnt[2][0]++;')
# Successful worker assignments cached by entire Boolean requirement matrix and activity.
rep('    bool greedy_workers(vector<int>* out) const {','    bool uncached_workers(vector<int>* out) const {')
point=s.index('    // --- ходы\n    void open_office')
memo='''    bool greedy_workers(vector<int>* out) const {
        if(!lab_flag("LAB_MEMO") || I->simple_workers) return uncached_workers(out);
        static thread_local unordered_map<string,vector<int>> cache;
        string key; key.reserve((size_t)I->no*(I->nsk+1));
        for(int o=0;o<I->no;o++) {key.push_back(isopen[o] && size_[o]>0);for(int k=0;k<I->nsk;k++) key.push_back(isopen[o] && size_[o]>0 && need[o][k]>0);}
        auto it=cache.find(key);if(it!=cache.end()) {if(out)*out=it->second;return true;}
        vector<int> cert;if(!uncached_workers(&cert))return false;
        if(cache.size()>=4096)cache.clear();cache.emplace(move(key),cert);if(out)*out=move(cert);return true;
    }

'''
s=s[:point]+memo+s[point:]
# Port ALNS scoring only; no XOVER or merged geometry code.
l=(ROOT/'solver/lns.h').read_text()
a=l.index('    // ALNS (');b=l.index('    int since_dp',a)
block=l[a:b].replace('!getenv("ALNS") || atoi(getenv("ALNS")) > 0','lab_flag("LAB_ALNS")')
rep('    int since_dp = 0;',block+'    int since_dp = 0;')
rep('        bool ch = resize_dp(s, min(tloop + 5.0, dp_deadline)', '        double tdp=elapsed();\n        bool ch = resize_dp(s, min(tloop + 5.0, dp_deadline)')
rep('        dpn++;\n    };','        dpn++;\n        if(alns) at0+=elapsed()-tdp; aprev=cur;\n    };')
a=l.index('        if (alns) {');b=l.index('        if (DBG) { double t',a)
rep('        int kind = rng() % 100;','        int kind = rng() % 100;\n'+l[a:b])
# Persistent per-origin trajectory states. Same timing and initial starts as v4.
rep('    int round = 0;\n    while (elapsed()', '''    struct Trajectory {vector<int>a;vector<char>o;double f=NEG;int visits=0;};
    vector<Trajectory> archive(cands.size());
    const bool persist=lab_flag("LAB_ARCHIVE"), wide=lab_flag("LAB_WIDE");
    int round=0, starts=0;
    while (elapsed()''')
rep('        bool fromBest = false;','        bool fromBest = false; int origin=-1;')
rep('            int r = round % max<size_t>(1, min<size_t>(rank.size(), 6));','            int r = (wide?starts:round) % max<size_t>(1, wide?rank.size():min<size_t>(rank.size(), 6));\n            starts++;')
rep('            build(combo % cands.size(), combo / cands.size(), min(ce, dp_deadline), true, skt);','''            origin=combo % cands.size();
            if(persist && !archive[origin].a.empty()) {s.init(I);s.load_state(archive[origin].a,archive[origin].o);archive[origin].visits++;}
            else build(origin, combo / cands.size(), min(ce, dp_deadline), true, skt);''')
rep('        } else lns(s, rng, ce, dp_deadline, fromBest, LAMS[tid % 4], RUINS[tid % 3]);\n    }','''        } else lns(s, rng, ce, dp_deadline, fromBest, LAMS[tid % 4], RUINS[tid % 3]);
        if(persist && origin>=0 && s.objective()>archive[origin].f && s.skills_ok()) {
            Engine e(s);if(e.size_viol(-1,-1)==0) {archive[origin].a=s.asg;archive[origin].o=s.isopen;archive[origin].f=s.objective();}
        }
    }''')
s='#include <unordered_map>\n'+s
(R/'src/lab.cpp').write_text(s)
(R/'SOURCE.json').write_text(json.dumps({'base_sha256':hashlib.sha256((ROOT/'experiments/v4_local_search/baseline/frozen_v4.cpp').read_bytes()).hexdigest(),'candidate_sha256':hashlib.sha256(s.encode()).hexdigest(),'flags':['LAB_BATCH','LAB_ALNS','LAB_ARCHIVE','LAB_WIDE','LAB_MEMO'],'defaults':'all off'},indent=2))
