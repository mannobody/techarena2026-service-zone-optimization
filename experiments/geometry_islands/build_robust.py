from pathlib import Path
import subprocess,json,hashlib
H=Path(__file__).resolve().parent
s=(H/'artifacts/index_v1.cpp').read_text();needle='// Выпуклая оболочка (монотонная цепь)';pos=s.index(needle);s=s[:pos]+(H/'src/robust.h').read_text()+'\n'+s[pos:]
s=s.replace('cr(h[k - 2], h[k - 1], p[i]) <= 0','geo_turn(h[k - 2], h[k - 1], p[i]) <= 0')
s=s.replace('void apply_cov(int o, const vector<Pt>& h)', 'void legacy_apply_cov(int o, const vector<Pt>& h)',1).replace('bool geo_ok(int s, int o, vector<Pt>& newh) const', 'bool legacy_geo_ok(int s, int o, vector<Pt>& newh) const',1)
s=s.replace('    // --- навыки',(H/'src/robust_sol.h').read_text()+'\n    // --- навыки',1)
s=s.replace('if (m == 1) in = fabs(I.P[i].x','if(g_geo_exact)in=geo_exact_covers(h,I.P[i]);\n            else if (m == 1) in = fabs(I.P[i].x',1)
p=H/'artifacts/robust_v1.cpp';assert not p.exists();p.write_text(s);subprocess.run(['g++','-O3','-std=c++17',str(p),'-o',str(p.with_suffix(''))],check=True)
b=H/'baseline/solver';g=(b/'geom.h').read_text();g=g.replace(needle,(H/'src/robust.h').read_text()+'\n'+needle).replace('cr(h[k - 2], h[k - 1], p[i]) <= 0','geo_turn(h[k - 2], h[k - 1], p[i]) <= 0')
o='#include <iostream>\n'+(b/'base.h').read_text()+'\n'+g+r'''
int main(){int mode;while(cin>>mode){if(mode==0){Pt p[3];for(auto&v:p){uint64_t x,y;cin>>x>>y;memcpy(&v.x,&x,8);memcpy(&v.y,&y,8);}printf("%d\n",geo_orientation(p[0],p[1],p[2]));}else{int n;cin>>n;vector<Pt>h(n);for(auto&v:h)cin>>v.x>>v.y;Pt q;cin>>q.x>>q.y;hull_of(h);printf("%d\n",geo_exact_covers(h,q));}}}
'''
p=H/'artifacts/robust_oracle.cpp';p.write_text(o);subprocess.run(['g++','-O3','-std=c++17',str(p),'-o',str(p.with_suffix(''))],check=True)
(H/'build_robust.json').write_text(json.dumps({str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (H/'artifacts').glob('robust*')},indent=2))
