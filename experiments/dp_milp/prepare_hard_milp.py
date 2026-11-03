from pathlib import Path
H=Path(__file__).resolve().parent;s=(H/'milp.py').read_text().replace('from pyscipopt import Model,quicksum','from pyscipopt import Model,quicksum,Eventhdlr,SCIP_EVENTTYPE\nimport json')
s=s.replace("mode='assigned'):","mode='assigned',checkpoint_path=None):")
needle=' warm=m.createSol();assigned='
handler='''
 def checkpoint():
  best=m.getBestSol()
  if best is None:return
  candidate=[]
  for o in ops:
   ss=[s for s in pool[o] if m.getSolVal(best,x[s])>.5]
   if ss:candidate.append(dict(officeId=o,sites=ss,workers=[w for w in range(I.w) if m.getSolVal(best,u[o,w])>.5] if joint else by[o]['workers']))
  score=value(I,candidate)
  if not isinstance(score,str) and score>=before-1e-7:
   dest=Path(checkpoint_path);tmp=dest.with_suffix('.tmp');tmp.write_text(json.dumps(dict(solution=candidate,value=score,before=before,status='checkpoint',seconds=time.perf_counter()-start,candidates=len(owner),mode=mode,rejected=None)));tmp.replace(dest)
 class BestEvent(Eventhdlr):
  def eventinit(self):self.model.catchEvent(SCIP_EVENTTYPE.BESTSOLFOUND,self)
  def eventexit(self):self.model.dropEvent(SCIP_EVENTTYPE.BESTSOLFOUND,self)
  def eventexec(self,event):checkpoint()
 if checkpoint_path:m.includeEventhdlr(BestEvent(),'save_best','validated offline checkpoint')
 warm=m.createSol();assigned='''
assert needle in s;s=s.replace(needle,handler,1);(H/'milp_checkpoint.py').write_text(s)
b=(H/'bench_milp.py').read_text().replace('milp60','milp_hard60').replace('from milp import Instance,improve','from milp_checkpoint import Instance,improve')
b=b.replace('60,mode);r.update',"58,mode,H/'logs/milp_hard60'/f'{case}_{mode}.checkpoint.json');r.update")
a=b.index('def run(job):');e=b.index('\nrows=[]',a)
b=b[:a]+'''def run(job):
 import time
 r,mode=job;dest=D/f'{r["case"]}_{mode}.checkpoint.json'
 # Parent publishes a validated incumbent before the child starts.
 from milp import Instance,value
 inc=json.loads(Path(r['incumbent']).read_text());before=value(Instance.read(r['input']),inc)
 dest.write_text(json.dumps(dict(solution=inc,value=before,before=before,status='initial',seconds=0,candidates=None,mode=mode,rejected=None)))
 t=time.monotonic()
 try:
  pr=subprocess.run([sys.executable,__file__,r['case'],mode,r['input'],r['incumbent']],text=True,capture_output=True,timeout=60,env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1'))
  (D/f'{r["case"]}_{mode}.stderr').write_text(pr.stderr)
  if pr.returncode:return dict(case=r['case'],mode=mode,rc=pr.returncode,error=pr.stderr)
  result=json.loads((D/f'{r["case"]}_{mode}.json').read_text());result['hard_timeout']=False
 except subprocess.TimeoutExpired:
  result=json.loads(dest.read_text());result.update(case=r['case'],input=r['input'],incumbent=r['incumbent'],hard_timeout=True,status='external_deadline',limit=60,threads=1)
 result['process_wall']=time.monotonic()-t
 return {k:v for k,v in result.items() if k!='solution'}
''' +b[e:]
(H/'bench_milp_hard.py').write_text(b)
