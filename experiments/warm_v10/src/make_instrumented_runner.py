"""Add external /proc observations; keep measured development runner immutable."""
from pathlib import Path
R=Path(__file__).resolve().parents[1];p=R/'src/run_instrumented.py';assert not p.exists()
s=(R/'src/run.py').read_text()
def replace(a,b):
 global s
 assert s.count(a)==1,(a[:80],s.count(a));s=s.replace(a,b)
replace('import concurrent.futures,hashlib,json,os,random,re,signal,subprocess,sys,time,queue,statistics',
        'import concurrent.futures,hashlib,json,os,random,re,signal,subprocess,sys,time,queue,statistics,collections')
replace("def describe(inp,out):",'''def sample_process(wrapper,history):
    # GNU time waits for its direct child; taskset then execs the contest executable.
    try:
        children=Path(f'/proc/{wrapper}/task/{wrapper}/children').read_text().split()
        if not children:return
        pid=int(children[0]);tasks=Path(f'/proc/{pid}/task')
        active=0
        for q in tasks.iterdir():
            try:
                stat=q.joinpath('stat').read_text().split(') ')[1].split()
                sched=q.joinpath('schedstat').read_text().split()
                wait=q.joinpath('wchan').read_text().strip()
                history['last'][q.name]=dict(runtime_ns=int(sched[0]),runqueue_ns=int(sched[1]),slices=int(sched[2]))
                history['states'][stat[0]]+=1;history['wchan'][wait]+=1;active+=1
            except (OSError,ValueError,IndexError):pass
        history['max_sampled_threads']=max(history['max_sampled_threads'],active)
        history['samples']+=1
        try:history['last_io']={k:int(v)for k,v in re.findall(r'(\\w+):\\s*(\\d+)',Path(f'/proc/{pid}/io').read_text())}
        except OSError:pass
    except (OSError,ValueError,IndexError):pass

def describe(inp,out):''')
replace("'-f','rss_kb=%M user=%U sys=%S'", "'-f','rss_kb=%M user=%U sys=%S majorfaults=%F minorfaults=%R voluntary=%w involuntary=%c inputs=%I outputs=%O'")
replace("    pressure_before=cpu_pressure()", "    history=dict(last={},states=collections.Counter(),wchan=collections.Counter(),max_sampled_threads=0,samples=0,last_io={});next_sample=0.\n    pressure_before=cpu_pressure()")
replace("            wall=time.monotonic()-begin", "            wall=time.monotonic()-begin\n            if wall>=next_sample:\n                sample_process(p.pid,history);next_sample=wall+min(1.,spec['seconds']/4)")
replace("    row['internal_deadline_stop']='ZM deadline_stop=1'in txt", "    row['process_sampling']=history\n    row['resource_extra_fields']={k:float(v)for k,v in re.findall(r'(majorfaults|minorfaults|voluntary|involuntary|inputs|outputs)=([0-9.]+)',row['resource'])}\n    row['internal_deadline_stop']='ZM deadline_stop=1'in txt")
p.write_text(s)
