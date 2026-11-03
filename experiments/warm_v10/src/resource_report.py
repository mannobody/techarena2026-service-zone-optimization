import json,statistics
from pathlib import Path
R=Path(__file__).resolve().parents[1];series=['development280_v5_both','acceleration280','independent280','resource_diagnostic280'];out={};lines=['# Фактически полученные ресурсы','', 'Одинаковая CPU-affinity задаёт одинаковое выделение двух CPU. Она не гарантирует одинаковую долю реально полученного процессорного времени. Ни одна строка не исключена из quality-таблиц из-за низкого CPU/wall. /proc-наблюдения выполняет внешний runner; C++ не читает их.']
for name in series:
 p=R/'logs'/name/'results.json'
 if not p.exists():continue
 rows=json.loads(p.read_text());details=[];groups={}
 for x in rows:
  f=x['resource_fields'];cpu=f.get('user',0)+f.get('sys',0);h=x.get('process_sampling');a=dict(case=x['case'],seed=x['seed'],variant=x['variant'],affinity=x['affinity'],wall=x['wall'],cpu=cpu,cpu_ratio=cpu/x['wall'],rss_kb=f.get('rss_kb'),working_success=x['success'])
  if h:
   runtime=sum(t['runtime_ns']for t in h['last'].values())/1e9;queue=sum(t['runqueue_ns']for t in h['last'].values())/1e9;states=h['states'];n=sum(states.values())
   a.update(sampled_runtime=runtime,sampled_runqueue=queue,sampled_cpu_ratio=runtime/x['wall'],sampled_runnable_fraction=states.get('R',0)/max(1,n),states=states,wchan=h['wchan'],last_io=h['last_io'],samples=h['samples'],max_sampled_threads=h['max_sampled_threads'],context_switches=x.get('resource_extra_fields'))
  details.append(a);groups.setdefault(x['variant'],[]).append(a)
 out[name]=dict(details=details,variants={v:dict(n=len(a),median_cpu_ratio=statistics.median(x['cpu_ratio']for x in a),min_cpu_ratio=min(x['cpu_ratio']for x in a),max_cpu_ratio=max(x['cpu_ratio']for x in a),median_wall=statistics.median(x['wall']for x in a),max_rss_kb=max(x['rss_kb']for x in a))for v,a in groups.items()},low_cpu=[a for a in details if a['wall']>100 and a['cpu_ratio']<1])
 lines+=['','## '+name,'','| Версия | n | Медиана CPU/wall | Минимум | Максимум | Max RSS, MiB |','|---|---:|---:|---:|---:|---:|']
 for v,a in out[name]['variants'].items():lines.append(f"| {v} | {a['n']} | {a['median_cpu_ratio']:.4f} | {a['min_cpu_ratio']:.4f} | {a['max_cpu_ratio']:.4f} | {a['max_rss_kb']/1024:.2f} |")
 for a in out[name]['low_cpu']:
  lines+=['',f"Низкий расход: {a['case']}/{a['seed']}/{a['variant']}, affinity {a['affinity']}, CPU/wall={a['cpu_ratio']:.4f}."]
  if 'sampled_runtime'in a:lines.append(f"Наблюдения: runtime≈{a['sampled_runtime']:.2f}s, runqueue≈{a['sampled_runqueue']:.2f}s, доля R-состояний {a['sampled_runnable_fraction']:.3f}, wchan={a['wchan']}. Это диагностические счётчики, а не причинное доказательство конкретного внешнего процесса/блокировки.")
(R/'RESOURCE_REPORT.json').write_text(json.dumps(out,indent=2));(R/'RESOURCE_REPORT_RU.md').write_text('\n'.join(lines)+'\n')
