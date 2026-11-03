from pathlib import Path
import json,time
lab=Path(__file__).resolve().parent
s=(lab/'src/escape_geometry_kick.h').read_text()
s=s.replace('            if(!ok||s.objective_fast()<best-loss_cap){restore(E,G,cur);failed_kicks++;}', '            bool retained=ok&&s.objective_fast()>=best-loss_cap;\n            if(!retained){restore(E,G,cur);failed_kicks++;}')
s=s.replace('            fprintf(stderr,"GEOKICK success=%d', '''            double polish_start=elapsed();
            if(retained&&elapsed()<episode_end)polish(s,rng,episode_end,episode_end,true);
            s.recompute_psum();E.jr.clear();E.clear_ban();cur=G.val();hash=state_hash();
            observe();if(s.objective_fast()>g_best.load(memory_order_relaxed)+1e-9)offer(I,s);
            fprintf(stderr,"GEOKICK_POLISH retained=%d seconds=%.9f episode_remaining=%.9f\\n",(int)retained,elapsed()-polish_start,episode_end-elapsed());
            fprintf(stderr,"GEOKICK success=%d''')
(lab/'src/escape_geometry_kick_polish.h').write_text(s)
s=(lab/'src/geometry_kick_v4.cpp').read_text().replace('#include "escape_geometry_kick.h"','#include "escape_geometry_kick_polish.h"')
old='            if (escape.tick(E,Gd,rng,cur,now)) wsig=~0ULL;';assert s.count(old)==1
s=s.replace(old,'            if (escape.tick(E,Gd,rng,cur,now)) { wsig=~0ULL; now=elapsed(); if(now>=tloop) break; }')
(lab/'src/geometry_kick_polish_v4.cpp').write_text(s)
s=(lab/'src/post_geometry_kick.cpp').read_text().replace('#include "geometry_kick_v4.cpp"','#include "geometry_kick_polish_v4.cpp"')
(lab/'src/post_geometry_kick_polish.cpp').write_text(s)
(lab/'GEOMETRY_KICK_POLISH_DESIGN.json').write_text(json.dumps({'registered':time.time(),'change':'After retained V1 support kick, run native polish with the same absolute episode_end before local-best rollback; no extra time; refresh elapsed after tick to avoid one additional heavy move. Independent kick RNG unchanged. No boundary, late acceptance, tabu, support tail or parameter tuning.','mode':5,'default':0,'cpu':[18,19],'seconds':4,'seeds':[2701,2702],'cases':['anti','tightA','alphabig','multiskill','huge','cluster'],'variants':['v4','off','retain','geometry_kick_polish'],'prior_sources_unchanged':True,'soft_deadline_limitation':'native polish/resplit/verification may overrun individual soft deadline; actual process wall checked'},indent=2))
