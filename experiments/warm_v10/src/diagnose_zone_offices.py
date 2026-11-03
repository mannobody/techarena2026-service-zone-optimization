"""Research-only fixed-site-group anchor assignment, never used by the contest solver."""
import copy,hashlib,itertools,json,math,sys,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];ROOT=R.parents[1];sys.path.insert(0,str(ROOT/'task'))
from validate_solution import validate
inp,inc,dest=map(Path,sys.argv[1:4]);dest.mkdir(exist_ok=False);a=json.loads(inp.read_text());sol=json.loads(inc.read_text());base=validate(inp,inc);assert isinstance(base,(int,float))
no=len(a['offices']);K=len(sol);deltas=[]
for z in sol:
 old=z['officeId'];deltas.append([a['offices'][old]['cost']-a['offices'][o]['cost']+sum(a['distances'][old][s]-a['distances'][o][s]for s in z['sites'])for o in range(no)])
start=time.monotonic();seen=feasible=0;complete=True;best_upper=0.;best_valid=base;proposals=[]
for offices in itertools.permutations(range(no),K):
 seen+=1
 if seen>2000000 or time.monotonic()-start>20:complete=False;break
 if any(len(sol[i]['sites'])>a['offices'][o]['maxSize']for i,o in enumerate(offices)):continue
 feasible+=1;gain=sum(deltas[i][o]for i,o in enumerate(offices));best_upper=max(best_upper,gain)
 if gain<=1e-7:continue
 s=copy.deepcopy(sol)
 for i,o in enumerate(offices):s[i]['officeId']=o
 p=dest/(str(len(proposals))+'.solution.json');p.write_text(json.dumps(s));v=validate(inp,p);valid=isinstance(v,(int,float))
 if valid:assert abs(v-base-gain)<1e-6*max(1,abs(gain));best_valid=max(best_valid,v)
 proposals.append(dict(offices=offices,predicted_gain=gain,official=v,valid=valid,solution=str(p)))
out=dict(original=base,best_valid=best_valid,best_gain=best_valid-base,complete=complete,enumerated=seen,expected=math.perm(no,K),capacity_feasible=feasible,best_gain_ignoring_geometry=best_upper,positive_proposals=proposals,instance_sha256=hashlib.sha256(inp.read_bytes()).hexdigest(),incumbent_sha256=hashlib.sha256(inc.read_bytes()).hexdigest(),command=sys.argv,note='Viewed-input endpoint diagnosis. Site groups and worker teams fixed; all geometric conflicts checked officially. Not a complete-solver benchmark, no changes to frozen source or primary output.')
(dest/'result.json').write_text(json.dumps(out,indent=2));print(json.dumps({k:v for k,v in out.items()if k not in ['positive_proposals','command','note']}))
