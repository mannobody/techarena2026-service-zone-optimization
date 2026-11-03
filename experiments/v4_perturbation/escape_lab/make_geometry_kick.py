from pathlib import Path
import hashlib,json,time
lab=Path(__file__).resolve().parent;root=lab.parents[2]
gp=root/'experiments/v4_perturbation/geometry_lab/src/geometry_perturb_only_v1.h'
assert hashlib.sha256(gp.read_bytes()).hexdigest()=='b1877a90fdad4ebc5fed6bd21f53784889c369e4c69bc7223543646623d504b2'
(lab/'src/geometry_perturb_only_v1.h').write_bytes(gp.read_bytes())
s=(lab/'src/escape.h').read_text().replace('mode>4','mode>5').replace('if(mode!=1&&mode!=3)return changed;','if(mode!=1&&mode!=3&&mode!=5)return changed;')
s=s.replace('        double t=elapsed();size_t mark=E.jr.size();', '''        double t=elapsed();size_t mark=E.jr.size();
        if(mode==5){
            GeometryStats gs;
            mt19937_64 kick_rng=rng;
            bool ok=geometry_perturb(s,kick_rng,min(episode_end,t+.35*episode),2,gs);
            if(!ok||s.objective_fast()<best-loss_cap){restore(E,G,cur);failed_kicks++;}
            E.jr.clear();E.clear_ban();cur=G.val();hash=state_hash();
            recovery_seconds+=elapsed()-t;observe();
            if(s.objective_fast()>g_best.load(memory_order_relaxed)+1e-9)offer(I,s);
            fprintf(stderr,"GEOKICK success=%d attempts=%ld accepted=%ld geometry_reject=%ld worker_reject=%ld loss_reject=%ld moved=%ld freed_points=%ld seconds=%.9f\\n",(int)ok,gs.attempts,gs.accepted,gs.geometry_reject,gs.worker_reject,gs.loss_reject,gs.moved,gs.freed_points,elapsed()-t);
            return true;
        }''')
(lab/'src/escape_geometry_kick.h').write_text(s)
s=(lab/'src/escape_v4.cpp').read_text().replace('#include "escape.h"','#include "geometry_perturb_only_v1.h"\n#include "escape_geometry_kick.h"')
(lab/'src/geometry_kick_v4.cpp').write_text(s)
s=(lab/'src/post_repeat_escape.cpp').read_text().replace('#include "escape_v4.cpp"','#include "geometry_kick_v4.cpp"')
(lab/'src/post_geometry_kick.cpp').write_text(s)
(lab/'GEOMETRY_KICK_DESIGN.json').write_text(json.dumps({'registered':time.time(),'mode':5,'default':0,'geometry_source':str(gp.relative_to(root)),'geometry_sha256':hashlib.sha256(gp.read_bytes()).hexdigest(),'change':'replace random-refill kick only with frozen V1 support-site geometry_perturb mode2; native acceptance, bounded plateau episode, verified local best, immediate monotone offer on gain; no support tail','quality_previous_unchanged':True,'primary_checkpoint_stage':'exact v4 final TL60 checkpoints, same as A support screen','seconds':4,'seeds':[2701,2702],'variants':['v4','off','geometry_kick'],'cpu':[14,15]},indent=2))
