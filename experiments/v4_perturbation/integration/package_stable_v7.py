"""Package exact v4 as conservative v7 after the user's stability-only instruction.

No new algorithm passed the registered gate. Do not call this a solver gain.
The experimental candidate is separately packaged by package_v8.py.
"""
import hashlib,json,os,re,shutil,signal,subprocess,sys,time,zipfile
from pathlib import Path
I=Path(__file__).resolve().parent;R=I.parent;ROOT=R.parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
decision=json.loads((I/'FINAL_DECISION_WITH_AUDIT.json').read_text())
assert not decision['recommended_as_replacement'], 'Reassess release selection if the registered gate changes'
assert decision['final_record_audit_pass']
pipeline=json.loads((I/'HOLDOUT_PIPELINE_PROGRESS.json').read_text())
assert 'completed_unix' in pipeline or 'stopped_by_user_unix' in pipeline
source=R/'baseline/frozen_v4.cpp';binary=R/'baseline/v4'
source_hash='5b3914fa9791cb879f3232fb2876a915de83b848ad4b353b0dbf25b574998c25'
binary_hash='5cc54b6ad0f02a3d6d471d0e2f9129c229b4925aaa2b2c01ce26bd5305a4963c'
assert sha(source)==source_hash and sha(binary)==binary_hash
target=ROOT/'experiments/server_v7';target.mkdir(exist_ok=False)
art=target/'artifacts';art.mkdir();package=art/'package';package.mkdir()
shutil.copy2(source,package/'main.cpp')
# GCC embeds the compilation unit basename in ELF STT_FILE. Preserve the
# baseline basename so even metadata can match the measured control binary.
# The generated build copy is not a runtime dependency or an archive entry.
(package/'Makefile').write_text('build:\n\tcp main.cpp frozen_v4.cpp\n\tg++ -O3 -std=c++17 -pthread -o solution frozen_v4.cpp\n\nrun:\n\tNT=2 ./solution\n\n.PHONY: build run\n')
archive=art/'case03_cpp_server_v7_O3.zip'
with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    for n in ['main.cpp','Makefile']:z.write(package/n,arcname=n)
check=art/'zip_check';check.mkdir()
with zipfile.ZipFile(archive) as z:
    assert set(z.namelist())=={'main.cpp','Makefile'} and len(z.namelist())==2 and z.testzip() is None
    for n in z.namelist():
        data=z.read(n);assert data==(package/n).read_bytes();(check/n).write_bytes(data)
with (target/'BUILD_FROM_ZIP.log').open('x') as log:
    subprocess.run(['taskset','-c','14,15','make','-C',str(check),'build'],stdout=log,stderr=subprocess.STDOUT,check=True)
assert sha(check/'solution')==binary_hash, 'ZIP rebuild differs from exact v4 control'
shutil.copy2(ROOT/'experiments/server_v6/logs/package_check/edge_one_site/instance.json',check/'instance.json')
env={k:v for k,v in os.environ.items() if k in ['PATH','HOME','LANG','LD_LIBRARY_PATH']};env['TL']='1'
start=time.monotonic();timeout=False
with (target/'MAKE_RUN_SMOKE.stdout').open('x') as out,(target/'MAKE_RUN_SMOKE.stderr').open('x') as err:
    p=subprocess.Popen(['taskset','-c','14,15','make','-C',str(check),'run'],env=env,stdout=out,stderr=err,start_new_session=True)
    try:rc=p.wait(timeout=11)
    except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);rc=p.wait();timeout=True
wall=time.monotonic()-start
sys.path.insert(0,str(ROOT/'task'));from validate_solution import validate
value=validate(check/'instance.json',check/'solution.json')
nt=re.search(r'threads=(\d+)',(target/'MAKE_RUN_SMOKE.stderr').read_text())
smoke={'rc':rc,'timeout':timeout,'wall':wall,'valid':not isinstance(value,str),'objective_or_error':value,
       'actual_nt':int(nt[1]) if nt else None,'DBG':'unset','TL':1,'input_sha256':sha(check/'instance.json'),'solution_sha256':sha(check/'solution.json')}
(target/'MAKE_RUN_SMOKE.json').write_text(json.dumps(smoke,indent=2))
assert rc==0 and not timeout and wall<=4 and not isinstance(value,str) and smoke['actual_nt']==2
manifest={'version':'v7','status':'exact v4 baseline; no new algorithmic improvement claimed','packaged_unix':time.time(),
          'zip':str(archive.relative_to(ROOT)),'zip_sha256':sha(archive),'zip_entries':['main.cpp','Makefile'],
          'source_sha256':source_hash,'makefile_sha256':sha(package/'Makefile'),'binary_rebuilt_from_zip_sha256':binary_hash,
          'identical_to_independently_tested_binary':True,'baseline_source':str(source.relative_to(ROOT)),
          'default_seconds':280,'make_run_nt':2,'make_run_entrypoint_smoke':smoke,
          'evidence':'This exact binary is the v4 control in every primary and extra independent TL60/TL280 run.',
          'selection':'No new combination passed the registered stability gate. User requested experimental +24% candidate in v8, stable-only v7. Therefore v7 retains exact v4.',
          'build_source_basename':'Makefile creates an identical frozen_v4.cpp build copy to preserve ELF source-name metadata; runtime reads no source file.',
          'experimental_candidate':'experiments/server_v8','experimental_decision':decision,
          'no_upload_or_git_mutation':True}
(target/'PROVENANCE.json').write_text(json.dumps(manifest,indent=2))
(I/'V7_PACKAGE.json').write_text(json.dumps(manifest,indent=2))
(target/'README.md').write_text(f'''# Server v7 — стабильная основа

**V7 побайтово сохраняет исходник и собранный бинарник точной серверной v4.
Новых алгоритмических улучшений здесь нет:** ни одна проверенная новая
комбинация не прошла заранее заданный критерий устойчивости.

По уточнённому поручению пользователя эксперимент с отдельным выигрышем
+24.245460% вынесен в [v8](../server_v8/README.md). В v7 нет новых kick,
late acceptance, tabu, геометрического хвоста или изменений v6.

Архив: [case03_cpp_server_v7_O3.zip](artifacts/case03_cpp_server_v7_O3.zip).
SHA256 ZIP: `{sha(archive)}`.
В архиве ровно main.cpp и Makefile. Сборка распакованного архива совпала
с точным v4-контролем всех независимых TL60/TL280 тестов.
Стандартный лимит280с; без аргументов читает instance.json и пишет solution.json.
Makefile задаёт NT=2. Внешние библиотеки, сеть и дополнительные runtime-файлы
не нужны. Успешно проверены make build, make run и официальный валидатор.

```sh
make build
make run
```

[Исследование и полезные отдельные методы](../v4_perturbation/REPORT.md) ·
[Результаты экспериментальной v8](../server_v8/RESULTS_RU.md) ·
[Происхождение и проверки](PROVENANCE.json).

Стабильная основа означает сохранение известной v4, а не гарантию любого
скрытого теста. V4 и v6 не изменены; ничего не закоммичено, не добавлено
в staging и не отправлено на сервер.
''')
print(json.dumps({k:manifest[k] for k in ['version','status','zip','zip_sha256','identical_to_independently_tested_binary']},indent=2))
