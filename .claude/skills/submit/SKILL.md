---
name: submit
description: Подготовить посылку на NSUTS: полный прогон 280 с, синтетика, сборка dist/case03_cpp.zip и запись в results/nsuts.md. Только по явной просьбе отправить решение.
---

В рейтинг идёт последняя посылка, поэтому отправляем только проверенный `main`.

1. `git status` чистый, ветка `main`, `git pull --ff-only`.
2. Параллельно в фоне: `python3 bench.py 280` и `python3 bench.py 60 --synth`. Требование: всё VALID,
   нет TIME, нет регрессии против `results/best.csv` больше разброса.
3. `./submission/make_zips.sh` → `dist/case03_cpp.zip` (можно взять артефакт CI `case03_cpp-<sha>`).
4. Отправляет человек (Docker C++, не стандартный компилятор). Попроси номер посылки.
5. Допиши в конец `results/nsuts.md`: дата, номер посылки, `git rev-parse --short HEAD`, балл (когда будет).
   Если 280-секундный прогон побил рекорд — отдельный PR с `bench.py 280 --record`.
