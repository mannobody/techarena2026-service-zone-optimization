#!/usr/bin/env python3
"""Aggregate complete experiments; preserve failed runs and unmatched pairs."""
import json,subprocess,sys,re,statistics as st
from pathlib import Path
R=Path(__file__).resolve().parent
expected={'diagnostic60_v1':18,'development60_clean':96,'development60_v3':96,'holdout60_tail':48,'huge180':6,'open60_tail':30,'regression60_repeat':12,'development60_cycle_repeat':48,'holdout60_cycle':48,'synthetic10_tail':28,'package_cycle_synthetic':28,'holdout60_cycle_variance':12}
quality={}
for name,n in expected.items():
 p=R/'logs'/name/'results.json'
 if not p.exists():continue
 rows=json.loads(p.read_text())
 if len(rows)!=n:print(name,'pending',len(rows),'/',n);continue
 subprocess.run([sys.executable,str(R/'summarize.py'),str(p)],check=True,capture_output=True)
 quality[name]=json.loads(p.with_name('SUMMARY.json').read_text())
ops={}
for name in ['warm_operators2_fixed','mature_operators2','mature_cycle2']:
 rows=json.loads((R/'logs'/name/'results.json').read_text());out={}
 for mode in sorted({x['mode'] for x in rows}):
  rr=[x for x in rows if x['mode']==mode];dd=[100*x['gain']/max(1,abs(x['initial'])) for x in rr if x['success']]
  out[mode]={'runs':len(rr),'success':sum(x['success'] for x in rr),'mean_pct':st.mean(dd),'median_pct':st.median(dd),'min_pct':min(dd),'max_pct':max(dd),'std_pct':st.pstdev(dd),'wtl':[sum(d>1e-7 for d in dd),sum(abs(d)<=1e-7 for d in dd),sum(d< -1e-7 for d in dd)],'max_wall':max(x['wall'] for x in rr)}
 ops[name]=out
traces={}
for name in quality:
 rr=[]
 for p in (R/'logs'/name).glob('*.stderr'):
  for before,after,end,deadline in re.findall(r'trace_exchange_finish before=([\d.e+-]+) after=([\d.e+-]+) end=([\d.e+-]+) deadline=([\d.e+-]+)',p.read_text()):
   a,b,e,d=map(float,(before,after,end,deadline));rr.append({'run':p.stem,'before':a,'after':b,'gain':b-a,'pct':100*(b-a)/max(1,abs(a)),'deadline_overrun':max(0,e-d)})
 if rr:traces[name]={'calls':len(rr),'improvements':sum(x['gain']>1e-7 for x in rr),'mean_pct':st.mean(x['pct'] for x in rr),'max_pct':max(x['pct'] for x in rr),'max_deadline_overrun':max(x['deadline_overrun'] for x in rr),'runs':rr}
variance={}
if 'holdout60_cycle_variance' in quality:
 extra=json.loads((R/'logs/holdout60_cycle_variance/results.json').read_text())
 original=json.loads((R/'logs/holdout60_cycle/results.json').read_text())
 combined=extra+[x for x in original if x['case'] in ('alphabig','large')]
 derived=R/'logs/holdout_cycle_sixseed';derived.mkdir(exist_ok=True)
 (derived/'results.json').write_text(json.dumps(combined,indent=2))
 subprocess.run([sys.executable,str(R/'summarize.py'),str(derived/'results.json')],check=True,capture_output=True)
 variance=json.loads((derived/'SUMMARY.json').read_text())
(R/'FINAL_METRICS.json').write_text(json.dumps({'quality':quality,'operators':ops,'tail_traces':traces,'variance_six_seed':variance},indent=2))
lines=['| Серия / кандидат | Успехи | Среднее Δ% | Медиана Δ% | min Δ% | max Δ% | σ, п.п. | W/T/L |','|---|---:|---:|---:|---:|---:|---:|---|']
for name,q in quality.items():
 for v,c in q['comparisons'].items():
  d=c['paired_pct']
  if not d:continue
  lines.append(f"| {name} / {v} | {q['success']}/{q['runs']} | {d['mean']:+.4f} | {d['median']:+.4f} | {d['worst']:+.4f} | {d['best']:+.4f} | {d['std']:.4f} | {'/'.join(map(str,c['wtl']))} |")
(R/'RESULTS_TABLE.md').write_text('\n'.join(lines)+'\n')
print('\n'.join(lines))
