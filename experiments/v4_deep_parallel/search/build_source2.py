from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parent;ROOT=R.parents[2]
s=(R/'src/lab.cpp').read_text()
s=s.replace('    for (auto& e : g_elite) if (fabs(e.f - f) <= 1e-9 * max(1.0, fabs(f))) return;', '    bool niches=lab_flag("LAB_NICHES");\n    for (auto& e : g_elite) if (fabs(e.f - f) <= 1e-9 * max(1.0, fabs(f)) && (!niches || e.open==op)) return;')
s=s.replace('    if (g_elite.size() > 6) g_elite.resize(6);','''    if(niches) {
        map<vector<char>,int> count;vector<Elite> next;
        for(auto& e:g_elite)if(count[e.open]++<2) {next.push_back(move(e));if(next.size()==12)break;}
        g_elite=move(next);
    } else if (g_elite.size() > 6) g_elite.resize(6);''')
s=s.replace('    asg = g_elite[i].asg;', '    if(lab_flag("LAB_NICHES") && rng()%4==0)i=rng()%g_elite.size();\n    asg = g_elite[i].asg;')
l=(ROOT/'solver/moves.h').read_text();a=l.index('static bool ruin_crossover(');b=l.index('// Count-preserving composite',a)
x=l[a:b]
x=x.replace('        pts_in_hull(I, h, inside);','''        inside.clear();
        double x0=1e300,x1=-1e300,y0=1e300,y1=-1e300;
        for(auto p:h){x0=min(x0,p.x);x1=max(x1,p.x);y0=min(y0,p.y);y1=max(y1,p.y);}
        for(int p:g_geo_grid.query(I,x0,x1,y0,y1))if(geo_exact_covers(h,I.P[p]))inside.push_back(p);''')
x=x.replace('    Sol& s = E.s;', '    if(!g_geo_exact)return false;\n    Sol& s = E.s;')
pos=s.index('// lns.h:');s=s[:pos]+x+s[pos:]
s=s.replace('        int mode = rng() % 100;\n        s.begin_defer();\n        if (mode < 40', '''        int mode = rng() % 100;
        if(lab_flag("LAB_XOVER") && mode<12 && !lock_offices) {
            if(!ruin_crossover(E,rng)) {E.undo(mark);continue;}mode=-1;
        }
        s.begin_defer();
        if(mode<0) {}
        else if (mode < 40''')
(R/'src/lab2.cpp').write_text(s)
(R/'SOURCE2.json').write_text(json.dumps({'parent_source':hashlib.sha256((R/'src/lab.cpp').read_bytes()).hexdigest(),'sha256':hashlib.sha256(s.encode()).hexdigest(),'new_flags':['LAB_XOVER','LAB_NICHES'],'defaults':'off'},indent=2))
