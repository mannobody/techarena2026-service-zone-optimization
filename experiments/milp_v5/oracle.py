from grouped import *
rows=[]
for r in json.loads((H.parent/'dp_milp/logs/milp_oracle.json').read_text()):
 I=Instance(r['data']);inc=[dict(officeId=o,sites=list(range(o*4,o*4+4)),workers=[o]) for o in range(3)]
 for mode in ['assigned','joint']:
  ans=improve(I,inc,60,mode,pools={o:list(range(o*4,o*4+4)) for o in range(3)});assert abs(ans['value']-r['expected'])<1e-6,(r['seed'],mode,ans);assert ans['status']=='HighsModelStatus.kOptimal' and not ans['invalid'];rows.append(dict(seed=r['seed'],expected=r['expected'],**{k:v for k,v in ans.items() if k!='solution'}))
(H/'logs/oracle.json').write_text(json.dumps(rows,indent=2));print(len(rows),'matches')
