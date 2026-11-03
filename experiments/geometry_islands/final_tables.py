from pathlib import Path
import json,statistics as st
H=Path(__file__).resolve().parent
def read(tag):return json.loads((H/'logs'/tag/'results.json').read_text())['results']
md=['# Сводные сравнения','', 'Проценты — относительное изменение objective, затем равный вес каждому входу. Это не официальный нормированный score жюри. Все A/B: -O3 -std=c++17, TL60, NT2, jobs4. Зёрна не фиксируют траекторию многопоточного поиска.',''];summary={}
for tag,var,ref,expected in [('index_train60','grid','scan',32),('index_holdout60','grid','base',60),('robust_holdout60','exact','base',60)]:
 rows=read(tag);good=[r for r in rows if r['error'] is None and r['rc']==0];out=[];pairs=[]
 for case in sorted(set(r['case'] for r in rows)):
  a=[r for r in good if r['case']==case and r['variant']==ref];b=[r for r in good if r['case']==case and r['variant']==var]
  if not a or not b:continue
  av=st.median(r['score'] for r in a);bv=st.median(r['score'] for r in b);d=100*(bv/av-1) if av else 0
  for ar in a:
   br=next((r for r in b if r['seed']==ar['seed']),None)
   if br and ar['score']:pairs.append(dict(case=case,seed=ar['seed'],pct=100*(br['score']/ar['score']-1)))
  out.append(dict(case=case,n_base=len(a),n_new=len(b),base=av,candidate=bv,pct=d))
 ds=[r['pct'] for r in out];stats=dict(completed=len(rows),expected=expected,valid=len(good),mean_pct=st.mean(ds),median_pct=st.median(ds),worst_median=min(out,key=lambda r:r['pct']),best_median=max(out,key=lambda r:r['pct']),worst_pair=min(pairs,key=lambda r:r['pct']),best_pair=max(pairs,key=lambda r:r['pct']),paired_wins=sum(p['pct']>1e-7 for p in pairs),paired_losses=sum(p['pct']< -1e-7 for p in pairs),pairs=len(pairs),max_wall=max(r['wall'] for r in rows))
 summary[tag]=dict(stats=stats,table=out,pairs=pairs)
 md +=[f'## {tag}', '',f'Завершено {len(rows)}/{expected}, VALID {len(good)}/{len(rows)}. Mean {st.mean(ds):+.4f}%, median {st.median(ds):+.4f}%. Max wall {stats["max_wall"]:.3f} с.', '', '| Вход | n base/new | Медиана базы | Медиана новой | Δ |','|---|---:|---:|---:|---:|']
 for r in out:md.append(f'| {r["case"]} | {r["n_base"]}/{r["n_new"]} | {r["base"]:.9g} | {r["candidate"]:.9g} | {r["pct"]:+.4f}% |')
 md +=['',f'По парным зёрнам: wins/losses/ties={stats["paired_wins"]}/{stats["paired_losses"]}/{len(pairs)-stats["paired_wins"]-stats["paired_losses"]}; worst={stats["worst_pair"]}; best={stats["best_pair"]}.','']
# Transparent override: only failed multiskill rows replaced, original failures retained separately.
post=[];failures=[]
for tag,fix in [('post60_v1','post60_multiskill_v1_fixed'),('post60_open_v2','post60_multiskill_v2_fixed'),('post60_target_v3','post60_multiskill_v3_fixed'),('post60_global_v4','post60_multiskill_v4_fixed')]:
 for row in read(tag):
  source=tag
  if row['error'] is not None or row['rc']!=0:
   failures.append(dict(source=tag,row=row));old=row;row=next(r for r in read(fix) if r['case']==old['case'] and r['variant']==old['variant']);source=fix
  assert row['error'] is None and row['rc']==0
  before=row['stats']['before'];post.append(dict(source=source,case=row['case'],variant=row['variant'],seed=row['seed'],before=before,after=row['score'],pct=100*(row['score']/before-1) if before else 0))
md +=['## Post-операторы: исправленный вывод', '', 'У каждого оператора дополнительные60 с NT1 SEED11 после одинакового base60 NT2 SEED1. Семь неуспешных multiskill-выводов заменены явно указанными повторами *_fixed, исходные ошибки сохранены. Это сравнение операторов, а не equal-total-time A/B.', '', '| Метод | Входов | Mean Δ | Median Δ | max Δ | Улучшенных входов |','|---|---:|---:|---:|---:|---:|']
ps=[]
for var in sorted(set(r['variant'] for r in post)):
 rr=[r for r in post if r['variant']==var];ds=[r['pct'] for r in rr];p=dict(variant=var,cases=len(rr),mean=st.mean(ds),median=st.median(ds),maximum=max(ds),wins=sum(x>1e-7 for x in ds));ps.append(p)
 md.append(f'| {var} | {len(rr)} | {p["mean"]:+.4f}% | {p["median"]:+.4f}% | {p["maximum"]:+.4f}% | {p["wins"]} |')
summary['post']=dict(stats=ps,rows=post,raw_failures=failures)
(H/'COMPARISON.md').write_text('\n'.join(md)+'\n');(H/'logs/COMPARISON.json').write_text(json.dumps(summary,indent=2))
for tag,obj in summary.items():print(tag,json.dumps(obj['stats']))
