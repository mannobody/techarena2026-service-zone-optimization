"""Regenerate aggregate tables; never infer judge score from synthetic ratios."""
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import statistics

HERE=Path(__file__).resolve().parent


def main():
    lines=['# Измерения evolution','',
           'Все задачи сгенерированы. `score` — значение исходной целевой функции.',
           'В ячейке: медиана по доступным зёрнам; число прогонов указано отдельно.',
           'Таблица автоматически строится из logs/*/results.json. Незаконченные серии помечены числом строк.', '']
    manifest={};summary={}
    for f in sorted((HERE/'logs').glob('*/results.json')):
        d=json.loads(f.read_text());r=d['results'];tag=f.parent.name
        if not r:continue
        for p in [f,*f.parent.glob('*.snapshot'),*f.parent.glob('build.json'),*f.parent.glob('config.json')]:
            manifest[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
        for p in d.get('config',{}).get('inputs',[]):
            path=Path(p);manifest[p]=hashlib.sha256(path.read_bytes()).hexdigest()
        lines += [f'## {tag}','',f'Данные: {f}; строк: {len(r)}.', '',
                  '`'+json.dumps(d.get('config',{}),ensure_ascii=False)+'`','']
        if 'package' in d:
            lines+=[f"VALID {len(r)}/{len(r)}; seconds={d['seconds']}; NT={d['threads']}; max wall={max(x['wall'] for x in r):.3f}s.",'']
            continue
        if 'variant' not in r[0]:
            lines+=['| Задача | Исходное | После MIP | Контроль, то же время | Время MIP, с |',
                    '|---|---:|---:|---:|---:|']
            for x in r:lines.append(f"| {x['case']} | {x['base']:.6f} | {x['local']:.6f} | {x['matched']:.6f} | {x['extra_wall']:.6f} |")
            lines+=[''];continue
        grouped=defaultdict(list)
        for x in r:grouped[x['case'],x['variant']].append(x)
        variants=sorted({x['variant'] for x in r});cases=sorted({x['case'] for x in r})
        lines+=['| Задача | '+' | '.join(variants)+' | n по вариантам |',
                '|---|'+'---:|'*len(variants)+'---|']
        aggregate={}
        for c in cases:
            stats={v:statistics.median(x['score'] for x in grouped[c,v] if x['score'] is not None)
                   for v in variants if grouped[c,v] and any(x['score'] is not None for x in grouped[c,v])}
            aggregate[c]=stats
            lines.append('| '+c+' | '+' | '.join(f'{stats[v]:.6f}' if v in stats else '—' for v in variants)+' | '+
                         ', '.join(str(len(grouped[c,v])) for v in variants)+' |')
        errors=[{k:x[k] for k in ['case','variant','seed','error']} for x in r if x['error']]
        limits=sorted({x['limit'] for x in r});threads=sorted({x['threads'] for x in r})
        summary[tag]=dict(rows=len(r),limits=limits,threads=threads,median_by_case=aggregate,
                          wall_min=min(x['wall'] for x in r),wall_max=max(x['wall'] for x in r),errors=errors)
        lines += ['',f"VALID: {len(r)-len(errors)}/{len(r)}; wall min/max: {summary[tag]['wall_min']:.3f}/{summary[tag]['wall_max']:.3f} с.",'']
    for p in HERE.glob('*.py'):
        manifest[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
    for p in [*HERE.glob('*.h'),*HERE.glob('*.cpp')]:
        manifest[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
    for p in [*HERE.glob('*.md'),HERE/'requirements.txt',*HERE.glob('data/holdout/*.txt')]:
        if p.exists():manifest[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
    for p in (HERE/'logs').rglob('*'):
        if p.is_file() and p.suffix in ('.json','.txt','.snapshot') and p.name!='summary.json':
            manifest[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
    for p in [*HERE.glob('artifacts/candidate*.zip'),*HERE.glob('artifacts/candidate*/manifest.json')]:
        manifest[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
    for p in (HERE/'data').rglob('*.json'):
        manifest[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
    (HERE/'logs/SUMMARY.md').write_text('\n'.join(lines)+'\n')
    (HERE/'logs/summary.json').write_text(json.dumps(summary,indent=2))
    (HERE/'MANIFEST.json').write_text(json.dumps(manifest,indent=2))
    print(HERE/'logs/SUMMARY.md')


if __name__=='__main__':main()
