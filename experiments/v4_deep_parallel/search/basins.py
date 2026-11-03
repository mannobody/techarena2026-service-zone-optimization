from pathlib import Path
import json,re,sys
R=Path(__file__).resolve().parent;out=[]
for name in sys.argv[1:]:
 D=R/'logs'/name
 if not (D/'MANIFEST.json').exists():continue
 spec=json.loads((D/'MANIFEST.json').read_text())['spec']
 for case,path in spec['cases'].items():
  I=json.loads((R.parents[2]/path).read_text())
  for seed in spec['seeds']:
   for v in spec['variants']:
    p=D/f'{case}_{seed}_{v}.json'
    if not p.exists():continue
    row=json.loads(p.read_text());sp=p.with_suffix('.solution.json')
    if not row['success'] or not sp.exists():continue
    sol=json.loads(sp.read_text());op=sorted(z['officeId'] for z in sol);counts=[];loads=[];masks=[];profit=0;cost=0
    for z in sol:
     o=z['officeId'];counts.append(len(z['sites']));loads.append(sum(len(I['sites'][x]['tasks']) for x in z['sites']));masks.append(sorted({k for x in z['sites'] for k in I['sites'][x]['tasks']}));profit+=sum(I['sites'][x]['reward']-I['distances'][o][x] for x in z['sites']);cost+=I['offices'][o]['cost']
    text=p.with_suffix('.stderr').read_text();cands={int(a):sorted(map(int,filter(None,c.split(',')))) for a,b,c in re.findall(r'cand(\d+) f=([\d.eE+\-]+) ops=([\d,]*)',text)}
    ranks=[(int(a),float(b),int(c),int(d)) for a,b,c,d in re.findall(r'rank(\d+) val=([\d.eE+\-]+) cand=(\d+) ctor=(\d+)',text)]
    mask_rank=[a for a,b,c,d in ranks if cands.get(c)==op]
    its=sum(map(int,re.findall(r'lns it=(\d+)',text)));a=re.search(r'wide_start .*? t=([\d.]+)',text)
    out.append({'run':name,'case':case,'seed':seed,'variant':v,'objective':row['objective'],'offices':op,'counts':counts,'task_loads':loads,'skills':masks,'profit':profit,'cost':cost,'task_penalty':I['balanceCoefficient']*(max(loads)-min(loads)) if loads else 0,'candidate_mask_matches':[c for c,m in cands.items() if m==op],'candidate_rank_matches':mask_rank,'lns_iterations':its,'warm_end':float(a[1]) if a else None,'affinity':row['affinity']})
(R/'BASINS.json').write_text(json.dumps(out,indent=2));print(f'{len(out)} final configurations')
