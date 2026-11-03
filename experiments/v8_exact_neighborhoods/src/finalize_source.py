"""Freeze a conservative runtime before new inputs are generated or examined.
Selected by structural counterexamples + completed development, not holdout.
Full B&B/packets remain explicit options: fixed-state results do not justify
spending a tail by default. Keep v8 support escape OFF, as its prior holdout failed.
"""
import hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];out=R/'artifacts/final';out.mkdir(exist_ok=False)
s=(R/'artifacts/candidate_v3/main.cpp').read_text()
def change(a,b):
    global s
    assert a in s,a;s=s.replace(a,b,1)
change('#include <unistd.h>','#include <unistd.h>\n#include <sys/time.h>')
change('static const int m=getenv("XN_FILL")?atoi(getenv("XN_FILL")):0;',
       'static const int m=getenv("XN_FILL")?atoi(getenv("XN_FILL")):2;')
change('static const bool xn_exact_worker=getenv("XN_WORKER")&&atoi(getenv("XN_WORKER"));',
       'static const bool xn_exact_worker=!getenv("XN_WORKER")||atoi(getenv("XN_WORKER"));')
change('if(!getenv("XN_SIG_FIX")||atoi(getenv("XN_SIG_FIX")))sig_open(o);',
       'if(getenv("XN_SIG_FIX")&&atoi(getenv("XN_SIG_FIX")))sig_open(o);')
change('int mode=getenv("XN_MODE")?atoi(getenv("XN_MODE")):3;',
       'int mode=getenv("XN_MODE")?atoi(getenv("XN_MODE")):0;')
change('mode(getenv("ESCAPE_MODE")?atoi(getenv("ESCAPE_MODE")):5)',
       'mode(getenv("ESCAPE_MODE")?atoi(getenv("ESCAPE_MODE")):0)')
change('if((!getenv("XN_MODE")||atoi(getenv("XN_MODE"))>0)&&I.ns<=10&&I.no<=5)',
       'if((!getenv("XN_TINY")||atoi(getenv("XN_TINY"))>0)&&I.ns<=10&&I.no<=5)')
change('alarm((unsigned)max(5.0, limit + 14));', '''// Deadline includes parsing, all recovery, validation, and serialization.
    // Existing signal handler publishes the separately retained valid incumbent.
    itimerval timer{};double remaining=max(.001,limit-elapsed()-.03);
    timer.it_value.tv_sec=(long)remaining;
    timer.it_value.tv_usec=(long)((remaining-timer.it_value.tv_sec)*1e6);
    setitimer(ITIMER_REAL,&timer,nullptr);''')
(out/'main.cpp').write_text(s);(out/'Makefile').write_text((R/'artifacts/Makefile').read_text())
(out/'SELECTION.json').write_text(json.dumps(dict(
    source_sha256=hashlib.sha256(s.encode()).hexdigest(),
    defaults=dict(TL=280,NT=2,ESCAPE_MODE=0,XN_FILL=2,XN_WORKER=1,XN_TINY=1,XN_MODE=0,XN_SIG_FIX=0),
    rationale='greedy fallback + raw-negative penalty improvement + deadline-bounded worker completeness; structural tails not promoted after mature checkpoint screen; v8 escape failed previous independent evaluation',
    status='experimental, independent quality validation pending; no claim of superiority',
    rejected_defaults=['q12 exact tail: loses mature boundary budget','whole-zone templates: conditional barrier win only','support kick: previous independent stability failed','signature fix: canonical state correctness but no quality attribution']),indent=2))
print(hashlib.sha256(s.encode()).hexdigest())
