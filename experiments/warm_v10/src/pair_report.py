import json
from pathlib import Path
R=Path(__file__).resolve().parents[1];v=json.loads((R/'SELECTION.json').read_text())['variant'];d=R/'logs/independent280';summary=json.loads((d/'ANALYSIS.json').read_text());out={};lines=['# Разбор крайних независимых пар','', 'Это разложение конечных результатов и назначений. Оно не доказывает причинный вклад отдельного crossover/конструктора. Все исходные ответы, работники и координаты оболочек доступны по ссылкам.']
for control in ['v4','v9']:
 pairs=[p for p in summary['comparisons'][v+'_vs_'+control]['pairs']if p['percent']is not None];pairs.sort(key=lambda p:p['percent']);selected=pairs[:3]+list(reversed(pairs[-3:]));seen=set();details=[]
 lines+=['','## Сравнение с '+control,'']
 for p in selected:
  key=(p['case'],p['seed'])
  if key in seen:continue
  seen.add(key);c,seed=key;a_path=d/f'{c}_{seed}_{control}.analysis.json';b_path=d/f'{c}_{seed}_{v}.analysis.json';a=json.loads(a_path.read_text());b=json.loads(b_path.read_text())
  def metrics(x):
   zones=x['zones'];loads=[z['task_load']for z in zones];assignment={s:z['office']for z in zones for s in z['sites']}
   return dict(sites=len(assignment),offices=len(zones),workers=sum(len(z['workers'])for z in zones),task_min=min(loads,default=0),task_max=max(loads,default=0),assignment=assignment,opened=[z['office']for z in zones])
  ma,mb=metrics(a),metrics(b);union=ma['assignment'].keys()|mb['assignment'].keys();changed=sum(ma['assignment'].get(x,-1)!=mb['assignment'].get(x,-1)for x in union)
  delta={k:b[k]-a[k]for k in ['reward','distance','cost','penalty','objective']};assert abs(delta['objective']-(delta['reward']-delta['distance']-delta['cost']-delta['penalty']))<1e-6*max(1,abs(delta['objective']))
  detail=dict(pair=p,components_delta=delta,baseline={k:x for k,x in ma.items()if k!='assignment'},candidate={k:x for k,x in mb.items()if k!='assignment'},changed_assignments=changed,changed_on_union=changed/max(1,len(union)),baseline_analysis=str(a_path),candidate_analysis=str(b_path));details.append(detail)
  lines+=['',f"### {c}, seed {seed}: {p['percent']:+.4f}%",'', '| Величина | Контроль | Кандидат | Разность |','|---|---:|---:|---:|']
  for k in ['objective','reward','distance','cost','penalty']:lines.append(f"| {k} | {a[k]:.6f} | {b[k]:.6f} | {delta[k]:+.6f} |")
  for k in ['sites','offices','workers','task_min','task_max']:lines.append(f"| {k} | {ma[k]} | {mb[k]} | {mb[k]-ma[k]:+d} |")
  lines+=['',f"Изменены назначения {changed} сайтов ({100*detail['changed_on_union']:.2f}% объединения занятых сайтов). Офисы: {ma['opened']} → {mb['opened']}. "+f"[Контроль: состав/работники/оболочки]({a_path}), [кандидат]({b_path})."]
 out[control]=details
(R/'PAIR_ANALYSIS.json').write_text(json.dumps(out,indent=2));(R/'PAIR_ANALYSIS_RU.md').write_text('\n'.join(lines)+'\n')
