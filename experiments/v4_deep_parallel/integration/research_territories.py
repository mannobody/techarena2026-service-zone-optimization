"""Run only after root's timed mature series completes; reserve CPU16..21."""
import concurrent.futures, itertools, json, os, random, subprocess, sys, time
from pathlib import Path
from territory_model import build, solve, score

ROOT=Path(__file__).resolve().parents[3]; R=Path(__file__).resolve().parent

def oracle():
    dest=R/'logs/territory_oracle';dest.mkdir(exist_ok=False)
    rows=[]
    for seed in range(16):
        rng=random.Random(741000+seed)
        data={'sites':[{'x':(i%3+1)+(10 if i>=3 else 0),'y':0,
            'reward':rng.randint(1,30),'tasks':rng.choice([[],[0],[1],[0,1],[0,0,1]])} for i in range(6)],
            'offices':[{'x':0,'y':0,'cost':2,'maxSize':2+seed%2},
                       {'x':10,'y':0,'cost':3,'maxSize':3}],
            'workers':[[0,1],[0,1],[0],[1]],
            'distances':[[rng.randrange(1,10) for i in range(6)] for o in range(2)],
            'maxDifference':seed%3,'balanceCoefficient':[0,1,10,100][seed%4]}
        if seed%5==0:data['sites'][1]['x']=data['sites'][0]['x']
        inc=[{'officeId':0,'sites':[0,2],'workers':[0]},
             {'officeId':1,'sites':[3,5],'workers':[1]}]
        assert not isinstance(score(data,inc),str)
        L,meta=build(data,inc);ops,profiles,y,x,u,pools=meta
        choices=[[-1]+[o for o in ops if s in pools[o]] for s in range(6)]
        best=0.;fixed=-float('inf')
        for asg in itertools.product(*choices):
            mem={o:[s for s,q in enumerate(asg) if q==o] for o in ops}
            active=[o for o in ops if mem[o]]
            for ws in itertools.product([-1]+active,repeat=len(data['workers'])):
                sol=[{'officeId':o,'sites':mem[o],'workers':[w for w,q in enumerate(ws) if q==o]} for o in active]
                val=score(data,sol)
                if not isinstance(val,str):
                    best=max(best,val)
                    if active==ops:fixed=max(fixed,val)
                    break
        for backend in ['highs','scip']:
            result=solve(data,inc,10,backend)
            got=score(data,result['solution'])
            ok=result['optimal_in_restricted_family'] and abs(got-best)<1e-6
            relaxed=solve(data,inc,10,backend,True)
            bound=relaxed['fixed_offices_relaxation_bound']
            ok=ok and bound is not None and bound>=fixed-1e-6
            row={'seed':seed,'backend':backend,'expected':best,'actual':got,
                 'fixed_offices_brute':fixed,'conditional_lp_bound':bound,'ok':ok}
            rows.append(row);(dest/'results.json').write_text(json.dumps(rows,indent=2))
            assert ok,row
        (dest/f'case{seed}.json').write_text(json.dumps({'instance':data,'incumbent':inc}))
    print('territory oracle PASS',len(rows),flush=True)

def case_run(case, affinity):
    base=R/'logs/mature_v4_280'
    inp=R/'inputs'/f'{case}.json';inc=base/f'{case}_1301_v4.solution.json'
    dest=R/'logs/territory_mature';dest.mkdir(exist_ok=True)
    for backend,relaxed,seconds in [('highs',True,60),('highs',False,45),('scip',False,45)]:
        output=dest/f'{case}_{backend}_{"lp" if relaxed else "mip"}.json'
        cmd=['taskset','-c',','.join(map(str,affinity)),sys.executable,str(R/'territory_model.py'),
             str(inp),str(inc),str(output),'--seconds',str(seconds),'--backend',backend]
        if relaxed:cmd.append('--relaxed')
        with output.with_suffix('.stderr').open('w') as err:
            result=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=err,text=True,timeout=seconds+180)
        output.with_suffix('.stdout').write_text(result.stdout)
        print(case,backend,relaxed,result.returncode,flush=True)
        assert result.returncode==0

if __name__=='__main__':
    while not (R/'logs/mature_v4_280/COMPLETE.json').exists():time.sleep(5)
    os.sched_setaffinity(0,{16,17})
    oracle()
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        futures=[]
        for i,cases in enumerate([['alphabig','tightA'],['anti','multiskill'],['large','huge']]):
            pair=[16+2*i,17+2*i]
            futures.append(pool.submit(lambda cs,cp:[case_run(c,cp) for c in cs],cases,pair))
        for future in futures:future.result()
