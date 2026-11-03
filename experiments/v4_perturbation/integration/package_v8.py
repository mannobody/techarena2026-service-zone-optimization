"""User-requested v8 packaging after the complete independent investigation.

No upload, Git operation, algorithm edit, or replacement of earlier releases.
Packaging is not promotion: the final acceptance decision is included verbatim.
"""
import hashlib,json,os,re,shutil,signal,subprocess,sys,time,zipfile
from pathlib import Path

# Serialize an observation copy without altering commands or subprocess env.
import sys as _report_sys
_REPORT_ROOT = next(p for p in Path(__file__).resolve().parents
                    if (p / 'tools/public_metadata.py').is_file())
_report_sys.path.insert(0, str(_REPORT_ROOT / 'tools'))
from public_metadata import public_json as _public_json
def report_json(value, **kwargs):
    return _public_json(value, _REPORT_ROOT, **kwargs)

I=Path(__file__).resolve().parent;R=I.parent;ROOT=R.parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
freeze=json.loads((I/'FINAL_FREEZE.json').read_text())
decision=json.loads((I/'FINAL_DECISION_WITH_AUDIT.json').read_text())
pipeline=json.loads((I/'HOLDOUT_PIPELINE_PROGRESS.json').read_text())
assert 'completed_unix' in pipeline or 'stopped_by_user_unix' in pipeline
assert (I/'REPORT.md').exists()
for k in ['source','binary']:assert sha(ROOT/freeze[k])==freeze[k+'_sha256']
target=ROOT/'experiments/server_v8'
target.mkdir(exist_ok=False)
art=target/'artifacts';art.mkdir()
package=art/'package';package.mkdir()
source=ROOT/freeze['source']
shutil.copy2(source,package/'main.cpp')
# Contest runner uses make build / make run, as in preserved v4/v6 packages.
# This adapter changes no C++ source or compiler flags. The original frozen
# research Makefile remains unchanged and continues to be checked by holdout.
(package/'Makefile').write_text('build:\n\tg++ -O3 -std=c++17 -pthread -o solution main.cpp\n\nrun:\n\tNT=2 ./solution\n\n.PHONY: build run\n')
archive=art/'case03_cpp_server_v8_O3.zip'
with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    for n in ['main.cpp','Makefile']:z.write(package/n,arcname=n)
check=art/'zip_check';check.mkdir()
with zipfile.ZipFile(archive) as z:
    assert set(z.namelist())=={'main.cpp','Makefile'} and len(z.namelist())==2
    assert z.testzip() is None
    for n in z.namelist():
        data=z.read(n);assert data==(package/n).read_bytes();(check/n).write_bytes(data)
cmd=['taskset','-c','14,15','make','-C',str(check),'build']
with (target/'BUILD_FROM_ZIP.log').open('x') as log:
    subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,check=True)
assert sha(check/'solution')==freeze['binary_sha256'], 'rebuild differs from tested binary; investigate before declaring package verified'
shutil.copy2(ROOT/'experiments/server_v6/logs/package_check/edge_one_site/instance.json',check/'instance.json')
env={k:v for k,v in os.environ.items() if k in ['PATH','HOME','LANG','LD_LIBRARY_PATH']};env['TL']='1'
start=time.monotonic();timeout=False
with (target/'MAKE_RUN_SMOKE.stdout').open('x') as out,(target/'MAKE_RUN_SMOKE.stderr').open('x') as err:
    process=subprocess.Popen(['taskset','-c','14,15','make','-C',str(check),'run'],env=env,stdout=out,stderr=err,start_new_session=True)
    try:rc=process.wait(timeout=11)
    except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);rc=process.wait();timeout=True
wall=time.monotonic()-start
sys.path.insert(0,str(ROOT/'task'));from validate_solution import validate
value=validate(check/'instance.json',check/'solution.json')
nt=re.search(r'threads=(\d+)',(target/'MAKE_RUN_SMOKE.stderr').read_text())
smoke={'rc':rc,'timeout':timeout,'wall':wall,'valid':not isinstance(value,str),'objective_or_error':value,
       'actual_nt':int(nt[1]) if nt else None,'DBG':'unset','TL':1,'input_sha256':sha(check/'instance.json'),'solution_sha256':sha(check/'solution.json')}
(target/'MAKE_RUN_SMOKE.json').write_text(report_json(smoke,indent=2))
assert rc==0 and not timeout and wall<=4 and not isinstance(value,str) and smoke['actual_nt']==2
status='recommended by the registered local gate' if decision['recommended_as_replacement'] else 'experimental; NOT recommended as a stable replacement for v4'
manifest={'packaged_unix':time.time(),'version':'v8','status':status,
    'zip':str(archive.relative_to(ROOT)),'zip_sha256':sha(archive),'zip_entries':['main.cpp','Makefile'],
    'source_sha256':sha(package/'main.cpp'),'makefile_sha256':sha(package/'Makefile'),
    'binary_rebuilt_from_zip_sha256':sha(check/'solution'),'identical_to_independently_tested_binary':True,
    'freeze_manifest':str((I/'FINAL_FREEZE.json').relative_to(ROOT)),'freeze_manifest_sha256':sha(I/'FINAL_FREEZE.json'),
    'decision':decision,'build_command':cmd,'default_seconds':280,'default_escape_mode':freeze['default_mode'],
    'contract':'Without argv: instance.json -> solution.json. Archive contains only main.cpp and Makefile. No runtime checkpoint/network/external solver dependency.',
    'no_arg_validation':json.loads((I/'logs/final_contract10/COMPLETE.json').read_text()),
    'make_run_entrypoint_smoke':smoke,
    'makefile_adapter':'Contest targets build/run and executable solution, matching v4/v6 interface; run explicitly sets NT=2, matching all comparisons. Same flags and byte-identical tested binary. Original frozen research Makefile retained unchanged.',
    'note':'Exact byte-identical rebuild links the ZIP to all already completed frozen-binary tests. No package upload or Git mutation performed.'}
summary280=json.loads((I/'HOLDOUT280_SUMMARY.json').read_text())
highlight=next(x for x in summary280['comparisons']['candidate_vs_v4']['pairs'] if x['case']=='anti' and x['seed']==2202)
manifest['requested_single_pair_highlight']={k:v for k,v in highlight.items() if k!='configuration'}
manifest['highlight_note']='Observed single pair at TL280/NT2/DBG1; not a general +24% improvement or guaranteed rerun result. V7 separately retains exact v4.'
(target/'PROVENANCE.json').write_text(report_json(manifest,indent=2))
(I/'V8_PACKAGE.json').write_text(report_json(manifest,indent=2))
intro=('V8 прошла зарегистрированный локальный критерий; скрытый серверный результат не гарантируется.' if decision['recommended_as_replacement'] else
       '**V8 подготовлена по просьбе пользователя как исследовательская посылка. Устойчивое превосходство v4 не подтверждено; использовать её как рекомендованную замену v4 нельзя.**')
readme=f'''# Server v8 — исследование малых возмущений

{intro}

Это тот самый замороженный код, который на anti/seed2202 при TL280 дал
**+24.245460% к exact v4**: objective69391.177295 →86215.387452.
Это отдельная пара, а не обещание +24% на других задачах или при повторе.
Консервативная [v7](../server_v7/README.md) отдельно сохраняет точную v4.

ZIP: `artifacts/case03_cpp_server_v8_O3.zip`, SHA256 `{sha(archive)}`.
Архив содержит ровно `main.cpp` и `Makefile`; сборка после распаковки дала
побайтово тот же binary, который прошёл независимые тесты. Default TL280,
без аргументов `instance.json` → `solution.json`; `make run` явно задаёт NT=2,
как во всех сравнительных тестах. Сеть, внешние solver-библиотеки, checkpoints и persistent caches
для runtime не нужны.

В активной политике v8: прежний exact-v4 LNS, небольшой согласованный support-kick
на плато, ограниченное boundary-восстановление перед откатом, отдельное лучшее
валидное состояние, немедленный offer после положительного изменения,
синхронизация журнала/guide/hash/worker cache и проверка времени после каждого
controller tick. По умолчанию ESCAPE_MODE=5; ESCAPE_MODE=0 — контрольный off.
Late acceptance, tabu, отдельный геометрический хвост, packet/cycle и изменения
v6 не включены в активную политику механически. Их положительные частные эффекты
и отрицательные результаты сохранены в лабораторных отчётах.

По просьбе пользователя дополнительные длинные повторы остановлены:16 из30
завершены,8 прерваны,6 не начаты. Обе первичные серии TL60/TL280 завершены.
Незавершённая серия сохранена отдельно и не используется для объединённой статистики.

Не смешивать development-успехи с независимым доказательством. Полные результаты,
регрессии, дополнительные seed, компоненты objective, источники, benchmark specs
и ограничения времени находятся в `../v4_perturbation/integration/REPORT.md`.
Краткий итог: `../v4_perturbation/REPORT.md`. Статус допуска и все хеши —
`PROVENANCE.json`. Измерения качества выполнялись с DBG=1 у всех вариантов;
стабильность default DBG=0 отдельно не заявляется.

Сборка после распаковки:

```sh
make build
make run
```

V4 и v6 сохранены. Ничего не закоммичено, не добавлено в staging, не отправлено
в Git или на конкурсный сервер. Этот ZIP не меняет ранее зарегистрированные
критерии принятия и не скрывает их результат.
'''
(target/'README.md').write_text(readme)
results=['# Результаты и изменения v8', '', intro, '',
    '| Независимая проверка | Среднее к v4, % | Медиана, % | Худшая пара, % | W/T/L |',
    '|---|---:|---:|---:|---|']
pooled_notes=[]
for seconds in [60,280]:
    summary=json.loads((I/f'HOLDOUT{seconds}_SUMMARY.json').read_text())
    comparison=summary['comparisons']['candidate_vs_v4']
    d=comparison['distribution_valid_outputs_including_failed_processes'];w=comparison['wtl']
    results.append(f"|TL{seconds}, первичная серия|{d['mean']:+.6f}|{d['median']:+.6f}|{d['min']:+.6f}|{w['win']}/{w['tie']}/{w['loss']}|")
    pooled=json.loads((I/f'HOLDOUT{seconds}_FINAL.json').read_text())
    if pooled.get('status'):
        pooled_notes.extend(['', 'TL280: первичная серия завершена; дополнительные длинные повторы остановлены пользователем (16 из 30 завершены). Объединённая статистика не вычислялась.', ''])
        continue
    p=pooled['comparisons']['candidate_vs_v4'];ci=p['input_bootstrap95_mean']
    pooled_notes.extend(['',f"TL{seconds} с зарегистрированными дополнительными seed: среднее при равном весе входов {p['input_weighted_mean']:+.6f}%, 95% bootstrap CI [{ci[0]:+.6f}; {ci[1]:+.6f}]%. Успешные процессы {pooled['success']}/{pooled['runs']}.",''])
results += pooled_notes
results += ['## Что включено', '',
    '* Основа — точная серверная v4, без накопленного гибрида solver/ и без изменений v6.',
    '* Согласованная замена опорных сайтов на плато и короткое восстановление native boundary_move.',
    '* Отдельное сохранение лучшего валидного состояния и проверенная публикация улучшения.',
    '* Синхронизация журнала, guide, hash и worker cache; обновление времени после каждого controller tick.',
    '* Конкурсный Makefile: make build / make run, NT=2, стандартный лимит 280 секунд.', '',
    '## Полезные результаты для дальнейшей работы', '',
    '* Геометрический support-kick реализован и проверен на одинаковых checkpoint-состояниях. Небольшие локальные выигрыши не переносятся автоматически на полный поиск.',
    '* Лучший development-вариант выбран по среднему с равным весом входов до генерации holdout. Отдельная абляция boundary без kick сохранена.',
    '* Контроль all-off показывает заметную чувствительность к layout/timing и выбору офисов. Для оценки новых операторов нужны оба контроля: exact v4 и собственный off.',
    '* Packet/cycle, late acceptance, tabu, retention-only и отдельный геометрический хвост реализованы, но не добавлены в активную политику из-за отсутствия устойчивой пользы.',
    '* Основное ограничение — стоимость восстановления и уход полного поиска в менее выгодную конфигурацию. Есть проигрыши и при неизменных офисах; одного объяснения через случайный выбор офисов недостаточно.', '',
    '## Материалы', '',
    '[Полный независимый отчёт](../v4_perturbation/integration/REPORT.md), [development и отрицательные результаты](../v4_perturbation/integration/RESEARCH_NOTES_RU.md), [геометрические операторы](../v4_perturbation/geometry_lab/REPORT.md), [управление плато](../v4_perturbation/escape_lab/REPORT.md), [затраты операторов](../v4_perturbation/integration/OPERATOR_EFFICIENCY.json).', '',
    'Все исходные логи, входы, решения, hashes и команды остаются в experiments/v4_perturbation. Копирование их в конкурсный ZIP не требуется: он содержит только main.cpp и Makefile. Ничего не отправлено на сервер.']
(target/'RESULTS_RU.md').write_text('\n'.join(results)+'\n')
print(report_json({k:manifest[k] for k in ['version','status','zip','zip_sha256','identical_to_independently_tested_binary']},indent=2))
