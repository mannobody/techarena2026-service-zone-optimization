from pathlib import Path
H=Path(__file__).resolve().parent;s=(H/'milp_checkpoint.py').read_text().replace('checkpoint_path=None):','checkpoint_path=None,warm_extra=None):')
needle=' prep=time.perf_counter()-start;'
extra='''
 if warm_extra:
  w2=m.createSol();selected={s for row in warm_extra for s in row['sites']};opened={row['officeId'] for row in warm_extra}
  for s in owner:m.setSolVal(w2,x[s],int(s in selected))
  for o in ops:m.setSolVal(w2,z[o],int(o in opened))
  ll=[sum(int(I.tasks[s]) for s in row['sites']) for row in warm_extra]
  m.setSolVal(w2,hi,max(ll,default=0));m.setSolVal(w2,lo,min(ll,default=0));m.addSol(w2)
 prep=time.perf_counter()-start;'''
s=s.replace(needle,extra,1);(H/'milp_warm.py').write_text(s)
b=(H/'bench_milp_hard.py').read_text().replace('milp_hard60','milp_warm60').replace('from milp_checkpoint import Instance,improve','from milp_warm import Instance,improve')
b=b.replace("f'{case}_{mode}.checkpoint.json');r.update","f'{case}_{mode}.checkpoint.json',json.loads((H/'logs/native_post_relative60'/f'{case}_2.json').read_text()));r.update")
a=b.index('jobs=[');e=b.index('\ndef run(job):',a)
b=b[:a]+"jobs=[(r,'assigned') for r in items if r['case'] in ['controlled_many_sites','controlled_count_tight','controlled_gcd_large']]"+b[e:]
b=b.replace("inc=json.loads(Path(r['incumbent']).read_text());before=value(Instance.read(r['input']),inc)","inc=json.loads((H/'logs/native_post_relative60'/f'{r[\"case\"]}_2.json').read_text());before=value(Instance.read(r['input']),json.loads(Path(r['incumbent']).read_text()));warm_value=value(Instance.read(r['input']),inc)")
b=b.replace('solution=inc,value=before,before=before','solution=inc,value=warm_value,before=before')
(H/'bench_milp_warm.py').write_text(b)
