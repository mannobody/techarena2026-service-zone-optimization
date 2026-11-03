# v5 MILP preview

ZIP: `./experiments/milp_v5/artifacts/case03_cpp_server_v5_milp_lazy_O3.zip`. SHA256 `7d2910953884585ecf5ce10c067118eda5e59bbc23320fb9b7b5d8be5dd2f627`.

- `make build`: g++ -O3 -std=c++17 -o solution main.cpp -ldl
- `make run`: ./solution; instance.json → solution.json
- По умолчанию 280 с; MILP только в свободном хвосте после стадий v4, без резерва времени.
- Требуется доступная libhighs.so или libhighs.so.1 с 32-bit HighsInt; проверено на 1.15.1. При отсутствии/несовместимости работает native fallback. Библиотека в ZIP не включена.
- `MIP=0` отключает MILP; `DBG=1` показывает v5_mip в stderr при запуске оператора.
- Независимый 60-секундный A/B: mean+0.1945%, median+0.0112%, worst-2.5692%. Все 60 VALID; package26 VALID. Экспериментальный кандидат, не гарантия скрытого score.
- На TL=60 фактический max wall финального кандидата: 60.149 с; таймер HiGHS мягкий.
- v4 и основной solver/ сохранены; кандидат поставляется отдельным пакетом.

Подробности, сравнения, ограничения и отрицательные результаты: REPORT.md.
