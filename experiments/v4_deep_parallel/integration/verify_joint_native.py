import itertools,json,os,random,subprocess,sys,time
from pathlib import Path
R=Path(__file__).resolve().parent;ROOT=R.parents[2]
sys.path.insert(0,str(ROOT/'task'))
from validate_solution import Instance,OpenedOffice,validate_solution,validate
os.sched_setaffinity(0,set(map(int,os.environ.get("JOINT_CPU_PAIR","0,5").split(","))))
dest=R/'logs/joint_native_oracle';dest.mkdir(exist_ok=False)
rows=[]
for seed in range(32):
    rng=random.Random(742000+seed)
    data={'sites':[{'x':i%3+1+(10 if i>=3 else 0),'y':0,'reward':rng.randrange(1,31),
        'tasks':rng.choice([[],[0],[1],[0,1],[0,0,1]])} for i in range(6)],
        'offices':[{'x':0,'y':0,'cost':seed%5,'maxSize':2+seed%2},
                   {'x':10,'y':0,'cost':3,'maxSize':3}],
        'workers':[[0,1],[0,1]],'distances':[[rng.randrange(0,20) for i in range(6)] for o in range(2)],
        'maxDifference':seed%3,'balanceCoefficient':[0,1,10,100][seed%4]}
    if seed%5==0:data['sites'][1]['x']=data['sites'][0]['x']
    inc=[{'officeId':0,'sites':[0,2],'workers':[0]},{'officeId':1,'sites':[3,5],'workers':[1]}]
    parsed=Instance.model_validate(data);best=0.
    for mask in range(64):
        sol=[]
        for o in range(2):
            ss=[s for s in range(o*3,o*3+3) if mask>>s&1]
            if ss:sol.append(OpenedOffice.model_validate({'officeId':o,'sites':ss,'workers':[o]}))
        val=validate_solution(parsed,sol)
        if not isinstance(val,str):best=max(best,val)
    inp=dest/f'case{seed}.json';start=dest/f'case{seed}.incumbent.json';out=dest/f'case{seed}.solution.json'
    inp.write_text(json.dumps(data));start.write_text(json.dumps(inc))
    proc=subprocess.run([str(R/'bin/post_joint'),str(inp),str(start),str(out),'5'],capture_output=True,text=True,timeout=10)
    (dest/f'case{seed}.stderr').write_text(proc.stderr)
    value=validate(inp,out);ok=proc.returncode==0 and not isinstance(value,str) and abs(value-best)<1e-6
    row={'seed':seed,'expected':best,'actual':value,'rc':proc.returncode,'ok':ok};rows.append(row)
    (dest/'results.json').write_text(json.dumps(rows,indent=2));assert ok,row
print('native joint oracle PASS',len(rows),flush=True)
post=R/'logs/joint_native_mature';post.mkdir(exist_ok=False)
for case in ['alphabig','tightA','multiskill','anti','large','huge']:
    for seed in [1301,1302]:
        inp=R/'inputs'/f'{case}.json';inc=R/'logs/mature_v4_280'/f'{case}_{seed}_v4.solution.json'
        out=post/f'{case}_{seed}.solution.json';t=time.monotonic()
        proc=subprocess.run([str(R/'bin/post_joint'),str(inp),str(inc),str(out),'3'],capture_output=True,text=True,timeout=10)
        out.with_suffix('.stderr').write_text(proc.stderr)
        before=validate(inp,inc);after=validate(inp,out)
        row={'case':case,'seed':seed,'rc':proc.returncode,'before':before,'after':after,'wall':time.monotonic()-t,
             'ok':proc.returncode==0 and not isinstance(after,str) and after>=before-1e-6}
        out.with_suffix('.result.json').write_text(json.dumps(row,indent=2));assert row['ok'],row
        print(case,seed,'gain',after-before,flush=True)
