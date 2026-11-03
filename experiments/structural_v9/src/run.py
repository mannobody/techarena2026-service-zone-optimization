"""Paired same-core NT=2 complete runs, official validation outside timing."""
import concurrent.futures,hashlib,json,os,random,re,signal,subprocess,sys,time,queue,statistics
from pathlib import Path
from shapely.geometry import MultiPoint
R=Path(__file__).resolve().parents[1];ROOT=R.parents[1];sys.path.insert(0,str(ROOT/'task'))
from validate_solution import validate
sys.path.insert(0,str(ROOT/'tools'))
from public_metadata import public_json
def report_json(value, **kwargs):
    return public_json(value, ROOT, **kwargs)
os.sched_setaffinity(0,{14,15}) # runner/validators outside the solver CPU pairs
specpath=Path(sys.argv[1]);spec=json.loads(specpath.read_text());dest=R/'logs'/spec['name'];dest.mkdir(exist_ok=False)
cpus=spec.get('cpus',[[12,13],[16,17],[18,19],[20,21]])
slots=queue.Queue()
for cpu in cpus:slots.put(cpu)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
manifest={'spec':spec,'spec_sha256':sha(specpath),'inputs':{k:sha(ROOT/v)for k,v in spec['cases'].items()},'binaries':{k:sha(ROOT/v['binary'])for k,v in spec['variants'].items()},'validator':sha(ROOT/'task/validate_solution.py'),'cpu_topology':subprocess.check_output(['lscpu','-p=CPU,CORE,SOCKET'],text=True),'runner_sha256':sha(Path(__file__))}
(dest/'MANIFEST.json').write_text(report_json(manifest,indent=2))
def describe(inp,out):
    a=json.loads(inp.read_text());s=json.loads(out.read_text());reward=distance=cost=0.;loads=[];zones=[]
    for o in s:
        idx=o['officeId'];ss=o['sites'];oo=a['offices'][idx]
        rw=sum(a['sites'][x]['reward']for x in ss);di=sum(a['distances'][idx][x]for x in ss);lo=sum(len(a['sites'][x]['tasks'])for x in ss)
        reward+=rw;distance+=di;cost+=oo['cost'];loads.append(lo)
        h=MultiPoint([(a['sites'][x]['x'],a['sites'][x]['y'])for x in ss]+[(oo['x'],oo['y'])]).convex_hull
        zones.append(dict(office=idx,sites=ss,workers=o['workers'],site_count=len(ss),task_load=lo,reward=rw,distance=di,cost=oo['cost'],hull=h.__geo_interface__))
    penalty=a['balanceCoefficient']*(max(loads)-min(loads))if loads else 0
    return dict(reward=reward,distance=distance,cost=cost,penalty=penalty,objective=reward-distance-cost-penalty,zones=zones)
def run_one(case,seed,label,conf,cpu):
    prefix=dest/f'{case}_{seed}_{label}';inp=ROOT/spec['cases'][case];out=prefix.with_suffix('.solution.json');err=prefix.with_suffix('.stderr');res=prefix.with_suffix('.resource')
    env={k:v for k,v in os.environ.items()if k in ['PATH','HOME','LANG','LD_LIBRARY_PATH']};env|={'NT':'2','SEED':str(seed)};env.update(conf.get('env',{}))
    assert sha(inp)==manifest['inputs'][case]and sha(ROOT/conf['binary'])==manifest['binaries'][label]
    cmd=['/usr/bin/time','-f','rss_kb=%M user=%U sys=%S','-o',str(res),'taskset','-c',','.join(map(str,cpu)),str(ROOT/conf['binary']),str(inp),str(out),str(spec['seconds'])]
    begin=time.monotonic();started=time.time();timed=False;snapshots=[];points=iter([spec['seconds']*x for x in [.25,.50,.85]]);nextpoint=next(points,None)
    with err.open('w')as f:
        p=subprocess.Popen(cmd,env=env,stdout=subprocess.DEVNULL,stderr=f,start_new_session=True)
        while p.poll()is None:
            wall=time.monotonic()-begin
            if nextpoint is not None and wall>=nextpoint:
                try:
                    data=json.loads(out.read_text());snap=prefix.with_name(prefix.name+f'.t{nextpoint:.2f}.solution.json');snap.write_text(report_json(data));snapshots.append(dict(at=wall,path=str(snap.relative_to(ROOT))))
                except (OSError,ValueError):pass
                nextpoint=next(points,None)
            if wall>spec['seconds']+spec.get('grace',2):
                timed=True;os.killpg(p.pid,signal.SIGTERM)
                try:p.wait(timeout=1)
                except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
                break
            time.sleep(.015 if spec['seconds']<20 else .05)
        rc=p.wait()
    wall=time.monotonic()-begin;v=validate(inp,out);valid=isinstance(v,(int,float));txt=err.read_text()
    row=dict(case=case,seed=seed,variant=label,command=cmd,env=env,affinity=cpu,rc=rc,timeout=timed,wall=wall,started_unix=started,ended_unix=time.time(),official=v,valid=valid,snapshots=snapshots,solution_sha256=sha(out)if out.exists()else None,resource=res.read_text()if res.exists()else '',error=bool(re.search(r'error:|VERIFY|INVALID',txt)))
    row['internal_deadline_stop']='ZM deadline_stop=1'in txt
    nt=re.findall(r'threads=(\d+)',txt);row['logged_threads']=int(nt[-1])if nt else None
    row['resource_fields']={k:float(v)for k,v in re.findall(r'(rss_kb|user|sys)=([0-9.]+)',row['resource'])}
    row['success']=rc==0 and not timed and valid and not row['error']and wall<=spec['seconds']+.2
    if valid:
        desc=describe(inp,out);assert abs(desc['objective']-v)<1e-6*max(1,abs(v));row['components']={k:x for k,x in desc.items()if k!='zones'};prefix.with_suffix('.analysis.json').write_text(report_json(desc,indent=2))
    for snap in snapshots:
        snap['official']=validate(inp,ROOT/snap['path'])
    prefix.with_suffix('.json').write_text(report_json(row,indent=2));return row
def pair(case,seed):
    cpu=slots.get();variants=list(spec['variants'].items());random.Random(seed*7919+sum(map(ord,case))).shuffle(variants)
    try:return [run_one(case,seed,label,conf,cpu)for label,conf in variants]
    finally:slots.put(cpu)
tasks=[(c,s)for c in spec['cases']for s in spec['seeds']];random.Random(442).shuffle(tasks);rows=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=len(cpus))as pool:
    for f in concurrent.futures.as_completed([pool.submit(pair,*p)for p in tasks]):
        new=f.result();rows+=new;(dest/'results.json').write_text(report_json(rows,indent=2))
        print(report_json(dict(done=len(rows),total=len(tasks)*len(spec['variants']),case=new[0]['case'],seed=new[0]['seed'],values={r['variant']:r['official']for r in new},ok=all(r['success']for r in new))),flush=True)
