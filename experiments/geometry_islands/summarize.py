import json,statistics as st
from pathlib import Path

# Serialize an observation copy without altering commands or subprocess env.
import sys as _report_sys
_REPORT_ROOT = next(p for p in Path(__file__).resolve().parents
                    if (p / 'tools/public_metadata.py').is_file())
_report_sys.path.insert(0, str(_REPORT_ROOT / 'tools'))
from public_metadata import public_json as _public_json
def report_json(value, **kwargs):
    return _public_json(value, _REPORT_ROOT, **kwargs)

H=Path(__file__).resolve().parent;summary={};md=['# Результаты geometry_islands','', 'Каждая строка — один вход и вариант. Полные seed/config/пути находятся в results.json указанной серии. Для post прирост к сохранённому incumbent; это дополнительное время. Ошибки не скрываются.','']
for folder in sorted((H/'logs').iterdir()):
 p=folder/'results.json'
 if not p.exists():continue
 d=json.loads(p.read_text())
 if not isinstance(d,dict) or 'config' not in d:continue
 rows=d['results'];good=[r for r in rows if r['error'] is None and r['rc']==0];table=[];ref='base' if any(r['variant']=='base' for r in rows) else 'scan' if any(r['variant']=='scan' for r in rows) else None
 for case,var in sorted(set((r['case'],r['variant']) for r in rows)):
  rr=[r for r in good if r['case']==case and r['variant']==var];bb=[r['score'] for r in good if r['case']==case and r['variant']==ref]
  if not rr:continue
  vals=[r['score'] for r in rr];base=st.median(bb) if bb else rr[0].get('stats',{}).get('before');delta=100*(st.median(vals)/base-1) if base and base>0 else None
  table.append(dict(case=case,variant=var,n=len(rr),median=st.median(vals),min=min(vals),max=max(vals),delta_pct=delta,max_wall=max(r['wall'] for r in rr)))
 summary[folder.name]=dict(config=d['config'],total=len(rows),valid=len(good),reference=ref,table=table,failed=[r for r in rows if r not in good])
 md +=[f'## {folder.name}','',f"VALID {len(good)}/{len(rows)}. Config: `{report_json(d['config'],ensure_ascii=False)}`.",f"[Исходные результаты]({p.relative_to(_REPORT_ROOT)}).",'', '| Вход | Вариант | n | Медиана | min | max | Δ, % | max wall |','|---|---|---:|---:|---:|---:|---:|---:|']
 for r in table:md.append(f"| {r['case']} | {r['variant']} | {r['n']} | {r['median']:.9g} | {r['min']:.9g} | {r['max']:.9g} | {r['delta_pct'] if r['delta_pct'] is not None else '—'} | {r['max_wall']:.4f} |")
 md+=['']
 for var in sorted(set(r['variant'] for r in table)):
  ds=[r['delta_pct'] for r in table if r['variant']==var and r['delta_pct'] is not None]
  if ds and var!=ref:print(folder.name,var,'valid',len(good),'/',len(rows),'cases',len(ds),'mean',round(st.mean(ds),4),'median',round(st.median(ds),4),'worst',round(min(ds),4),'best',round(max(ds),4))
(H/'logs/SUMMARY.json').write_text(report_json(summary,indent=2));(H/'RESULTS.md').write_text('\n'.join(md))
