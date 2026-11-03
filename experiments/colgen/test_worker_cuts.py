"""Check cheap worker-cover cuts against exact IP, full LP and enumerated CG."""
import json
from pathlib import Path
import time

from model import Instance,Master,cg_enumerated
from test_models import tiny,witnesses


if __name__=='__main__':
    rows=[]; start=time.perf_counter()
    for j,mode in enumerate(['normal','multiskill','missing','A0','freeA','alpha0','alpha_huge',
                             'zero_capacity','duplicates','collinear','scale','anti']):
        I=Instance(tiny(12000+j,mode=mode)); cols=I.enumerate_columns()
        base=Master(I).solve(cols); M=Master(I,worker_cuts=True)
        cut=M.solve(cols); cg=cg_enumerated(M,cols)
        ip=M.solve(cols,integer=True)
        truth=Master(I).solve(cols,integer=True)['value']
        assert abs(ip['value']-truth)<1e-5*max(1.,abs(truth))
        assert cut['value']<=base['value']+1e-5*max(1.,abs(truth))
        assert cg['converged'] and abs(cg['result']['value']-cut['value'])<1e-5*max(1.,abs(truth))
        assert all(r['cheap_certificate']>=cut['value']-1e-5*max(1.,abs(truth)) for r in cg['trace'])
        r=dict(mode=mode,seed=12000+j,base_lp=base['value'],worker_cover_lp=cut['value'],exact_ip=truth)
        rows.append(r); print(json.dumps(r),flush=True)
    w=witnesses()
    (Path(__file__).parent/'logs/worker_cuts.json').write_text(json.dumps(dict(results=rows,witnesses=w,seconds=time.perf_counter()-start),indent=2))
    (Path(__file__).parent/'logs/witnesses_final.json').write_text(json.dumps(w,indent=2))
