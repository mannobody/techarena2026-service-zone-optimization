from pathlib import Path
import json,time
lab=Path(__file__).resolve().parent
s=(lab/'src/escape_geometry_kick.h').read_text().replace('mode>5','mode>6').replace('if(mode!=1&&mode!=3&&mode!=5)return changed;','if(mode!=1&&mode!=3&&mode!=5&&mode!=6)return changed;')
a=s.index('        if(mode==5){');b=s.index('        // Count-compatible',a)
s=s[:a]+'''        if(mode==5||mode==6){
            GeometryStats gs; bool ok=true;
            if(mode==5){mt19937_64 kick_rng=rng;ok=geometry_perturb(s,kick_rng,min(episode_end,t+.35*episode),2,gs);}
            bool retained=ok&&s.objective_fast()>=best-loss_cap;
            if(!retained){restore(E,G,cur);failed_kicks++;}
            E.jr.clear();E.clear_ban();cur=G.val();hash=state_hash();
            recovery_seconds+=elapsed()-t;observe();
            if(s.objective_fast()>g_best.load(memory_order_relaxed)+1e-9)offer(I,s);
            // A failed proposal is rolled back, but gets the same bounded repair
            // as mode6. The control differs only by omission of geometry proposal.
            double repair_start=elapsed();long calls=boundary_stats.calls;
            if(elapsed()<episode_end)boundary_move(s,rng,min(episode_end,elapsed()+.04),1,1,24);
            s.recompute_psum();E.jr.clear();E.clear_ban();cur=G.val();hash=state_hash();
            observe();if(s.objective_fast()>g_best.load(memory_order_relaxed)+1e-9)offer(I,s);
            fprintf(stderr,"GEOBOUND mode=%d raw_success=%d retained=%d attempts=%ld accepted=%ld geometry_reject=%ld worker_reject=%ld loss_reject=%ld moved=%ld freed_points=%ld boundary_calls=%ld repair_seconds=%.9f total_seconds=%.9f\\n",mode,(int)ok,(int)retained,gs.attempts,gs.accepted,gs.geometry_reject,gs.worker_reject,gs.loss_reject,gs.moved,gs.freed_points,boundary_stats.calls-calls,elapsed()-repair_start,elapsed()-t);
            return true;
        }
''' +s[b:]
(lab/'src/escape_geometry_boundary.h').write_text(s)
s=(lab/'src/geometry_kick_v4.cpp').read_text().replace('#include "escape_geometry_kick.h"','#include "escape_geometry_boundary.h"')
old='            if (escape.tick(E,Gd,rng,cur,now)) wsig=~0ULL;';assert s.count(old)==1
s=s.replace(old,'            if (escape.tick(E,Gd,rng,cur,now)) { wsig=~0ULL; now=elapsed(); if(now>=tloop) break; }')
(lab/'src/geometry_boundary_v4.cpp').write_text(s)
s=(lab/'src/post_geometry_kick.cpp').read_text().replace('#include "geometry_kick_v4.cpp"','#include "geometry_boundary_v4.cpp"')
(lab/'src/post_geometry_boundary.cpp').write_text(s)
(lab/'GEOMETRY_BOUNDARY_DESIGN.json').write_text(json.dumps({'registered':time.time(),'change':'Final additional prototype: frozen V1 geometry support kick then single native boundary(q24, max .04s within same episode_end), observe/offer before rollback. Mode6 omits kick and performs the identical bounded boundary repair under the same plateau and best retention policy. Failed kicks restore best then still receive the same repair. Refresh elapsed after tick. No native polish, late acceptance, tabu or tail.','modes':{'geometry_boundary':5,'boundary_only':6,'retain':4,'off':0},'default':0,'cpu_pairs':[[14,15],[18,19]],'seconds':4,'seeds':[2701,2702],'cases':['anti','tightA','alphabig','multiskill','huge','cluster'],'prior_sources_unchanged':True,'polish_prototype':'Superseded before freeze/benchmark; compile preserved as unbenchmarked','soft_deadline_limitation':'boundary setup/verification still uninterruptible; process wall checked; no extra budget'},indent=2))
