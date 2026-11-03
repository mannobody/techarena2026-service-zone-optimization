import json,statistics as st
from pathlib import Path
H=Path(__file__).resolve().parent
summary=json.loads((H/'logs/SUMMARY.json').read_text());lines=['# Числовые результаты','', 'Все цели исходные; проценты — к медиане базы того же входа в той же серии.','Флаги сборки всех native-вариантов: `g++ -O3 -std=c++17`.','']
for tag,v in summary.items():
 lines += [f'## {tag}','',f"Допустимых: {v['valid']}/{v['count']}. Параметры: `{json.dumps(v['config'],ensure_ascii=False,sort_keys=True)}`.",f"Полные наблюдения и пути входов/ответов: [{tag}/results.json]({H/'logs'/tag/'results.json'}).",'', '| Вход | Вариант | n | Медиана | min | max | Δ медиан, % | max wall, с |','|---|---|---:|---:|---:|---:|---:|---:|']
 for r in v['table']:
  delta=f"{r['delta_pct']:+.4f}" if r['delta_pct'] is not None else '—'
  lines.append(f"| {r['case']} | {r['variant']} | {r['n']} | {r['median']:.9g} | {r['min']:.9g} | {r['max']:.9g} | {delta} | {r['max_wall']:.3f} |")
 lines+=['']
p=H/'logs/TAIL_ANALYSIS.json'
if p.exists():
 for tag,r in json.loads(p.read_text()).items():
  ds=[v['delta_pct'] for v in r['paired']]
  lines += [f'## Фактическая доводка: {tag}','',f"Внутри собственного запуска: улучшений {r['actual_positive']}/{r['actual_count']}, средний прирост по вызванным финальным этапам {r['actual_mean_pct']:.4f}%.",f"Для независимых A/B запусков: пар {len(ds)}, медиана Δ {st.median(ds) if ds else 0:+.4f}%, min {min(ds) if ds else 0:+.4f}%, max {max(ds) if ds else 0:+.4f}%.",f"Среднее отношений медиан по задачам: {r['case_mean_pct']:+.4f}%. Описательный bootstrap CI среднего по задачам: {r['case_bootstrap_mean_ci95']}; малое число задач и общая конкурентная нагрузка ограничивают интерпретацию.",'']
  for key,title in [('enabled_cases','N≤1500: оператор разрешён'),('disabled_control_cases','N>1500: оператор отключён, контроль разброса')]:
   g=r[key]
   if g['count']:
    lines += [f"{title}: {g['count']} задач; среднее {g['mean_pct']:+.4f}%, медиана {g['median_pct']:+.4f}%, диапазон {g['min_pct']:+.4f}..{g['max_pct']:+.4f}%.",'']
(H/'RESULTS.md').write_text('\n'.join(lines))
