from pathlib import Path
R=Path(__file__).resolve().parent;ROOT=R.parents[2];base=(ROOT/'experiments/v4_local_search/baseline/frozen_v4.cpp').read_text();s=(R/'src/candidate_padding.cpp').read_text()
a=s.index('static bool move_resplit(');b=s.index('\nstatic void recreate(',a);f=s[a:b].replace('static bool move_resplit(', 'static bool geom_resplit(').replace('double hard = 1e18)', 'double hard = 1e18, int gm = 7)').replace('    static const int gm = getenv("GEO_SPLIT") ? atoi(getenv("GEO_SPLIT")) : 0;\n','')
f=f.replace('    Sol& s = E.s;', '    if(elapsed()>=hard)return false;\n    Sol& s = E.s;',1)
f=f.replace('    auto sweep = [&](double th) {','    auto sweep = [&](double th) {\n        if(elapsed()>=hard)return;')
f=f.replace('        for (size_t k = start;; k++) {','        for (size_t k = start;; k++) {\n            if((k&127)==0 && elapsed()>=hard)return;')
a=base.index('static void polish(');b=base.index('\n// Пересчитать план навыков',a);p=base[a:b].replace('static void polish(', 'static void geom_polish(').replace('bool lock_offices = false)', 'bool lock_offices = false, int flags = 7)')
p=p.replace('move_resplit(E, G0, rng,', 'geom_resplit(E, G0, rng,').replace('I.ns > 1500 ? pend + 1.0 : 1e18)', 'pend, flags)')
header='''// Geometry lab: independent monotone tail; include after existing improve/boundary/exact helpers.
// Original move_resplit/polish are unchanged; flags=7 counts+expanded pool,15 also A0 negative padding.
// All function deadlines are absolute elapsed(). Caller must supply only its available budget.
'''+f+'\n'+p+'''
static void geom_finish(const Inst&I,double limit){
 int flags=getenv("GEOM_TAIL")?atoi(getenv("GEOM_TAIL")):0;
 if(!flags)return;
 double end=limit-max(.25,.002*limit);
 if(elapsed()>=end||g_best.load()<=0)return;
 double requested=getenv("GEOM_SECONDS")?max(0.,atof(getenv("GEOM_SECONDS"))):1.;
 end=min(end,elapsed()+requested);
 vector<int>a;vector<char>op;{lock_guard<mutex>lk(g_best_mx);a=g_best_asg;op=g_best_open;}
 if(a.empty())return;
 Sol s;s.init(I);s.load_state(a,op);g_wdfs_deadline=end;
 uint64_t seed=getenv("SEED")?strtoull(getenv("SEED"),nullptr,10):0;
 mt19937_64 rng(seed^0x63E0F17ULL);double before=g_best.load(),start=elapsed();
 geom_polish(s,rng,end,end,false,flags);
 fprintf(stderr,"geom_tail flags=%d before=%.12f after=%.12f seconds=%.6f\\n",flags,before,g_best.load(),elapsed()-start);
}
'''
(R/'src/geometry_tail.h').write_text(header)
