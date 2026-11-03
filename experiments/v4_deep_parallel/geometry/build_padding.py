from pathlib import Path
R=Path(__file__).resolve().parent;s=(R/'src/candidate.cpp').read_text();a=s.index('static bool move_resplit(');b=s.index('\nstatic void recreate(',a);f=s[a:b]
f=f.replace('    auto cap=', '    bool pad=false;\n    if((gm&8)&&I.A==0)for(int o:op)if(o!=o1&&o!=o2&&s.size_[o]>0)pad=true;\n    auto cap=')
f=f.replace('(I.pr(o1,x)>0 || I.pr(o2,x)>0)', '(pad || I.pr(o1,x)>0 || I.pr(o2,x)>0)')
f=f.replace('if (v > 0 && fits', 'if ((pad || v > 0) && fits').replace('if (vh > 0 && fits','if ((pad || vh > 0) && fits').replace('if (vl > 0 && fits','if ((pad || vl > 0) && fits').replace('if (v <= 0 || !fits(x, o))','if ((!pad && v <= 0) || !fits(x, o))')
s=s[:a]+f+s[b:];(R/'src/candidate_padding.cpp').write_text(s)
p=(R/'src/post.cpp').read_text().replace('#include "candidate.cpp"','#include "candidate_padding.cpp"').replace('(mode==8?4:mode==9?5:7)','(mode==8?4:mode==9?5:mode==11?13:mode==12?15:7)');(R/'src/post_padding.cpp').write_text(p)
