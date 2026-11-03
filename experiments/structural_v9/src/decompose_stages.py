"""Endpoint identity for ordinary primary runs; no causal counterfactual claim."""
import json,re,statistics,os
from pathlib import Path
os.sched_setaffinity(0,{14,15})
R=Path(__file__).resolve().parents[1];d=R/'logs/independent280';a=json.loads((d/'results.json').read_text());by={(x['case'],x['seed'],x['variant']):x for x in a};out=[]
for x in a:
    if x['variant']!='candidate'or x['case'].startswith('small_'):continue
    b=by[x['case'],x['seed'],'v4'];t=(d/f"{x['case']}_{x['seed']}_candidate.stderr").read_text();s=re.search(r'ZMSIGNED .*before=([-0-9.]+) after=([-0-9.]+) seconds=([-0-9.]+)',t)
    row=dict(case=x['case'],seed=x['seed'],baseline=b['official'],candidate=x['official'],percent=100*(x['official']-b['official'])/abs(b['official']),both_success=x['success']and b['success'])
    if s:
        before=float(s[1]);after=float(s[2]);den=abs(b['official']);row.update(before_signed=before,after_signed=after,pre_stage_gap_percent=100*(before-b['official'])/den,signed_gain_percent=100*(after-before)/den,old_boundary_gain_percent=100*(x['official']-after)/den,signed_seconds=float(s[3]));assert abs(row['percent']-row['pre_stage_gap_percent']-row['signed_gain_percent']-row['old_boundary_gain_percent'])<1e-8
    else:row['decomposition']='no signed stage log; no inferred trajectory values'
    out.append(row)
(R/'ORDINARY_STAGE_DECOMPOSITION.json').write_text(json.dumps(out,indent=2))
lines=['## Разложение обычных независимых входов','',
'Для строк с логом: итоговый Δ% = разница с финальным v4 до signed + signed gain + прежняя boundary-доводка. Это численное разложение одной траектории; первый член включает ранний поиск и прежний finish, а не измеряет отдельную причину. В выбранном режиме pool выключен. Все33 пары остаются в основных метриках.','',
'|Вход|Логов|Mean Δ,%|До signed,%|Signed,%|Прежняя boundary,%|','|---|---:|---:|---:|---:|---:|']
for case in sorted(set(x['case']for x in out)):
    rows=[x for x in out if x['case']==case];q=[x for x in rows if 'signed_gain_percent'in x];mean=lambda k:statistics.mean(x[k]for x in q)
    fields=[f'{mean(k):+.5f}'for k in ['pre_stage_gap_percent','signed_gain_percent','old_boundary_gain_percent']]if q else ['—']*3
    lines.append('|'+case+'|'+str(len(q))+'/3|'+f"{statistics.mean(x['percent']for x in rows):+.5f}"+'|'+'|'.join(fields)+'|')
(R/'ORDINARY_STAGE_DECOMPOSITION_RU.md').write_text('\n'.join(lines)+'\n');print('\n'.join(lines[-8:]))
