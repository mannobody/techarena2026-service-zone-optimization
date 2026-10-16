# Кейс 3. Сервисные зоны

Решение команды для хакатона TechArena 2026.

## Работа в команде

- В `main` изменения попадают только через pull request.
- Каждый работает в своей ветке: `<имя>/<задача>`, например `ivan/baseline`.
- Ветки Claude называются `claude/<задача>`.

## Структура

- `task/` — условие (`Techarena.pdf`), открытые инстансы, официальный `validate_solution.py`, примеры посылок от организаторов.
- `solver/solve.cpp` — основной решатель на C++ (один файл, только стандартная библиотека). `solver/solve.py` — та же схема на Python + numpy. `solver/ub_mip.py` — верхняя оценка через MIP без геометрии (OR-Tools).
- `submission/` — посылки для NSUTS: `case03_cpp.zip` (Docker, Makefile с `g++`) и `case03_python.zip`. Пересобрать: `./submission/make_zips.sh`.
- `SOLVER.md` — разбор условия, схема решателя, результаты и план улучшений.
- `research.md`, `proto/` — исследование до получения условия.

## Как запустить локально

```sh
g++ -O2 -std=c++17 -o solve solver/solve.cpp
./solve task/instance0/instance.json /tmp/sol0.json 60   # вход, выход, секунды
python3 task/validate_solution.py task/instance0/instance.json /tmp/sol0.json
```

Без аргументов решатель читает `instance.json`, пишет `solution.json` в текущем каталоге и работает 270 с (меняется переменной `TL`).
