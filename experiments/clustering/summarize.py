"""Aggregate saved measurements without rerunning a solver."""
from pathlib import Path
import json, statistics, hashlib
HERE=Path(__file__).resolve().parent

def main():
    summaries={}; lines=['# Сохранённые измерения кластеризации','', 'Дельты — отношение медиан score; все входы синтетические.','']
    for folder in sorted((HERE/'logs').iterdir()):
        f=folder/'results.json'
        if not f.exists(): continue
        d=json.loads(f.read_text()); rows=d['results']; info={'rows':len(rows),'config':d.get('config',{})}
        lines += ['## '+folder.name,'',f'Источник: {f}',f'Строк: {len(rows)}','']
        if rows and 'variant' in rows[0]:
            groups={}
            for case in sorted({r['case'] for r in rows}):
                cr=[r for r in rows if r['case']==case]
                values={v:statistics.median(r['score'] for r in cr if r['variant']==v) for v in sorted({r['variant'] for r in cr})}
                delta={v:100*(s/values['base']-1) if values['base'] else None for v,s in values.items() if v!='base'}
                groups[case]={'median_scores':values,'percent':delta}
                lines.append(f'{case}: '+json.dumps(groups[case],ensure_ascii=False))
            info['groups']=groups;info['errors']=sum(bool(r.get('error')) or r.get('returncode',0)!=0 for r in rows)
        elif rows and 'method' in rows[0]:
            info['improvements']=[dict(case=r['case'],method=r['method'],percent=100*(r['value']/r['base']-1),matched_percent=(100*(r['value']/r['matched']-1) if r.get('matched') else None)) for r in rows if r['base'] and r['value']>r['base']+1e-7]
            info['algorithm_seconds']={k:[min(r[k] for r in rows if k in r),max(r[k] for r in rows if k in r)] for k in ['seconds','algorithm_seconds','embedding_seconds'] if any(k in r for r in rows)}
            lines += [json.dumps(info,ensure_ascii=False)]
        else: lines += [json.dumps(rows,ensure_ascii=False)]
        summaries[folder.name]=info;lines += ['']
    (HERE/'logs/SUMMARY.json').write_text(json.dumps(summaries,indent=2,ensure_ascii=False))
    (HERE/'logs/SUMMARY.md').write_text('\n'.join(lines))
    files=[*HERE.glob('*.py'),*HERE.glob('*.h'),*HERE.glob('*.cpp'),*HERE.glob('*.md'),*HERE.glob('data/*.json'),*HERE.glob('logs/*/results.json')]
    (HERE/'MANIFEST.json').write_text(json.dumps({str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},indent=2))

if __name__=='__main__': main()
