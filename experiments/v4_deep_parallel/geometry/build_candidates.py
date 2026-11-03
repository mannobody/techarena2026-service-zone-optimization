from pathlib import Path
R=Path(__file__).resolve().parent;ROOT=R.parents[2]
s=(ROOT/'experiments/v4_local_search/baseline/frozen_v4.cpp').read_text()
a=s.index('static bool move_resplit(');b=s.index('\nstatic void recreate(',a);f=s[a:b]
f=f.replace('    vector<int> op;','    static const int gm = getenv("GEO_SPLIT") ? atoi(getenv("GEO_SPLIT")) : 0;\n    vector<int> op;',1)
f=f.replace('    // кандидаты:', '''    int cap1=I.maxsize[o1],cap2=I.maxsize[o2];
    if(gm&1){
        int othermin=INT_MAX;
        for(int o:op)if(o!=o1&&o!=o2&&s.size_[o]>0)othermin=min(othermin,s.size_[o]);
        if(othermin<INT_MAX){
            long long lim=(long long)othermin+I.A;
            cap1=(int)min((long long)cap1,lim);cap2=(int)min((long long)cap2,lim);
        }
    }
    auto cap=[&](int o){return o==o1?cap1:cap2;};
    // кандидаты:''')
f=f.replace('        for (int o : I.cand[x]) if (s.isopen[o]) { if (o == o1 || o == o2) U.push_back(x); break; }','''        if(gm&2){
            // Other hulls stay fixed. A site covered by a third zone cannot join this pair.
            bool blocked=false;
            if(s.cov[x])for(int o:op)if(o!=o1&&o!=o2&&geo_exact_covers(s.hull[o],I.P[x])){blocked=true;break;}
            if(!blocked && (I.pr(o1,x)>0 || I.pr(o2,x)>0))U.push_back(x);
        }else for (int o : I.cand[x]) if (s.isopen[o]) { if (o == o1 || o == o2) U.push_back(x); break; }''')
f=f.replace('L.init(I.maxsize[lo_off], I.ntask);','L.init(cap(lo_off), I.ntask);').replace('H.init(I.maxsize[hi_off], I.ntask);','H.init(cap(hi_off), I.ntask);')
f=f.replace('I.maxsize[bLo]', 'cap(bLo)').replace('I.maxsize[bHi]', 'cap(bHi)')
f=f.replace('            int szL = L.size(), szH = H.size();', """            if(gm&4){
                int availableL=L.top.size()+L.rest.size(),availableH=H.top.size()+H.rest.size();
                L.m=(int)min((long long)cap(lo_off),(long long)min(availableH,cap(hi_off))+I.A);
                H.m=(int)min((long long)cap(hi_off),(long long)min(availableL,cap(lo_off))+I.A);
                L.balance();H.balance();
            }
            int szL = L.size(), szH = H.size();""")
# Final reconstruction must use the chosen dynamic capacities, not static caps.
f=f.replace('int bLo = o1, bHi = o2;', 'int bLo = o1, bHi = o2, bestCapLo=cap1, bestCapHi=cap2;')
f=f.replace('bLo = lo_off; bHi = hi_off;', 'bLo = lo_off; bHi = hi_off; bestCapLo=L.size(); bestCapHi=H.size();')
f=f.replace('if ((int)sl.size() > cap(bLo)) sl.resize(cap(bLo));', 'if ((int)sl.size() > bestCapLo) sl.resize(bestCapLo);')
f=f.replace('if ((int)sh.size() > cap(bHi)) sh.resize(cap(bHi));', 'if ((int)sh.size() > bestCapHi) sh.resize(bestCapHi);')
s=s[:a]+f+s[b:]
(R/'src/candidate.cpp').write_text(s)
# Standalone checkpoint driver: never packaged.
post=(ROOT/'experiments/v4_local_search/src/post.cpp').read_text()
post=post.replace('#include "../../../solver/solve.cpp"','#include "candidate.cpp"\n#include "structural.h"')
post=post.replace('if(!search_valid(s))return 5;','vector<int>wof;double verified;if(!s.greedy_workers(&wof)||!verify(I,s.asg,s.isopen,wof,&verified))return 5;')
start=post.index('    if(mode==0)');end=post.index('    offer(I,s);',start)
post=post[:start]+'''    if(mode<=3||mode>=8){int flags=mode<=3?mode:(mode==8?4:mode==9?5:7);setenv("GEO_SPLIT",to_string(flags).c_str(),1);polish(s,rng,end,end,false);}
    else structural_search(s,rng,end,mode);
'''+post[end:]
(R/'src/post.cpp').write_text(post)
